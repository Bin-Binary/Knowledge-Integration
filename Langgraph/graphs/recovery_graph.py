import logging
from typing import Any, Callable, Dict
from langchain_core.messages import AIMessage

from graphs.state import MasterAgentState
from protocols.components import ExceptionRecoveryProtocol
from schemas.decision import IntentResult
from schemas.recovery import FailureContext, RecoveryOutcome

logger = logging.getLogger(__name__)


def create_recovery_node(
    recovery_manager: ExceptionRecoveryProtocol,
) -> Callable[[MasterAgentState], Any]:
    """
    独立异常恢复节点工厂（严格依赖 ExceptionRecoveryProtocol，对具体恢复子类零感知）。
    职责：
    - is_recovered=True : 回填自愈后的 IntentResult 并清空 failure_context，使流程重返 Happy Path；
    - is_recovered=False: 写入兜底 AIMessage 并标记 is_terminal=True，安全终止本轮对话。
    """

    async def recovery_node(state: MasterAgentState) -> Dict[str, Any]:
        trace_id = state.get("trace_id", "unknown_trace")
        failure_ctx: FailureContext | None = state.get("failure_context")

        if failure_ctx is None:
            logger.warning(f"[RecoveryNode] Trace={trace_id} invoked without failure_context.")
            return {"is_terminal": True}

        outcome: RecoveryOutcome = await recovery_manager.handle_failure(failure_ctx)

        # 路径 A：自愈成功（例如 L1 剥离思维链或 L2 修复 JSON 还原了 IntentResult）
        if outcome.is_recovered and isinstance(outcome.recovered_data, IntentResult):
            logger.info(
                f"[RecoveryNode] Trace={trace_id} self-healed ({outcome.action_taken}), "
                f"resuming normal pipeline."
            )
            return {
                "recovery_outcome": outcome,
                "failure_context": None,
                "intent_result": outcome.recovered_data,
                "is_terminal": False,
            }

        # 路径 B：无法恢复 -> 安全兜底输出并结束流程
        logger.warning(
            f"[RecoveryNode] Trace={trace_id} degraded ({outcome.action_taken}), aborting turn safely."
        )
        fallback_text = outcome.fallback_message or "抱歉，系统处理您的请求时遇到了一点小波动，请稍后再试。"
        return {
            "recovery_outcome": outcome,
            "failure_context": None,
            "is_terminal": True,
            "messages": [AIMessage(content=fallback_text)],
        }

    return recovery_node
