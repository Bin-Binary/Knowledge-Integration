import logging
from typing import Any, Callable, Dict, Optional, Tuple

from langchain_core.messages import AIMessage
from langgraph.config import get_stream_writer

from protocols import AgentResolverProtocol, ExceptionMapperProtocol
from schemas import (
    RouteContext,
    RouteDecision,
    AgentResponse,
    AgentStatus,
    AgentStep,
    AgentToken,
)
from graphs.state import MasterAgentState, extract_domain_context_from_state
from infra import log_execution

logger = logging.getLogger(__name__)


def _unpack_execution_inputs(
    state: MasterAgentState,
) -> Tuple[str, str, RouteDecision, RouteContext]:
    """公共入站拆包：提取追踪信息、路由决策与只读业务上下文"""
    trace_id = state.get("trace_id", "unknown_trace")
    session_id = state.get("session_id", "unknown_session")
    current_input, safe_history = extract_domain_context_from_state(state)

    decision: Optional[RouteDecision] = state.get("route_decision")
    if decision is None:
        raise ValueError("Execution node invoked without route_decision in state.")

    context = RouteContext(
        session_id=session_id,
        current_input=current_input,
        safe_history=safe_history,
        rag_context=state.get("rag_context"),
        window_metrics=state.get("window_metrics"),
        session_state=state.get("session_state"),
        user_profile=state.get("user_profile", {}),
    )
    return trace_id, current_input, decision, context


def _pack_execution_updates(response: AgentResponse) -> Dict[str, Any]:
    """公共出站封包：将 AgentResponse 转换为图状态增量更新"""
    updates: Dict[str, Any] = {
        "messages": [AIMessage(content=response.final_answer)],
        "final_response": response.final_answer,
        "failure_context": None,
        "recovery_outcome": None,
    }
    if response.updated_state is not None:
        updates["session_state"] = response.updated_state
    return updates


def _handle_execution_error(
    state: MasterAgentState,
    exc: Exception,
    map_exception: ExceptionMapperProtocol,
    trace_id: str,
    current_input: str,
    target_node: str,
) -> Dict[str, Any]:
    """公共异常接管：映射为 FailureContext 交由 recovery_node 自愈"""
    current_retry = state.get("_recovery_attempts", 0)

    failure_ctx = map_exception(
        exc,
        trace_id=trace_id,
        failed_stage=f"agent_execution:{target_node}",
        target_schema_name="AgentResponse",
        user_query=current_input,
        retry_count=current_retry,
    )

    logger.warning(
        "[ExecutionNode] Caught [%s] in '%s': %s",
        failure_ctx.category,
        target_node,
        failure_ctx.error_message,
    )

    return {
        "failure_context": failure_ctx,
        "recovery_outcome": None,
    }


def create_execution_node(
    resolver: AgentResolverProtocol,
    map_exception: ExceptionMapperProtocol,
) -> Callable[[MasterAgentState], Any]:
    """统一非流式执行节点工厂"""

    @log_execution("agent_execution_node")
    async def agent_execution_node(state: MasterAgentState) -> Dict[str, Any]:
        trace_id, current_input, decision, context = _unpack_execution_inputs(state)

        try:
            agent = resolver.get(decision.target_node)
            response: AgentResponse = await agent.run(context, decision)

            if response.status == AgentStatus.FAILED:
                raise RuntimeError(
                    response.error_message
                    or f"Agent '{decision.target_node}' reported FAILED status."
                )

            logger.info(
                "[ExecutionNode] Agent=%s | Status=%s | Steps=%d",
                decision.target_node,
                response.status.value,
                len(response.steps),
            )
            return _pack_execution_updates(response)

        except Exception as exc:
            return _handle_execution_error(
                state, exc, map_exception, trace_id, current_input, decision.target_node
            )

    return agent_execution_node


def create_streaming_execution_node(
    resolver: AgentResolverProtocol,
    map_exception: ExceptionMapperProtocol,
) -> Callable[[MasterAgentState], Any]:
    """流式执行节点工厂：消费 AgentProtocol.stream() 并通过 LangGraph custom stream 实时向外推送"""

    @log_execution("agent_streaming_execution_node")
    async def agent_streaming_execution_node(state: MasterAgentState) -> Dict[str, Any]:
        writer = get_stream_writer()
        trace_id, current_input, decision, context = _unpack_execution_inputs(state)

        try:
            agent = resolver.get(decision.target_node)
            final_response: Optional[AgentResponse] = None

            async for item in agent.stream(context, decision):
                if isinstance(item, AgentToken):
                    writer({"type": "token", "content": item.content})
                elif isinstance(item, AgentStep):
                    writer({"type": "step", "thought": item.thought, "action": item.action})
                elif isinstance(item, AgentResponse):
                    final_response = item

            if final_response is None or final_response.status == AgentStatus.FAILED:
                raise RuntimeError(
                    (final_response.error_message if final_response else None)
                    or f"Streaming agent '{decision.target_node}' failed or terminated without AgentResponse."
                )

            logger.info(
                "[StreamingExecutionNode] Agent=%s | Status=%s | Steps=%d",
                decision.target_node,
                final_response.status.value,
                len(final_response.steps),
            )
            return _pack_execution_updates(final_response)

        except Exception as exc:
            return _handle_execution_error(
                state, exc, map_exception, trace_id, current_input, decision.target_node
            )

    return agent_streaming_execution_node
