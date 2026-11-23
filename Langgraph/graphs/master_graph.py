# /graphs/master_graph.py
import logging
from typing import Any, Literal, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from protocols.components import (
    IntentRecognizerProtocol,
    RouterProtocol,
    ExceptionRecoveryProtocol,
)
from protocols.internal_knowledge import InternalKnowledgeEngineProtocol
from schemas.intent_and_route_catalog import TargetDomain
from schemas.decision import RouteDecision
from graphs.state import MasterAgentState
from graphs.intent_graph import create_intent_node
from graphs.routing_graph import create_routing_node
from graphs.knowledge_graph import build_knowledge_domain_subgraph
from graphs.execution_graph import create_execution_node
from graphs.recovery_graph import create_recovery_node
from infra.observability import log_execution
from components.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)

# 顶层业务域图节点名称，严格对齐 TargetDomain 枚举值
KNOWLEDGE_NODE = TargetDomain.KNOWLEDGE.value
EXECUTION_NODE = TargetDomain.EXECUTION.value


def _resolve_post_routing_stage(decision: RouteDecision, has_knowledge: bool) -> str:
    """统一配置驱动决策：根据知识库启用状态与调度契约决定下一阶段"""
    if not has_knowledge or decision.should_skip_knowledge:
        return EXECUTION_NODE
    return KNOWLEDGE_NODE

@log_execution("route_after_intent", level=logging.DEBUG)
def _route_after_intent(
    state: MasterAgentState,
) -> Literal["recovery_node", "routing"]:
    """意图识别出口条件边：异常转自愈，其余（含空意图）一律进入路由调度由 Router 统一兜底"""
    if state.get("failure_context") is not None:
        return "recovery_node"
    return "routing"


@log_execution("route_after_knowledge", level=logging.DEBUG)
def _route_after_knowledge(
    state: MasterAgentState,
) -> str:
    """
    知识领域子图出口条件边：
    1. 子图内部异常 -> 转入 recovery_node；
    2. 持续学习路径（deep_learn）已产出 final_response -> 直接收尾结束；
    3. 快速检索路径（fast_retrieve）填充完 rag_context -> 流向 execution 生成回复。
    """
    if state.get("failure_context") is not None:
        return "recovery_node"
    if state.get("final_response"):
        return "end_flow"
    return EXECUTION_NODE


@log_execution("route_after_execution", level=logging.DEBUG)
def _route_after_execution(
    state: MasterAgentState,
) -> Literal["recovery_node", "end_flow"]:
    """执行节点出口条件边：捕获执行期未自愈异常时转入 recovery_node，否则正常结束"""
    if state.get("failure_context") is not None:
        return "recovery_node"
    return "end_flow"


@log_execution("build_master_agent_graph")
def build_master_agent_graph(
    intent_recognizer: IntentRecognizerProtocol,
    router: RouterProtocol,
    agent_registry: AgentRegistry,
    recovery_manager: ExceptionRecoveryProtocol,
    knowledge_engine: Optional[InternalKnowledgeEngineProtocol] = None,
    checkpointer: Optional[Any] = None,
) -> CompiledStateGraph:
    """
    生产环境主控状态图构建器（支持域内知识库热插拔）：
    拓扑主干：START -> intent_recognition -> routing -> [knowledge] -> execution -> END
    """
    workflow = StateGraph(MasterAgentState)
    has_knowledge = knowledge_engine is not None

    # 1. 注册核心节点
    workflow.add_node("intent_recognition", create_intent_node(intent_recognizer))
    workflow.add_node("routing", create_routing_node(router))
    workflow.add_node(EXECUTION_NODE, create_execution_node(agent_registry))
    workflow.add_node("recovery_node", create_recovery_node(recovery_manager))

    if has_knowledge:
        workflow.add_node(
            KNOWLEDGE_NODE,
            build_knowledge_domain_subgraph(knowledge_engine),
        )

    # 路由出口条件边（闭环读取 has_knowledge）
    @log_execution("route_after_routing", level=logging.DEBUG)
    def _route_after_routing(state: MasterAgentState) -> str:
        if state.get("failure_context") is not None:
            return "recovery_node"
        decision = state.get("route_decision")
        if decision is None:
            return "end_flow"
        return _resolve_post_routing_stage(decision, has_knowledge)

    # 异常自愈成功后的精准断点恢复路由
    @log_execution("route_after_recovery", level=logging.DEBUG)
    def _route_after_recovery(state: MasterAgentState) -> str:
        outcome = state.get("recovery_outcome")
        if outcome is None or not outcome.is_recovered or state.get("is_terminal", False):
            return "end_flow"

        decision = state.get("route_decision")
        if decision is not None:
            return _resolve_post_routing_stage(decision, has_knowledge)
        if state.get("intent_result") is not None:
            return "routing"
        return "end_flow"

    # 2. 编排拓扑边
    workflow.add_edge(START, "intent_recognition")

    workflow.add_conditional_edges(
        "intent_recognition",
        _route_after_intent,
        {
            "recovery_node": "recovery_node",
            "routing": "routing",
        },
    )
    routing_targets: dict[str, Any] = {
        "recovery_node": "recovery_node",
        EXECUTION_NODE: EXECUTION_NODE,
        "end_flow": END,
    }
    if has_knowledge:
        routing_targets[KNOWLEDGE_NODE] = KNOWLEDGE_NODE

    workflow.add_conditional_edges(
        "routing",
        _route_after_routing,
        routing_targets,
    )

    if has_knowledge:
        workflow.add_conditional_edges(
            KNOWLEDGE_NODE,
            _route_after_knowledge,
            {
                "recovery_node": "recovery_node",
                EXECUTION_NODE: EXECUTION_NODE,
                "end_flow": END,
            },
        )

    workflow.add_conditional_edges(
        EXECUTION_NODE,
        _route_after_execution,
        {
            "recovery_node": "recovery_node",
            "end_flow": END,
        },
    )

    recovery_targets: dict[str, Any] = {
        "routing": "routing",
        EXECUTION_NODE: EXECUTION_NODE,
        "end_flow": END,
    }
    if has_knowledge:
        recovery_targets[KNOWLEDGE_NODE] = KNOWLEDGE_NODE

    workflow.add_conditional_edges(
        "recovery_node",
        _route_after_recovery,
        recovery_targets,
    )

    logger.info("MasterAgentGraph compiled (knowledge_enabled=%s).", has_knowledge)
    return workflow.compile(checkpointer=checkpointer)
