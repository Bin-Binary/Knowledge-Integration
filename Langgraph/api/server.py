import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import time
import uuid
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config.system_config import AgentSystemConfig
from bootstrap import AgentApplication

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("agent_gateway")


class ChatTurnRequest(BaseModel):
    """外部调用方传入的标准请求体"""
    session_id: str = Field(..., min_length=1, max_length=128)
    user_message: str = Field(..., min_length=1, max_length=10000)
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatTurnResponse(BaseModel):
    """返回给上游网关的标准化响应体"""
    trace_id: str
    session_id: str
    latency_ms: float
    intent: Optional[Dict[str, Any]] = None
    route_decision: Optional[Dict[str, Any]] = None
    reply: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg_path = os.getenv("AGENT_CONFIG_PATH", "config/agent_settings.json")
    logger.info(f"[Startup] Loading system configuration from: {cfg_path}")

    sys_cfg = AgentSystemConfig.load_from_json(cfg_path)
    app.state.sys_cfg = sys_cfg
    app.state.agent_app = AgentApplication(sys_cfg=sys_cfg)

    logger.info(
        f"[Startup] AgentApplication ready | "
        f"Host={sys_cfg.server.host}:{sys_cfg.server.port} | "
        f"IntentModel={sys_cfg.get_llm_profile('intent').model_name}"
    )
    yield
    logger.info("[Shutdown] Cleaning up AgentApplication resources...")


def create_app() -> FastAPI:
    """应用工厂：加载 CORS 等基础中间件并绑定生命周期"""
    cfg_path = os.getenv("AGENT_CONFIG_PATH", "config/agent_settings.json")
    initial_cfg = AgentSystemConfig.load_from_json(cfg_path)

    application = FastAPI(
        title="Enterprise Agent Core Gateway",
        version="1.0.0",
        lifespan=lifespan
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=initial_cfg.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application


app = create_app()


@app.exception_handler(asyncio.TimeoutError)
async def timeout_exception_handler(request: Request, exc: asyncio.TimeoutError):
    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.error(f"[RequestTimeout] trace_id={trace_id} path={request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "trace_id": trace_id,
            "error_code": "AGENT_EXECUTION_TIMEOUT",
            "message": "Agent processing timed out."
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.exception(f"[UnhandledError] trace_id={trace_id} path={request.url.path} error={exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "trace_id": trace_id,
            "error_code": "INTERNAL_AGENT_ERROR",
            "message": "Agent service encountered an unexpected error."
        }
    )


@app.get("/health", tags=["System"])
async def health_check(request: Request):
    is_ready = hasattr(request.app.state, "agent_app") and request.app.state.agent_app is not None
    if not is_ready:
        raise HTTPException(status_code=503, detail="AgentApplication not initialized")
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/v1/agent/chat", response_model=ChatTurnResponse, tags=["Agent"])
async def chat_turn_endpoint(payload: ChatTurnRequest, request: Request):
    trace_id = request.headers.get("X-Trace-Id") or f"tr_{uuid.uuid4().hex[:16]}"
    request.state.trace_id = trace_id
    start_time = time.perf_counter()

    sys_cfg: AgentSystemConfig = request.app.state.sys_cfg
    agent_app: AgentApplication = request.app.state.agent_app

    logger.info(f"[RequestIn] trace_id={trace_id} session_id={payload.session_id} msg_len={len(payload.user_message)}")

    # 受配置中心 request_timeout_seconds 保护的异步图调用
    final_state = await asyncio.wait_for(
        agent_app.ainvoke_turn(
            session_id=payload.session_id,
            user_message=payload.user_message,
            user_profile=payload.user_profile
        ),
        timeout=sys_cfg.server.request_timeout_seconds
    )

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    intent_obj = final_state.get("intent_result")
    route_obj = final_state.get("route_decision")

    logger.info(
        f"[RequestOut] trace_id={trace_id} session_id={payload.session_id} "
        f"latency_ms={latency_ms} intent={intent_obj.intent if intent_obj else 'NONE'}"
    )

    return ChatTurnResponse(
        trace_id=trace_id,
        session_id=payload.session_id,
        latency_ms=latency_ms,
        intent=intent_obj.model_dump() if intent_obj else None,
        route_decision=route_obj.model_dump() if route_obj else None,
        reply=final_state.get("final_response")
    )
