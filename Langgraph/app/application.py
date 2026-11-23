# app/application.py
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from config.business_config import load_business_config
from config.system_config import AgentSystemConfig
from schemas.intent_and_route_catalog import AgentBusinessConfig
from protocols.governance import HumanApprovalGateProtocol
from protocols.persistence import (
    ContextWindowGuardProtocol,
    MemoryCommitterProtocol,
)
from protocols.sanitization import InputSanitizerProtocol, RawPayloadRepairerProtocol
from infra.observability import (
    bind_observability_context,
    reset_observability_context,
    setup_global_observability_logging,
)
from components._shared.sanitization_pipeline import (
    InputSanitizationPipeline,
    LenientJsonPayloadRepairer,
)
from app.container import assemble_master_graph


class AgentApplication:
    """
    生产环境 Agent 运行时门面：
    负责入站输入清洗、网关容错协议暴露、全链路可观测上下文绑定与状态图驱动。
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
        self.graph: CompiledStateGraph = assemble_master_graph(
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
