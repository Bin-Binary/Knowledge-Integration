import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import time
import uuid
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.messages import AIMessage

from schemas.api import ChatTurnRequest, ChatTurnResponse
from config.system_config import AgentSystemConfig
from bootstrap import AgentApplication

from infra.observability import ( 
    setup_global_observability_logging,
    bind_observability_context,
    reset_observability_context,
)

logger = logging.getLogger("agent_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg_path = os.getenv("AGENT_CONFIG_PATH", "config/agent_settings.json")
    sys_cfg = AgentSystemConfig.load_from_json(cfg_path)

    # 第一时间根据配置初始化全局日志格式与脱敏过滤器
    setup_global_observability_logging(
        log_level=sys_cfg.server.log_level,
        enable_verbose=sys_cfg.server.enable_verbose_error_logs,
    )

    logger.info(f"[Startup] Loading system configuration from: {cfg_path}")
    logger.info(
        f"[Startup] Log security initialized | verbose_error_logs={sys_cfg.server.enable_verbose_error_logs}"
    )

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

    # 全局请求可观测性中间件：从网关入口即绑定 trace_id 到 ContextVar
    @application.middleware("http")
    async def observability_middleware(request: Request, call_next):
        trace_id = request.headers.get("X-Trace-Id") or f"tr_{uuid.uuid4().hex[:16]}"
        session_id = request.headers.get("X-Session-Id", "sess_gateway")
        request.state.trace_id = trace_id

        tokens = bind_observability_context(trace_id=trace_id, session_id=session_id)
        try:
            response = await call_next(request)
            response.headers["X-Trace-Id"] = trace_id  # 顺便在响应头回传 trace_id，方便前端排查
            return response
        finally:
            reset_observability_context(tokens)

    return application

app = create_app()

@app.exception_handler(asyncio.TimeoutError)
async def timeout_exception_handler(request: Request, exc: asyncio.TimeoutError):
    trace_id = getattr(request.state, "trace_id", "unknown")
    
    """Filter 已自动注入 [trace_id] 前缀，无需手动写 trace_id={trace_id}
    logger.error(f"[RequestTimeout] trace_id={trace_id} path={request.url.path}")
    """    
    logger.error(f"[RequestTimeout] path={request.url.path}")
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
    """注意：全局异常 handler 若包含敏感信息，Filter 会在非 verbose 模式下自动剥离堆栈
    [弃用]logger.exception(f"[UnhandledError] trace_id={trace_id} path={request.url.path} error={exc}")
    """
    logger.error(f"[UnhandledError] path={request.url.path} error={exc}", exc_info=True)

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
    # 直接复用中间件生成并绑定的 trace_id
    trace_id = request.state.trace_id
    start_time = time.perf_counter()

    sys_cfg: AgentSystemConfig = request.app.state.sys_cfg
    agent_app: AgentApplication = request.app.state.agent_app

    logger.info(f"[RequestIn] trace_id={trace_id} session_id={payload.session_id} msg_len={len(payload.user_message)}")

    # 受配置中心 request_timeout_seconds 保护的异步图调用
    final_state = await asyncio.wait_for(
        agent_app.ainvoke_turn(
            session_id=payload.session_id,
            user_message=payload.user_message,
            user_profile=payload.user_profile,
            trace_id=trace_id,
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
    """[兜底保护]防降级时返回 None
    预防未来新增其他节点只往 messages 里追加了 AIMessage 而忘了写 final_response，网关就会返回 reply=None
    """
    reply_text = final_state.get("final_response")
    if not reply_text and final_state.get("messages"):
        last_msg = final_state["messages"][-1]
        if isinstance(last_msg, AIMessage):
            reply_text = str(last_msg.content)

    return ChatTurnResponse(
        trace_id=trace_id,
        session_id=payload.session_id,
        latency_ms=latency_ms,
        intent=intent_obj.model_dump() if intent_obj else None,
        route_decision=route_obj.model_dump() if route_obj else None,
        reply=reply_text
    )
