import os
import asyncio
import uuid
import logging
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

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
    """
    生产环境 Agent 运行时门面：
    负责入站输入清洗、网关容错协议暴露、全链路可观测上下文绑定与双模状态图驱动。
    """

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

        # 双模状态图共享同一份底层依赖实例与 Checkpointer
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
        checkpointer: Optional[Any] = None,
        context_guard: Optional[ContextWindowGuardProtocol] = None,
        approval_gate: Optional[HumanApprovalGateProtocol] = None,
        memory_committer: Optional[MemoryCommitterProtocol] = None,
    ) -> "AgentApplication":
        sys_path = sys_config_path or os.getenv("AGENT_CONFIG_PATH", "config/agent_settings.json")
        intent_path = intent_catalog_path or os.getenv("AGENT_INTENT_CATALOG_PATH", "config/intent_catalog.json")
        route_path = route_catalog_path or os.getenv("AGENT_ROUTE_CATALOG_PATH", "config/route_catalog.json")

        sys_cfg = AgentSystemConfig.load_from_json(sys_path)
        biz_cfg = load_business_config(intent_path=intent_path, route_path=route_path)
        return cls(
            sys_cfg=sys_cfg,
            biz_cfg=biz_cfg,
            checkpointer=checkpointer,
            context_guard=context_guard,
            approval_gate=approval_gate,
            memory_committer=memory_committer,
        )

    def _build_initial_turn_state(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        clean_message = self.sanitizer.sanitize(user_message)
        return {
            "session_id": session_id,
            "trace_id": trace_id or f"tr_{uuid.uuid4().hex[:16]}",
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

    def invoke_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        is_verbose: Optional[bool] = None,
    ) -> dict:
        trace_id = trace_id or f"tr_{uuid.uuid4().hex[:16]}"
        config = {"configurable": {"thread_id": session_id}}
        input_payload = self._build_initial_turn_state(
            session_id=session_id,
            user_message=user_message,
            user_profile=user_profile,
            trace_id=trace_id,
        )
        reset = bind_observability_context(
            trace_id=trace_id,
            session_id=session_id,
            is_verbose=is_verbose,
        )
        try:
            return self.graph.invoke(input_payload, config=config)
        finally:
            reset_observability_context(reset)

    async def ainvoke_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        is_verbose: Optional[bool] = None,
    ) -> dict:
        trace_id = trace_id or f"tr_{uuid.uuid4().hex[:16]}"
        config = {"configurable": {"thread_id": session_id}}
        input_payload = self._build_initial_turn_state(
            session_id=session_id,
            user_message=user_message,
            user_profile=user_profile,
            trace_id=trace_id,
        )
        reset = bind_observability_context(
            trace_id=trace_id,
            session_id=session_id,
            is_verbose=is_verbose,
        )
        try:
            return await self.graph.ainvoke(input_payload, config=config)
        finally:
            reset_observability_context(reset)

    async def _stream_typewriter_chunks(
        self,
        event_name: str,
        text: str,
        extra_data: Optional[Dict[str, Any]] = None,
        chunk_size: int = 6,        # 调大默认切片粒度，告别 2 字一包的过度碎片化
        delay_sec: float = 0.008,   # 加快节奏，降低首字等待延迟
    ) -> AsyncIterator[StreamEvent]:
        """将任意组件执行状态或兜底文本渲染为丝滑打字机流"""
        for i in range(0, len(text), chunk_size):
            payload = {"content": text[i : i + chunk_size], **(extra_data or {})}
            yield StreamEvent(event=event_name, data=payload)
            await asyncio.sleep(delay_sec)


    async def astream_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        is_verbose: Optional[bool] = None,
    ) -> AsyncIterator[StreamEvent]:
        trace_id = trace_id or f"tr_{uuid.uuid4().hex[:16]}"
        config = {"configurable": {"thread_id": session_id}}
        input_payload = self._build_initial_turn_state(
            session_id=session_id,
            user_message=user_message,
            user_profile=user_profile,
            trace_id=trace_id,
        )

        progress_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        obs_tokens = bind_observability_context(
            trace_id=trace_id,
            session_id=session_id,
            is_verbose=is_verbose,
            stream_queue=progress_queue,
        )
        merged_queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()

        async def _pump_graph() -> None:
            try:
                async for item in self.streaming_graph.astream(
                    input_payload, config=config, stream_mode=["custom", "updates"]
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
                source, payload = await merged_queue.get()

                # A. 来自 components/ 的实时执行状态 -> 原样即时推送整条进度，零人为切片延迟
                if source == "progress":
                    yield StreamEvent(
                        event="step",
                        data={
                            "content": payload.get("message", ""),
                            "phase": payload.get("phase", "running"),
                        },
                    )
                    continue

                # B. 来自 LangGraph 的原生流事件
                if source == "graph":
                    mode, chunk = payload
                    if mode == "custom" and isinstance(chunk, dict):
                        chunk_type = chunk.get("type")
                        if chunk_type == "token":
                            has_streamed_tokens = True
                            yield StreamEvent(
                                event="token",
                                data={"content": chunk.get("content", "")},
                            )
                        elif chunk_type == "step":
                            yield StreamEvent(
                                event="step",
                                data={
                                    "content": chunk.get("thought", ""),
                                    "action": chunk.get("action", ""),
                                },
                            )

                    elif mode == "updates" and isinstance(chunk, dict):
                        if "__interrupt__" in chunk:
                            interrupt_obj = chunk["__interrupt__"]
                            first_interrupt = (
                                interrupt_obj[0]
                                if isinstance(interrupt_obj, (list, tuple)) and interrupt_obj
                                else interrupt_obj
                            )
                            int_val = getattr(first_interrupt, "value", first_interrupt)
                            yield StreamEvent(
                                event="approval_required",
                                data=int_val if isinstance(int_val, dict) else {"detail": int_val},
                            )
                            return

                        for _, state_delta in chunk.items():
                            if not isinstance(state_delta, dict):
                                continue
                            # 非流式分支（如自愈降级、深度学习归档）直接完整推送终态回复，由前端决定渲染动效
                            fallback_reply = state_delta.get("final_response")
                            if not has_streamed_tokens and fallback_reply:
                                yield StreamEvent(
                                    event="token",
                                    data={"content": str(fallback_reply)},
                                )
                                has_streamed_tokens = True
                    continue

                # C. 结束与异常收尾
                if source == "error":
                    raise payload

                if source == "done":
                    while not progress_queue.empty():
                        rem = progress_queue.get_nowait()
                        yield StreamEvent(
                            event="step",
                            data={
                                "content": rem.get("message", ""),
                                "phase": rem.get("phase", "running"),
                            },
                        )
                    yield StreamEvent(event="done", data={"trace_id": trace_id})
                    break

        except Exception as exc:
            logger.error(
                "[StreamTurnError] trace_id=%s session_id=%s error=%s",
                trace_id,
                session_id,
                exc,
                exc_info=True,
            )
            yield StreamEvent(
                event="error",
                data={
                    "trace_id": trace_id,
                    "error_code": "STREAM_EXECUTION_ERROR",
                    "message": "流式响应生成过程中发生异常，请稍后重试。",
                },
            )
        finally:
            graph_task.cancel()
            progress_task.cancel()
            reset_observability_context(obs_tokens)
