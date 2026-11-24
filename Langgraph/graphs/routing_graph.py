# /graphs/routing_graph.py
import inspect
import logging
from typing import Any, Callable, Dict

from schemas import RouteContext
from protocols import RouterProtocol, ExceptionMapperProtocol
from graphs.state import MasterAgentState, extract_domain_context_from_state
from infra import log_execution

logger = logging.getLogger(__name__)


def create_routing_node(
    router: RouterProtocol,
    map_exception: ExceptionMapperProtocol,
) -> Callable[[MasterAgentState], Any]:
    """路由调度节点：调用 RouterProtocol.dispatch 产出 RouteDecision，异常交由 recovery_node 自愈"""

    @log_execution("routing_node")
    async def routing_node(state: MasterAgentState) -> Dict[str, Any]:
        trace_id = state.get("trace_id", "unknown_trace")
        session_id = state.get("session_id", "unknown_session")
        current_input, safe_history = extract_domain_context_from_state(state)

        context = RouteContext(
            session_id=session_id,
            current_input=current_input,
            safe_history=safe_history,
        )
        intent_result = state.get("intent_result")

        try:
            raw_call = router.dispatch(context, intent_result)
            decision = await raw_call if inspect.isawaitable(raw_call) else raw_call

            logger.info(
                "[RoutingNode] Target=%s | Domain=%s | Conf=%.2f",
                decision.target_node,
                decision.params.get("target_domain", "execution"),
                decision.confidence,
            )
            return {
                "route_decision": decision,
                "failure_context": None,
                "recovery_outcome": None,
            }
        except Exception as exc:
            prev_failure = state.get("failure_context")
            current_retry = prev_failure.retry_count if prev_failure else 0
            failure_ctx = map_exception(
                exc,
                trace_id=trace_id,
                failed_stage="routing",
                target_schema_name="RouteDecision",
                user_query=current_input,
                retry_count=current_retry,
            )
            logger.warning(
                "[RoutingNode] Caught [%s]: %s",
                failure_ctx.category.value,
                failure_ctx.error_message,
            )
            return {
                "route_decision": None,
                "failure_context": failure_ctx,
                "recovery_outcome": None,                
            }

    return routing_node
