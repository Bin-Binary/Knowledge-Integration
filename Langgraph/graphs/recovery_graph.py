# /graphs/recovery_graph.py
import logging
from typing import Any, Callable, Dict
from langchain_core.messages import AIMessage

from graphs.state import MasterAgentState
from protocols.components import ExceptionRecoveryProtocol
from schemas.decision import IntentResult, RouteDecision
from schemas.recovery import FailureContext, RecoveryOutcome
from infra.observability import log_execution
logger = logging.getLogger(__name__)


def create_recovery_node(
    recovery_manager: ExceptionRecoveryProtocol,
) -> Callable[[MasterAgentState], Any]:
    """
    独立异常恢复节点工厂（严格依赖 ExceptionRecoveryProtocol，对具体恢复子类零感知）。
    职责：
    - is_recovered=True : 按故障阶段回填自愈后的业务对象并清空 failure_context，使流程重返 Happy Path；
    - is_recovered=False: 写入兜底 AIMessage 与 final_response 并标记 is_terminal=True，安全终止本轮对话。
    """

    # 定义内部纯函数构建兜底状态，替代错误的 self._build_fallback_state
    def _build_fallback_updates(
        outcome: RecoveryOutcome, fallback_text: str
    ) -> Dict[str, Any]:
        return {
            "recovery_outcome": outcome,
            "failure_context": None,
            "is_terminal": True,
            "final_response": fallback_text,
            "messages": [AIMessage(content=fallback_text)],
        }

    @log_execution("recovery_node")
    async def recovery_node(state: MasterAgentState) -> Dict[str, Any]:
        failure_ctx: FailureContext | None = state.get("failure_context")

        if failure_ctx is None:
            logger.warning("[RecoveryNode] Invoked without failure_context.")
            return {"is_terminal": True}

        outcome: RecoveryOutcome = await recovery_manager.handle_failure(failure_ctx)

        if outcome.is_recovered and outcome.recovered_data is not None:
            updates: Dict[str, Any] = {
                "recovery_outcome": outcome,
                "failure_context": None,
                "is_terminal": False,
            }
            if failure_ctx.failed_stage == "intent_recognition" and isinstance(
                outcome.recovered_data, IntentResult
            ):
                updates["intent_result"] = outcome.recovered_data
            elif failure_ctx.failed_stage == "routing" and isinstance(
                outcome.recovered_data, RouteDecision
            ):
                updates["route_decision"] = outcome.recovered_data
            else:
                logger.error(
                    f"[RecoveryNode] Recovered data type mismatch "
                    f"for stage={failure_ctx.failed_stage}, actual={type(outcome.recovered_data).__name__}"
                )
                return _build_fallback_updates(
                    outcome, "抱歉，系统内部状态还原异常，请稍后再试。"
                )

            logger.info(
                f"[RecoveryNode] Self-healed ({outcome.action_taken}), resuming pipeline."
            )
            return updates

        logger.warning(
            f"[RecoveryNode] Degraded ({outcome.action_taken}), aborting turn safely."
        )
        fallback_text = (
            outcome.fallback_message
            or "抱歉，系统处理您的请求时遇到了一点小波动，请稍后再试。"
        )
        return _build_fallback_updates(outcome, fallback_text)

    return recovery_node
