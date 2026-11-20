# /graphs/master_graph.py
import logging
from typing import Any, Literal, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from protocols.components import IntentRecognizerProtocol, ExceptionRecoveryProtocol
from protocols.internal_knowledge import InternalKnowledgeEngineProtocol
from graphs.state import MasterAgentState
from graphs.intent_graph import create_intent_node
from graphs.recovery_graph import create_recovery_node
from graphs.knowledge_graph import create_knowledge_blackbox_node
from infra.observability import log_execution

logger = logging.getLogger(__name__)


@log_execution("route_after_intent", level=logging.DEBUG)
def _route_after_intent(
    state: MasterAgentState,
) -> Literal["recovery_node", "next_stage", "end_flow"]:
    """意图识别出口条件边：捕获到 failure_context 时跳转 recovery_node"""
    if state.get("failure_context") is not None:
        return "recovery_node"
    if state.get("intent_result") is None:
        return "end_flow"
    return "next_stage"


@log_execution("route_after_knowledge", level=logging.DEBUG)
def _route_after_knowledge(
    state: MasterAgentState,
) -> Literal["recovery_node", "next_stage"]:
    """知识库出口条件边：若知识库闭环抛出异常则转入自愈，否则携带 rag_context 流向下一阶段"""
    if state.get("failure_context") is not None:
        return "recovery_node"
    return "next_stage"


@log_execution("route_after_recovery", level=logging.DEBUG)
def _route_after_recovery(
    state: MasterAgentState,
) -> Literal["resume_flow", "end_flow"]:
    """异常恢复出口条件边：自愈成功重返主干道，否则安全结束本轮"""
    outcome = state.get("recovery_outcome")
    if outcome is not None and outcome.is_recovered and not state.get("is_terminal", False):
        return "resume_flow"
    return "end_flow"


@log_execution("build_master_agent_graph")
def build_master_agent_graph(
    intent_recognizer: IntentRecognizerProtocol,
    recovery_manager: ExceptionRecoveryProtocol,
    knowledge_engine: Optional[InternalKnowledgeEngineProtocol] = None,
    checkpointer: Optional[Any] = None,
) -> CompiledStateGraph:
    """生产环境主控状态图构建器（支持域内知识库热插拔）。"""
    workflow = StateGraph(MasterAgentState)

    # 1. 注册核心节点
    workflow.add_node("intent_recognition", create_intent_node(intent_recognizer))
    workflow.add_node("recovery_node", create_recovery_node(recovery_manager))

    has_knowledge = knowledge_engine is not None
    if has_knowledge:
        workflow.add_node(
            "knowledge_retrieval",
            create_knowledge_blackbox_node(knowledge_engine),
        )

    # 动态决定意图识别之后的下一个主干节点（有知识库进知识库，无知识库直接结束/进路由）
    after_intent_target = "knowledge_retrieval" if has_knowledge else END

    # 2. 编排拓扑边
    workflow.add_edge(START, "intent_recognition")

    workflow.add_conditional_edges(
        "intent_recognition",
        _route_after_intent,
        {
            "recovery_node": "recovery_node",
            "next_stage": after_intent_target,
            "end_flow": END,
        },
    )

    if has_knowledge:
        workflow.add_conditional_edges(
            "knowledge_retrieval",
            _route_after_knowledge,
            {
                "recovery_node": "recovery_node",
                "next_stage": END,  # 后续接入 router/planner 时，只需把此处改为 "routing"
            },
        )

    workflow.add_conditional_edges(
        "recovery_node",
        _route_after_recovery,
        {
            "resume_flow": after_intent_target,  # 意图自愈成功后，自动重返主干道进入知识检索
            "end_flow": END,
        },
    )

    logger.info(
        "MasterAgentGraph compiled (knowledge_enabled=%s).", has_knowledge
    )
    return workflow.compile(checkpointer=checkpointer)
