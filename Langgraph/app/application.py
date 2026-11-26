import os
import asyncio
import uuid
import logging
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional, Tuple

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from config import load_business_config, AgentSystemConfig
from schemas import AgentBusinessConfig, StreamEvent
from protocols import (
    ContextWindowGuardProtocol,
    MemoryCommitterProtocol,
    HumanApprovalGateProtocol,
    InputSanitizerProtocol,
    RawPayloadRepairerProtocol,
)
from infra import (
    bind_observability_context,
    reset_observability_context,
    setup_global_observability_logging,
)
from infra.sanitization_pipeline import (
    InputSanitizationPipeline,
    LenientJsonPayloadRepairer,
)
from app.container import assemble_dual_graphs

logger = logging.getLogger(__name__)


class AgentApplication:
    """生产环境 Agent 运行时门面：负责入站清洗、可观测上下文绑定与双模状态图驱动"""

    def __init__(
        self,
        sys_cfg: AgentSystemConfig,
        biz_cfg: AgentBusinessConfig,
        checkpointer: Optional[Any] = None,
        context_guard: Optional[ContextWindowGuardProtocol] = None,
        approval_gate: Optional[HumanApprovalGateProtocol] = None,
        memory_committer: Optional[MemoryCommitterProtocol] = None,
    ) -> None:
        self.sys_cfg = sys_cfg
        self.biz_cfg = biz_cfg
        setup_global_observability_logging(
            log_level=self.sys_cfg.server.log_level,
            enable_verbose=self.sys_cfg.server.enable_verbose_error_logs,
        )
        self.sanitizer: InputSanitizerProtocol = InputSanitizationPipeline()
        self.payload_repairer: RawPayloadRepairerProtocol = LenientJsonPayloadRepairer()
        self.checkpointer = checkpointer or MemorySaver()

        self.graph, self.streaming_graph = assemble_dual_graphs(
            sys_cfg=sys_cfg,
            biz_cfg=biz_cfg,
            checkpointer=self.checkpointer,
            context_guard=context_guard,
            approval_gate=approval_gate,
            memory_committer=memory_committer,
        )

    @classmethod
    def from_config_files(
        cls,
        sys_config_path: Optional[str | Path] = None,
        intent_catalog_path: Optional[str | Path] = None,
        route_catalog_path: Optional[str | Path] = None,
        **kwargs: Any,
    ) -> "AgentApplication":
        sys_path = sys_config_path or os.getenv("AGENT_CONFIG_PATH", "config/agent_settings.json")
        intent_path = intent_catalog_path or os.getenv("AGENT_INTENT_CATALOG_PATH", "config/intent_catalog.json")
        route_path = route_catalog_path or os.getenv("AGENT_ROUTE_CATALOG_PATH", "config/route_catalog.json")

        return cls(
            sys_cfg=AgentSystemConfig.load_from_json(sys_path),
            biz_cfg=load_business_config(intent_path=intent_path, route_path=route_path),
            **kwargs,
        )

    def _prepare_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        """统一生成追踪 ID、图配置与初始轮次状态"""
        tid = trace_id or f"tr_{uuid.uuid4().hex[:16]}"
        clean_message = self.sanitizer.sanitize(user_message)
        config = {"configurable": {"thread_id": session_id}}
        initial_state: Dict[str, Any] = {
            "session_id": session_id,
            "trace_id": tid,
            "user_profile": user_profile or {},
            "messages": [HumanMessage(content=clean_message)],
            "intent_result": None,
            "route_decision": None,
            "final_response": None,
            "rag_context": None,
            "window_metrics": None,
            "failure_context": None,
            "recovery_outcome": None,
            "is_terminal": False,
            "_recovery_attempts": 0,
            "_last_failed_node": None,
        }
        return tid, config, initial_state

    def invoke_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        is_verbose: Optional[bool] = None,
    ) -> dict:
        tid, config, payload = self._prepare_turn(session_id, user_message, user_profile, trace_id)
        tokens = bind_observability_context(trace_id=tid, session_id=session_id, is_verbose=is_verbose)
        try:
            return self.graph.invoke(payload, config=config)
        finally:
            reset_observability_context(tokens)

    async def ainvoke_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        is_verbose: Optional[bool] = None,
    ) -> dict:
        tid, config, payload = self._prepare_turn(session_id, user_message, user_profile, trace_id)
        tokens = bind_observability_context(trace_id=tid, session_id=session_id, is_verbose=is_verbose)
        try:
            return await self.graph.ainvoke(payload, config=config)
        finally:
            reset_observability_context(tokens)

    async def astream_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        is_verbose: Optional[bool] = None,
    ) -> AsyncIterator[StreamEvent]:
        tid, config, payload = self._prepare_turn(session_id, user_message, user_profile, trace_id)
        progress_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        obs_tokens = bind_observability_context(
            trace_id=tid,
            session_id=session_id,
            is_verbose=is_verbose,
            stream_queue=progress_queue,
        )
        merged_queue: asyncio.Queue[Tuple[str, Any]] = asyncio.Queue()

        async def _pump_graph() -> None:
            try:
                async for item in self.streaming_graph.astream(
                    payload, config=config, stream_mode=["custom", "updates"]
                ):
                    await merged_queue.put(("graph", item))
                await merged_queue.put(("done", None))
            except Exception as exc:
                await merged_queue.put(("error", exc))

        async def _pump_progress() -> None:
            while True:
                item = await progress_queue.get()
                await merged_queue.put(("progress", item))

        graph_task = asyncio.create_task(_pump_graph())
        progress_task = asyncio.create_task(_pump_progress())
        has_streamed_tokens = False

        try:
            while True:
                source, data = await merged_queue.get()

                if source == "progress":
                    yield StreamEvent(
                        event="step",
                        data={"content": data.get("message", ""), "phase": data.get("phase", "running")},
                    )
                elif source == "graph":
                    mode, chunk = data
                    if mode == "custom" and isinstance(chunk, dict):
                        if chunk.get("type") == "token":
                            has_streamed_tokens = True
                            yield StreamEvent(event="token", data={"content": chunk.get("content", "")})
                        elif chunk.get("type") == "step":
                            yield StreamEvent(
                                event="step",
                                data={"content": chunk.get("thought", ""), "action": chunk.get("action", "")},
                            )
                    elif mode == "updates" and isinstance(chunk, dict):
                        if "__interrupt__" in chunk:
                            raw_int = chunk["__interrupt__"]
                            first = raw_int[0] if isinstance(raw_int, (list, tuple)) and raw_int else raw_int
                            int_val = getattr(first, "value", first)
                            yield StreamEvent(
                                event="approval_required",
                                data=int_val if isinstance(int_val, dict) else {"detail": int_val},
                            )
                            return

                        for delta in chunk.values():
                            if isinstance(delta, dict) and not has_streamed_tokens and delta.get("final_response"):
                                yield StreamEvent(event="token", data={"content": str(delta["final_response"])})
                                has_streamed_tokens = True
                elif source == "error":
                    raise data
                elif source == "done":
                    while not progress_queue.empty():
                        rem = progress_queue.get_nowait()
                        yield StreamEvent(
                            event="step",
                            data={"content": rem.get("message", ""), "phase": rem.get("phase", "running")},
                        )
                    yield StreamEvent(event="done", data={"trace_id": tid})
                    break

        except Exception as exc:
            logger.error("[StreamTurnError] trace_id=%s session_id=%s error=%s", tid, session_id, exc, exc_info=True)
            yield StreamEvent(
                event="error",
                data={
                    "trace_id": tid,
                    "error_code": "STREAM_EXECUTION_ERROR",
                    "message": "流式响应生成过程中发生异常，请稍后重试。",
                },
            )
        finally:
            graph_task.cancel()
            progress_task.cancel()
            await asyncio.gather(graph_task, progress_task, return_exceptions=True)
            reset_observability_context(obs_tokens)
