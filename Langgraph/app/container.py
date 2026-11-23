# app/container.py
from typing import Any, Dict, Optional
from langgraph.graph.state import CompiledStateGraph

from config.system_config import AgentSystemConfig
from schemas.intent_and_route_catalog import AgentBusinessConfig, TargetDomain
from protocols.persistence import (
    ContextWindowGuardProtocol,
    MemoryCommitterProtocol,
)
from protocols.governance import HumanApprovalGateProtocol

from infra.adapters import LangChainStructuredAdapter
from components._shared.mapper import DefaultExceptionMapper
from components.intent.hybrid_recognizer import HybridIntentRecognizer
from components.routing.router import CatalogRouter
from components.recovery.composite_recovery import CompositeRecoveryManager
from components.recovery.json_heal_recovery import JsonHealRecoveryManager
from components.internal_knowledge.factory import create_default_knowledge_engine
from components.planning.llm_planner import LLMPlanner
from components.agents.plan_solve_agent import PlanAndSolveAgent
from components.agents.registry import AgentPluginCatalog, AgentRegistry
from graphs.master_graph import build_master_agent_graph
from app.llm_factory import build_adapter_pool


def build_agent_registry(
    biz_cfg: AgentBusinessConfig,
    adapters: Dict[str, LangChainStructuredAdapter],
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

    # 启动期 Fail-Fast 校验：确保 route_catalog 中指向 execution 域的目标节点均已注册
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


def assemble_master_graph(
    sys_cfg: AgentSystemConfig,
    biz_cfg: AgentBusinessConfig,
    *,
    checkpointer: Optional[Any] = None,
    context_guard: Optional[ContextWindowGuardProtocol] = None,
    approval_gate: Optional[HumanApprovalGateProtocol] = None,
    memory_committer: Optional[MemoryCommitterProtocol] = None,
) -> CompiledStateGraph:
    """组装全部具体组件并注入主控状态图（全系统唯一的依赖接线中心）"""
    adapters = build_adapter_pool(sys_cfg)
    exception_mapper = DefaultExceptionMapper(enable_sanitization=True)

    recognizer = HybridIntentRecognizer(
        catalog=biz_cfg.intent_catalog,
        llm_client=adapters["intent"],
        context_window_turns=sys_cfg.intent_recognition.context_window_turns,
    )
    router = CatalogRouter(catalog=biz_cfg.route_catalog)

    recovery_manager = CompositeRecoveryManager(
        handlers=[
            JsonHealRecoveryManager(structured_llm=adapters["recovery"]),
        ]
    )

    knowledge_cfg = sys_cfg.internal_knowledge
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

    agent_registry = build_agent_registry(biz_cfg, adapters)

    return build_master_agent_graph(
        intent_recognizer=recognizer,
        router=router,
        agent_resolver=agent_registry,
        recovery_manager=recovery_manager,
        map_exception=exception_mapper,
        knowledge_engine=knowledge_engine,
        context_guard=context_guard,
        approval_gate=approval_gate,
        memory_committer=memory_committer,
        checkpointer=checkpointer,
    )
