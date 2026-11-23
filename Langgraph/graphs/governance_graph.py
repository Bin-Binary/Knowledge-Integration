# /graphs/governance_graph.py
import logging
from typing import Any, Awaitable, Callable, Dict, Optional
from langgraph.types import interrupt

from graphs.state import MasterAgentState, extract_domain_context_from_state
from protocols import ExceptionMapperProtocol
from protocols.governance import HumanApprovalGateProtocol
from infra.observability import log_execution

logger = logging.getLogger(__name__)


def create_approval_gate_node(
    gate: HumanApprovalGateProtocol,
    map_exception: Optional[ExceptionMapperProtocol] = None,
) -> Callable[[MasterAgentState], Awaitable[Dict[str, Any]]]:
    """构建人工审批门禁节点（内置 LangGraph 原生 interrupt 断点挂起机制）"""

    @log_execution("approval_gate_node", level=logging.DEBUG)
    async def _node(state: MasterAgentState) -> Dict[str, Any]:
        decision = state.get("route_decision")
        if decision is None:
            return {}

        # 1. 仅捕获前置策略判断异常，绝不包裹下方的 interrupt()
        try:
            need_approval = gate.requires_approval(decision, dict(state))
        except Exception as exc:
            if map_exception is None:
                raise
            return _handle_gate_error(state, exc, map_exception, "approval_gate:check")

        if not need_approval:
            return {}

        logger.info(
            "[ApprovalGate] Suspending execution for human approval on target='%s'",
            decision.target_node,
        )

        # 2. 裸露触发 LangGraph 原生断点挂起（底层依赖 GraphInterrupt 异常冒泡，禁止 try-except 拦截）
        approval_payload = interrupt(
            {
                "event": "HUMAN_APPROVAL_REQUIRED",
                "target_node": decision.target_node,
                "params": decision.params,
                "reason": decision.reason,
            }
        )

        # 3. 唤醒后捕获审批凭证校验异常
        try:
            merged_state = {**dict(state), "human_approval_payload": approval_payload}
            is_approved = await gate.verify_approval(merged_state)
        except Exception as exc:
            if map_exception is None:
                raise
            return _handle_gate_error(state, exc, map_exception, "approval_gate:verify")

        if not is_approved:
            logger.warning(
                "[ApprovalGate] Human approval rejected for target='%s'",
                decision.target_node,
            )
            return {
                "is_terminal": True,
                "final_response": "该高危操作未获得人工审批通过，任务已安全终止。",
            }

        logger.info(
            "[ApprovalGate] Human approval granted for target='%s'",
            decision.target_node,
        )
        return {}

    return _node


def _handle_gate_error(
    state: MasterAgentState,
    exc: Exception,
    map_exception: ExceptionMapperProtocol,
    stage: str,
) -> Dict[str, Any]:
    current_input, _ = extract_domain_context_from_state(state)
    prev = state.get("failure_context")
    failure_ctx = map_exception(
        exc,
        trace_id=state.get("trace_id", "unknown_trace"),
        failed_stage=stage,
        user_query=current_input,
        retry_count=prev.retry_count if prev else 0,
    )
    logger.warning(
        "[ApprovalGate] Caught [%s] at %s: %s",
        failure_ctx.category.value,
        stage,
        failure_ctx.error_message,
    )
    return {"failure_context": failure_ctx, "recovery_outcome": None}
