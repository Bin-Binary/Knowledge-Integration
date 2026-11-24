# graphs/execution_graph.py
import logging
from typing import Any, Callable, Dict, Optional
from langchain_core.messages import AIMessage

# 100% 依赖抽象协议门面，彻底切断与 components 具体实现层的任何耦合
from protocols import AgentResolverProtocol, ExceptionMapperProtocol
from schemas import(
    RouteContext,
    RouteDecision,
    AgentResponse,
    AgentStatus,

)
from graphs.state import MasterAgentState, extract_domain_context_from_state
from infra import log_execution

logger = logging.getLogger(__name__)


def create_execution_node(
    resolver: AgentResolverProtocol,
    map_exception: ExceptionMapperProtocol,
) -> Callable[[MasterAgentState], Any]:
    """
    统一执行节点工厂：
    1. 入站拆包：将 MasterAgentState 转换为只读 RouteContext；
    2. 协议调度：通过 AgentResolverProtocol 查找并执行对应的 AgentProtocol；
    3. 出站封包：将 AgentResponse 的 final_answer 与 updated_state 回写至主图状态；
    4. 异常接管：通过 ExceptionMapperProtocol 将执行异常转化为 FailureContext 交由 recovery_node 自愈。
    """

    @log_execution("agent_execution_node")
    async def agent_execution_node(state: MasterAgentState) -> Dict[str, Any]:
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

        try:
            agent = resolver.get(decision.target_node)
            response: AgentResponse = await agent.run(context, decision)

            # 若 Agent 主动返回业务级 FAILED 终态，抛出异常交由统一自愈体系处理
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

            updates: Dict[str, Any] = {
                "messages": [AIMessage(content=response.final_answer)],
                "final_response": response.final_answer,
                "failure_context": None,
                "recovery_outcome": None,
            }

            # 若业务 Agent 触发了会话状态机迁移（如进入多轮填槽锁），同步回写 session_state
            if response.updated_state is not None:
                updates["session_state"] = response.updated_state

            return updates

        except Exception as exc:
            prev_failure = state.get("failure_context")
            current_retry = prev_failure.retry_count if prev_failure else 0

            failure_ctx = map_exception(
                exc,
                trace_id=trace_id,
                failed_stage=f"agent_execution:{decision.target_node}",
                target_schema_name="AgentResponse",
                user_query=current_input,
                retry_count=current_retry,
            )

            logger.warning(
                "[ExecutionNode] Caught [%s] in '%s': %s",
                failure_ctx.category.value,
                decision.target_node,
                failure_ctx.error_message,
            )

            return {
                "failure_context": failure_ctx,
                "recovery_outcome": None,
            }

    return agent_execution_node
