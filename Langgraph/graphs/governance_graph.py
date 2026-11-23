# /graphs/governance_graph.py
import logging
from typing import Callable, Awaitable, Dict, Any
from langgraph.types import interrupt

from graphs.state import MasterAgentState
from protocols.governance import HumanApprovalGateProtocol
from infra.observability import log_execution

logger = logging.getLogger(__name__)


def create_approval_gate_node(
    gate: HumanApprovalGateProtocol,
) -> Callable[[MasterAgentState], Awaitable[Dict[str, Any]]]:
    """构建人工审批门禁节点（内置 LangGraph 原生 interrupt 断点挂起机制）"""

    @log_execution("approval_gate_node", level=logging.DEBUG)
    async def _node(state: MasterAgentState) -> Dict[str, Any]:
        decision = state.get("route_decision")
        if decision is None or not gate.requires_approval(decision, dict(state)):
            return {}

        logger.info(
            "[ApprovalGate] Suspending execution for human approval on target='%s'",
            decision.target_node,
        )

        # 触发 LangGraph 原生断点挂起，外部通过 Command(resume=...) 恢复执行
        approval_payload = interrupt(
            {
                "event": "HUMAN_APPROVAL_REQUIRED",
                "target_node": decision.target_node,
                "params": decision.params,
                "reason": decision.reason,
            }
        )

        # 唤醒后将审批指令合并入只读快照供 gate 校验
        merged_state = {**dict(state), "human_approval_payload": approval_payload}
        is_approved = await gate.verify_approval(merged_state)

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
