# /api/server.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage

from schemas.api import ChatTurnRequest, ChatTurnResponse
from bootstrap import AgentApplication
from api.middlewares import register_middlewares_and_handlers

logger = logging.getLogger("agent_app")


def create_app() -> FastAPI:
    """应用工厂：完全委托 AgentApplication 管理配置与生命周期"""
    agent_app = AgentApplication.from_config_files()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.agent_app = agent_app
        sys_cfg = agent_app.sys_cfg
        logger.info(
            f"[Startup] AgentApplication ready | "
            f"Host={sys_cfg.server.host}:{sys_cfg.server.port} | "
            f"IntentModel={sys_cfg.get_llm_profile('intent').model_name}"
        )
        yield
        logger.info("[Shutdown] Cleaning up AgentApplication resources...")

    application = FastAPI(title="Agent Server", version="1.0.0", lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=agent_app.sys_cfg.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_middlewares_and_handlers(application)
    return application


app = create_app()


@app.get("/health", tags=["System"])
async def health_check(request: Request):
    is_ready = hasattr(request.app.state, "agent_app") and request.app.state.agent_app is not None
    if not is_ready:
        raise HTTPException(status_code=503, detail="AgentApplication not initialized")
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/v1/agent/chat", response_model=ChatTurnResponse, tags=["Agent"])
async def chat_turn_endpoint(payload: ChatTurnRequest, request: Request):
    trace_id = request.state.trace_id
    start_time = time.perf_counter()
    agent_app: AgentApplication = request.app.state.agent_app

    logger.info(f"[RequestIn] trace_id={trace_id} session_id={payload.session_id} msg_len={len(payload.user_message)}")

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
        f"[RequestOut] trace_id={trace_id} session_id={payload.session_id} "
        f"latency_ms={latency_ms} intent={intent_obj.intent if intent_obj else 'NONE'}"
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
