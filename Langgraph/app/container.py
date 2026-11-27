# /app/container.py
from typing import Any, Dict, Optional, Tuple
from langgraph.graph.state import CompiledStateGraph

from config import AgentSystemConfig
from schemas import AgentBusinessConfig, TargetDomain
from protocols import (
    ContextWindowGuardProtocol,
    MemoryCommitterProtocol,
    HumanApprovalGateProtocol,
)
from infra import HybridLangChainAdapter
from infra.registry_exception_mapper import RegistryExceptionMapper
from components.intent import HybridIntentRecognizer
from components.routing import CatalogRouter
from components.recovery.registry import RecoveryPluginRegistry
from components.recovery.composite_recovery import CompositeRecoveryManager
from components.internal_knowledge import create_default_knowledge_engine
from components.planning import LLMPlanner
from components.agents import (
    PlanAndSolveAgent,
    AgentPluginCatalog,
    AgentRegistry,
)
from graphs import build_master_agent_graph
from app.llm_factory import build_adapter_pool
from app.resilience_pipeline import ACTIVE_EXCEPTION_SPECS, RECOVERY_PIPELINE_ORDER


def build_agent_registry(
    biz_cfg: AgentBusinessConfig,
    adapters: Dict[str, HybridLangChainAdapter],
) -> AgentRegistry:
    """插件化自动扫描并装配所有业务执行器，并执行启动期 Fail-Fast 路由完整性校验"""
    AgentPluginCatalog.discover("components.agents")

    registry = AgentRegistry()
    plannable_executors: Dict[str, str] = {}

    for agent_id, spec in AgentPluginCatalog.all_specs().items():
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
                resolver=registry,
                synthesizer_node="general_chat_agent",
                max_replans=2,
            )
        )

    active_ids = set(registry.list_active_ids())
    route_cfg = biz_cfg.route_catalog
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


def _build_resilience_components(
    sys_cfg: AgentSystemConfig,
    adapters: Dict[str, Any],
) -> Tuple[RegistryExceptionMapper, CompositeRecoveryManager]:
    exc_cfg = sys_cfg.exception_handling
    exception_mapper = RegistryExceptionMapper(
        default_category=exc_cfg.default_category,
        max_error_length=exc_cfg.max_error_length,
        enable_sanitization=exc_cfg.enable_sanitization,
    ).register_specs(ACTIVE_EXCEPTION_SPECS)

    handlers = RecoveryPluginRegistry.build_handlers(
        enabled_names=RECOVERY_PIPELINE_ORDER,
        shared_deps={
            "structured_llm": adapters["recovery"],
            "fallback_intent": exc_cfg.fallback_intent,
        },
    )
    recovery_manager = CompositeRecoveryManager(
        handlers=handlers,
        default_fallback_message=exc_cfg.default_fallback_message,
    )
    return exception_mapper, recovery_manager


def _build_core_dependencies(
    sys_cfg: AgentSystemConfig,
    biz_cfg: AgentBusinessConfig,
) -> Dict[str, Any]:
    """内部公共依赖组装：确保连接池、插件注册表与知识引擎只实例化一次"""
    adapters = build_adapter_pool(sys_cfg)

    recognizer = HybridIntentRecognizer(
        catalog=biz_cfg.intent_catalog,
        llm_client=adapters["intent"],
        context_window_turns=sys_cfg.intent_recognition.context_window_turns,
        min_confidence=sys_cfg.intent_recognition.confidence_threshold,
    )
    exception_mapper, recovery_manager = _build_resilience_components(
        sys_cfg, adapters
    )
    router = CatalogRouter(catalog=biz_cfg.route_catalog)

    knowledge_cfg = sys_cfg.internal_knowledge
    knowledge_engine = (
        create_default_knowledge_engine(
            llm_client=adapters["knowledge"],
            vault_root=knowledge_cfg.vault_root,
            workspace_root=knowledge_cfg.workspace_root,
            quality_threshold=knowledge_cfg.quality_threshold,
            max_concurrency=knowledge_cfg.max_concurrency,
            organize_timeout_seconds=knowledge_cfg.organize_timeout_seconds,

        )
        if knowledge_cfg.enabled
        else None
    )
    agent_registry = build_agent_registry(biz_cfg, adapters)

    return {
        "intent_recognizer": recognizer,
        "router": router,
        "agent_resolver": agent_registry,
        "recovery_manager": recovery_manager,
        "map_exception": exception_mapper,
        "knowledge_engine": knowledge_engine,
        "knowledge_max_iterations": knowledge_cfg.max_iterations,
    }


def assemble_master_graph(
    sys_cfg: AgentSystemConfig,
    biz_cfg: AgentBusinessConfig,
    *,
    checkpointer: Optional[Any] = None,
    context_guard: Optional[ContextWindowGuardProtocol] = None,
    approval_gate: Optional[HumanApprovalGateProtocol] = None,
    memory_committer: Optional[MemoryCommitterProtocol] = None,
) -> CompiledStateGraph:
    """组装全部具体组件并注入主控状态图"""
    deps = _build_core_dependencies(sys_cfg, biz_cfg)
    return build_master_agent_graph(
        **deps,
        context_guard=context_guard,
        approval_gate=approval_gate,
        memory_committer=memory_committer,
        checkpointer=checkpointer,
    )


def assemble_dual_graphs(
    sys_cfg: AgentSystemConfig,
    biz_cfg: AgentBusinessConfig,
    *,
    checkpointer: Optional[Any] = None,
    context_guard: Optional[ContextWindowGuardProtocol] = None,
    approval_gate: Optional[HumanApprovalGateProtocol] = None,
    memory_committer: Optional[MemoryCommitterProtocol] = None,
) -> Tuple[CompiledStateGraph, CompiledStateGraph]:
    """同时装配标准图与流式图，共享同一份底层依赖实例与 Checkpointer。"""
    deps = _build_core_dependencies(sys_cfg, biz_cfg)
    shared_kwargs = dict(
        **deps,
        context_guard=context_guard,
        approval_gate=approval_gate,
        memory_committer=memory_committer,
        checkpointer=checkpointer,
    )
    standard_graph = build_master_agent_graph(**shared_kwargs, enable_streaming=False)
    streaming_graph = build_master_agent_graph(**shared_kwargs, enable_streaming=True)
    return standard_graph, streaming_graph
