# /api/server.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage

from schemas.api import ChatTurnRequest, ChatTurnResponse
from protocols.sanitization import RawPayloadRepairerProtocol
from app.application import AgentApplication
from api.middlewares import register_middlewares_and_handlers

logger = logging.getLogger("agent_app")
router = APIRouter()


@runtime_checkable
class AgentRuntimeProtocol(Protocol):
    """接入层视角下的 Agent 运行时最小契约（方便 API 单元测试注入 Mock）"""

    @property
    def sys_cfg(self) -> Any:
        ...

    @property
    def payload_repairer(self) -> RawPayloadRepairerProtocol:
        ...

    async def ainvoke_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        is_verbose: Optional[bool] = None,
    ) -> dict:
        ...


@router.get("/health", tags=["System"])
async def health_check(request: Request):
    is_ready = getattr(request.app.state, "agent_app", None) is not None
    if not is_ready:
        raise HTTPException(status_code=503, detail="AgentApplication not initialized")
    return {"status": "healthy", "version": "1.0.0"}


@router.post("/v1/agent/chat", response_model=ChatTurnResponse, tags=["Agent"])
async def chat_turn_endpoint(payload: ChatTurnRequest, request: Request):
    trace_id = request.state.trace_id
    start_time = time.perf_counter()
    agent_app: AgentRuntimeProtocol = request.app.state.agent_app

    logger.info(
        "[RequestIn] trace_id=%s session_id=%s msg_len=%d",
        trace_id,
        payload.session_id,
        len(payload.user_message),
    )

    final_state = await asyncio.wait_for(
        agent_app.ainvoke_turn(
            session_id=payload.session_id,
            user_message=payload.user_message,
            user_profile=payload.user_profile,
            trace_id=trace_id,
        ),
        timeout=agent_app.sys_cfg.server.request_timeout_seconds,
    )

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    intent_obj = final_state.get("intent_result")
    route_obj = final_state.get("route_decision")

    logger.info(
        "[RequestOut] trace_id=%s session_id=%s latency_ms=%s intent=%s",
        trace_id,
        payload.session_id,
        latency_ms,
        intent_obj.intent if intent_obj else "NONE",
    )

    reply_text = final_state.get("final_response")
    if not reply_text and final_state.get("messages"):
        last_msg = final_state["messages"][-1]
        if isinstance(last_msg, AIMessage):
            reply_text = str(last_msg.content)
    if not reply_text:
        reply_text = final_state.get("rag_context")

    return ChatTurnResponse(
        trace_id=trace_id,
        session_id=payload.session_id,
        latency_ms=latency_ms,
        intent=intent_obj.model_dump() if intent_obj else None,
        route_decision=route_obj.model_dump() if route_obj else None,
        reply=reply_text,
    )


def create_app(agent_app: Optional[AgentRuntimeProtocol] = None) -> FastAPI:
    """应用工厂：支持外部注入测试替身，默认自动从配置文件装配"""
    runtime_app = agent_app or AgentApplication.from_config_files()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.agent_app = runtime_app
        sys_cfg = runtime_app.sys_cfg
        logger.info(
            "[Startup] AgentApplication ready | Host=%s:%s | IntentModel=%s",
            sys_cfg.server.host,
            sys_cfg.server.port,
            sys_cfg.get_llm_profile("intent").model_name,
        )
        yield
        logger.info("[Shutdown] Cleaning up AgentApplication resources...")

    application = FastAPI(title="Agent Server", version="1.0.0", lifespan=lifespan)

    register_middlewares_and_handlers(
        application,
        payload_repairer=runtime_app.payload_repairer,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_app.sys_cfg.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(router)
    return application


app = create_app()
