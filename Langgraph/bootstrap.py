# /bootstrap.py
import os
import uuid
from pathlib import Path
import httpx
from typing import Optional, Dict, Any, Iterator
from contextlib import contextmanager

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from config.system_config import AgentSystemConfig, LLMProfileConfig
from config.business_config import load_business_config
from schemas.intent_and_route_catalog import AgentBusinessConfig, TargetDomain
from protocols.persistence import (
    ContextWindowGuardProtocol,
    MemoryCommitterProtocol,
)
from protocols.governance import HumanApprovalGateProtocol

from infra.adapters import LangChainStructuredAdapter
from infra.observability import (
    setup_global_observability_logging,
    bind_observability_context,
    reset_observability_context,
)
from components.intent.hybrid_recognizer import HybridIntentRecognizer
from components.routing.router import CatalogRouter
from components.recovery.composite_recovery import CompositeRecoveryManager
from components.recovery.json_heal_recovery import JsonHealRecoveryManager
from components.internal_knowledge.factory import create_default_knowledge_engine
from components.planning.llm_planner import LLMPlanner
from components.agents.plan_solve_agent import PlanAndSolveAgent
from components.agents.registry import AgentRegistry
from components.sanitization.pipeline import InputSanitizationPipeline
from graphs.master_graph import build_master_agent_graph

_PROXY_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy", "OPENAI_PROXY")


@contextmanager
def temporary_no_proxy(enabled: bool = True) -> Iterator[None]:
    """仅在客户端实例化期间临时屏蔽代理环境变量，退出立刻无损恢复"""
    if not enabled:
        yield
        return
    saved_env = {k: os.environ.pop(k) for k in _PROXY_KEYS if k in os.environ}
    try:
        yield
    finally:
        os.environ.update(saved_env)


class AgentApplication:
    """
    生产环境 Agent 应用容器：
    单例管理配置中心、多模型适配器池、持久化存储及编译后的 LangGraph 主控图。
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
        self.sanitizer = InputSanitizationPipeline()
        self.checkpointer = checkpointer or MemorySaver()
        self.context_guard = context_guard
        self.approval_gate = approval_gate
        self.memory_committer = memory_committer
        self.graph: CompiledStateGraph = self._initialize_graph()

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

    def _build_llm_adapter(self, role: str) -> LangChainStructuredAdapter:
        """通用模型适配器工厂：按角色（'intent' / 'planner' / 'executor'）构建隔离客户端"""
        profile: LLMProfileConfig = self.sys_cfg.get_llm_profile(role)

        with temporary_no_proxy(enabled=profile.bypass_proxy):
            sync_client = httpx.Client(
                trust_env=not profile.bypass_proxy,
                timeout=profile.timeout_seconds,
            )
            async_client = httpx.AsyncClient(
                trust_env=not profile.bypass_proxy,
                timeout=profile.timeout_seconds,
            )

        chat_model = ChatOpenAI(
            model=profile.model_name,
            temperature=profile.temperature,
            max_tokens=profile.max_tokens,
            timeout=profile.timeout_seconds,
            max_retries=profile.max_retries,
            api_key=profile.get_plain_api_key(),
            base_url=profile.base_url,
            http_client=sync_client,
            http_async_client=async_client,
            extra_body=profile.extra_body,
        )
        return LangChainStructuredAdapter(chat_model=chat_model)

    def _get_or_fallback_adapter(self, role: str, fallback: LangChainStructuredAdapter) -> LangChainStructuredAdapter:
        """按角色获取模型适配器，若配置中未单独声明该角色则平滑回退至默认适配器"""
        try:
            return self._build_llm_adapter(role)
        except KeyError:
            return fallback

    def _build_adapter_pool(self) -> Dict[str, LangChainStructuredAdapter]:
        intent_adapter = self._build_llm_adapter("intent")
        executor_adapter = self._get_or_fallback_adapter("executor", intent_adapter)
        return {
            "intent": intent_adapter,
            "recovery": self._get_or_fallback_adapter("recovery", intent_adapter),
            "knowledge": self._get_or_fallback_adapter("knowledge", intent_adapter),
            "executor": executor_adapter,
            "planner": self._get_or_fallback_adapter("planner", executor_adapter),
        }

    def _build_agent_registry(
        self, adapters: Dict[str, LangChainStructuredAdapter]
    ) -> AgentRegistry:
        """插件化自动扫描并装配所有业务执行器（支持零修改横向扩展）"""
        AgentRegistry.discover_plugins("components.agents")

        registry = AgentRegistry()
        plannable_executors: Dict[str, str] = {}

        for agent_id, spec in AgentRegistry.get_plugin_catalog().items():
            if agent_id == "plan_solve_agent":
                continue
            llm = adapters.get(spec.default_llm_role, adapters["executor"])
            registry.register_instance(spec.agent_cls(llm_client=llm))
            if spec.plannable:
                plannable_executors[agent_id] = spec.description

        if plannable_executors:
            llm_planner = LLMPlanner(
                llm_client=adapters["planner"],
                available_executors=plannable_executors,
                default_executor="general_chat_agent",
            )
            registry.register_instance(
                PlanAndSolveAgent(
                    planner=llm_planner,
                    registry=registry,
                    synthesizer_node="general_chat_agent",
                    max_replans=2,
                )
            )

        # 启动期 Fail-Fast 校验：确保 route_catalog 中指向 execution 域的目标节点均已注册
        active_ids = set(registry.list_active_ids())
        route_cfg = self.biz_cfg.route_catalog
        if route_cfg.default_fallback_node not in active_ids:
            raise ValueError(
                f"启动校验失败：default_fallback_node='{route_cfg.default_fallback_node}' 未在 AgentRegistry 中注册。"
            )
        for intent_name, spec in route_cfg.routes.items():
            if spec.target_domain == TargetDomain.EXECUTION and spec.target_node not in active_ids:
                raise ValueError(
                    f"启动校验失败：意图 '{intent_name}' 路由指向的 '{spec.target_node}' 未在 AgentRegistry 中注册。"
                )

        return registry

    def _initialize_graph(self) -> CompiledStateGraph:
        adapters = self._build_adapter_pool()

        recognizer = HybridIntentRecognizer(
            catalog=self.biz_cfg.intent_catalog,
            llm_client=adapters["intent"],
            context_window_turns=self.sys_cfg.intent_recognition.context_window_turns,
        )
        router = CatalogRouter(catalog=self.biz_cfg.route_catalog)

        recovery_manager = CompositeRecoveryManager(
            handlers=[
                JsonHealRecoveryManager(structured_llm=adapters["recovery"]),
            ]
        )

        knowledge_cfg = self.sys_cfg.internal_knowledge
        knowledge_engine = (
            create_default_knowledge_engine(
                llm_client=adapters["knowledge"],
                vault_root=knowledge_cfg.vault_root,
                workspace_root=knowledge_cfg.workspace_root,
                quality_threshold=knowledge_cfg.quality_threshold,
                max_concurrency=knowledge_cfg.max_concurrency,
            )
            if knowledge_cfg.enabled
            else None
        )

        agent_registry = self._build_agent_registry(adapters)

        return build_master_agent_graph(
            intent_recognizer=recognizer,
            router=router,
            agent_registry=agent_registry,
            recovery_manager=recovery_manager,
            knowledge_engine=knowledge_engine,
            context_guard=self.context_guard,
            approval_gate=self.approval_gate,
            memory_committer=self.memory_committer,
            checkpointer=self.checkpointer,
        )

    def _build_initial_turn_state(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "trace_id": trace_id or f"tr_{uuid.uuid4().hex[:16]}",
            "user_profile": user_profile or {},
            "messages": [HumanMessage(content=user_message)],
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
