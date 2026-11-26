import uuid
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send, Message

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
            # 必须委托给真实的底层 receive() 监听断连事件，绝不能直接返回 http.disconnect！
            return await receive()

        await self.app(scope, new_receive, send)



class ObservabilityMiddleware:
    """纯 ASGI 全链路可观测性中间件（完美兼容 StreamingResponse / SSE，彻底避免 BaseHTTPMiddleware 断流报错）"""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        raw_headers = dict(scope.get("headers", []))
        trace_id = (
            raw_headers.get(b"x-trace-id", b"").decode("utf-8", errors="ignore")
            or f"tr_{uuid.uuid4().hex[:16]}"
        )
        session_id = (
            raw_headers.get(b"x-session-id", b"").decode("utf-8", errors="ignore")
            or "sess_gateway"
        )

        # 挂载到 scope["state"]，保证后续 FastAPI 的 request.state.trace_id 与异常处理器照常可用
        scope.setdefault("state", {})["trace_id"] = trace_id

        async def send_with_trace_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                # 避免重复添加 X-Trace-Id（例如 StreamingResponse 手动传了该 header 时）
                if not any(k.lower() == b"x-trace-id" for k, _ in headers):
                    headers.append((b"x-trace-id", trace_id.encode("utf-8")))
                message["headers"] = headers
            await send(message)

        tokens = bind_observability_context(trace_id=trace_id, session_id=session_id)
        try:
            await self.app(scope, receive, send_with_trace_id)
        finally:
            reset_observability_context(tokens)


def register_middlewares_and_handlers(
    app: FastAPI,
    payload_repairer: Optional[RawPayloadRepairerProtocol] = None,
) -> None:
    """统一注册网关中间件与全局异常处理器"""
    # 1. 注册字节流容错中间件
    if payload_repairer is not None:
        app.add_middleware(LenientJsonEscapeMiddleware, payload_repairer=payload_repairer)

    # 2. 后注册的可观测性中间件会包裹在更外层，确保全链路上下文与 trace_id 优先绑定
    app.add_middleware(ObservabilityMiddleware)

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
