# /api/middlewares.py
import uuid
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from protocols import RawPayloadRepairerProtocol
from infra import bind_observability_context, reset_observability_context

logger = logging.getLogger("agent_app")


class LenientJsonEscapeMiddleware:
    """网关容错中间件：通过 RawPayloadRepairerProtocol 修复原始请求体中的非法反斜杠转义"""

    def __init__(
        self,
        app: ASGIApp,
        payload_repairer: Optional[RawPayloadRepairerProtocol] = None,
    ) -> None:
        self.app = app
        self._repairer = payload_repairer

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or self._repairer is None:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        if b"application/json" not in headers.get(b"content-type", b""):
            await self.app(scope, receive, send)
            return

        chunks = []
        while True:
            msg = await receive()
            if msg["type"] == "http.request":
                chunks.append(msg.get("body", b""))
                if not msg.get("more_body", False):
                    break
            elif msg["type"] == "http.disconnect":
                return

        fixed_body = self._repairer.repair_bytes(b"".join(chunks))
        sent = False

        async def new_receive() -> dict:
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": fixed_body, "more_body": False}
            return {"type": "http.disconnect"}

        await self.app(scope, new_receive, send)


def register_middlewares_and_handlers(
    app: FastAPI,
    payload_repairer: Optional[RawPayloadRepairerProtocol] = None,
) -> None:
    """统一注册网关中间件与全局异常处理器"""
    if payload_repairer is not None:
        app.add_middleware(LenientJsonEscapeMiddleware, payload_repairer=payload_repairer)

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id") or f"tr_{uuid.uuid4().hex[:16]}"
        session_id = request.headers.get("X-Session-Id", "sess_gateway")
        request.state.trace_id = trace_id

        tokens = bind_observability_context(trace_id=trace_id, session_id=session_id)
        try:
            response = await call_next(request)
            response.headers["X-Trace-Id"] = trace_id
            return response
        finally:
            reset_observability_context(tokens)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        trace_id = getattr(request.state, "trace_id", "unknown")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers={"X-Trace-Id": trace_id},
            content={
                "trace_id": trace_id,
                "error_code": "REQUEST_VALIDATION_ERROR",
                "message": "请求参数校验失败。",
                "detail": exc.errors(),
            },
        )

    @app.exception_handler(asyncio.TimeoutError)
    async def timeout_exception_handler(request: Request, exc: asyncio.TimeoutError):
        trace_id = getattr(request.state, "trace_id", "unknown")
        logger.error("[RequestTimeout] path=%s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            headers={"X-Trace-Id": trace_id},
            content={
                "trace_id": trace_id,
                "error_code": "AGENT_EXECUTION_TIMEOUT",
                "message": "Agent processing timed out.",
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        trace_id = getattr(request.state, "trace_id", "unknown")
        logger.error("[UnhandledError] path=%s error=%s", request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            headers={"X-Trace-Id": trace_id},
            content={
                "trace_id": trace_id,
                "error_code": "INTERNAL_AGENT_ERROR",
                "message": "Agent service encountered an unexpected error.",
            },
        )
