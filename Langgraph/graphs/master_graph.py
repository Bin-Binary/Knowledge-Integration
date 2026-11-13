import logging
from typing import Any, Optional, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from protocols.components import IntentRecognizerProtocol
from protocols.components import ExceptionRecoveryProtocol
from graphs.state import MasterAgentState
from graphs.intent_graph import create_intent_node
from graphs.recovery_graph import create_recovery_node


logger = logging.getLogger(__name__)

def _route_after_intent(state: MasterAgentState) -> Literal["recovery_node", "next_stage"]:
    """意图识别出口条件边：捕获到 failure_context 时跳转 recovery_node"""
    if state.get("failure_context") is not None:
        return "recovery_node"
    return "next_stage"


def _route_after_recovery(state: MasterAgentState) -> Literal["resume_flow", "end_flow"]:
    """
    异常恢复出口条件边：
    - 自愈成功（is_recovered=True 且未标记终态）-> 重返主干道继续流转；
    - 兜底终止（is_terminal=True）-> 直接走 END 结束本轮对话。
    """
    outcome = state.get("recovery_outcome")
    if outcome is not None and outcome.is_recovered and not state.get("is_terminal", False):
        return "resume_flow"
    return "end_flow"

def build_master_agent_graph(
    intent_recognizer: IntentRecognizerProtocol,
    recovery_manager: ExceptionRecoveryProtocol,
    # [预留扩展参数位 - 后续逐步取消注释接入]
    # window_pipeline: Optional[Any] = None,
    # router: Optional[RouterProtocol] = None,
    # planner: Optional[PlannerProtocol] = None,
    # executors: Optional[Dict[str, AgentProtocol]] = None,
    checkpointer: Optional[Any] = None
) -> CompiledStateGraph:
    """
    生产环境主控状态图构建器。
    采用管道式阶段设计，支持各核心组件热插拔与渐进式集成。
    """
    workflow = StateGraph(MasterAgentState)

    # 1. 注册核心节点
    workflow.add_node("intent_recognition", create_intent_node(intent_recognizer))
    workflow.add_node("recovery_node", create_recovery_node(recovery_manager))

    # 2. 编排拓扑边
    workflow.add_edge(START, "intent_recognition")

    workflow.add_conditional_edges(
        "intent_recognition",
        _route_after_intent,
        {
            "recovery_node": "recovery_node",
            "next_stage": END,  # 下一步接入 ChainRouter 时，此处改为 "routing"
        },
    )

    workflow.add_conditional_edges(
        "recovery_node",
        _route_after_recovery,
        {
            "resume_flow": END,  # 自愈成功后，下一步同样改为 "routing" 重回主干道
            "end_flow": END,
        },
    )

    logger.info("MasterAgentGraph compiled with Intent <-> Recovery self-healing loop.")
    return workflow.compile(checkpointer=checkpointer)
