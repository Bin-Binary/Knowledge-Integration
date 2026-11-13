from typing import TypedDict, Annotated, Optional, List, Dict, Any
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph.message import add_messages

from schemas.context import Message, WindowMetrics
from schemas.decision import IntentResult, RouteDecision

class MasterAgentState(TypedDict, total=False):
    """
    生产级全局图状态（TypedDict + Pydantic 混合模式）。
    使用 total=False 允许各阶段节点仅返回自己负责更新的增量字段。
    """
    # 核心对话流（由 LangGraph 原生 Reducer 自动合并）
    messages: Annotated[List[AnyMessage], add_messages]

    # 会话与系统元数据
    session_id: str
    session_state: Optional[str]              # 供后续状态机路由使用（如 "LOCKED:refund_flow"）
    user_profile: Dict[str, Any]

    # 滑动窗口与上下文载荷（后续接入 WindowPipeline 时填充）
    rag_context: Optional[str]
    window_metrics: Optional[WindowMetrics]

    # 各阶段核心决策产物（Pydantic 不可变对象）
    intent_result: Optional[IntentResult]     # 【当前阶段】意图识别输出
    route_decision: Optional[RouteDecision]   # 【下一阶段】路由调度输出
    final_response: Optional[str]             # 【终态输出】执行器生成的最终回复


def extract_domain_context_from_state(state: MasterAgentState) -> tuple[str, List[Message]]:
    """
    生产级消息适配器：将 LangGraph 的 AnyMessage 列表安全转换为内部领域 Message 列表。
    隔离 LangChain 框架类型对内部纯业务逻辑的侵入。
    """
    lc_messages = state.get("messages", [])
    if not lc_messages:
        return "", []

    last_msg = lc_messages[-1]
    current_input = str(last_msg.content) if isinstance(last_msg, HumanMessage) else ""

    history: List[Message] = []
    for msg in lc_messages[:-1]:
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, ToolMessage):
            role = "tool"
        else:
            continue
        history.append(Message(role=role, content=str(msg.content)))

    return current_input, history
