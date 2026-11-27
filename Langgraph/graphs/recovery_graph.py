# /graphs/recovery_graph.py
import logging
from typing import Any, Callable, Dict, Optional, Tuple, Type
from langchain_core.messages import AIMessage

from graphs.state import MasterAgentState
from protocols import ExceptionRecoveryProtocol
from schemas import (
    IntentResult,
    RouteDecision,
    FailureContext,
    RecoveryOutcome,
)
from infra import log_execution

logger = logging.getLogger(__name__)

# 默认的故障阶段状态回填映射表：{failed_stage: (state_field_name, expected_type)}
DEFAULT_STAGE_RESTORE_MAP: Dict[str, Tuple[str, Type[Any]]] = {
    "intent_recognition": ("intent_result", IntentResult),
    "routing": ("route_decision", RouteDecision),
}


def create_recovery_node(
    recovery_manager: ExceptionRecoveryProtocol,
    stage_restore_map: Optional[Dict[str, Tuple[str, Type[Any]]]] = None,
) -> Callable[[MasterAgentState], Any]:
    """
    独立异常恢复节点工厂（严格依赖 ExceptionRecoveryProtocol，对具体恢复子类零感知）。
    职责：
    - is_recovered=True : 按故障阶段回填自愈后的业务对象并清空 failure_context，使流程重返 Happy Path；
    - is_recovered=False: 写入兜底 AIMessage 与 final_response 并标记 is_terminal=True，安全终止本轮对话；
    - 全程维护 _recovery_attempts 与 _last_failed_node，防止图状态机发生无限重试死循环。
    """
    restore_rules = {**DEFAULT_STAGE_RESTORE_MAP, **(stage_restore_map or {})}

    def _build_fallback_updates(
        outcome: RecoveryOutcome,
        fallback_text: str,
        tracking_updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            **tracking_updates,
            "recovery_outcome": outcome,
            "failure_context": None,
            "is_terminal": True,
            "final_response": fallback_text,
            "messages": [AIMessage(content=fallback_text)],
        }

    @log_execution("recovery_node")
    async def recovery_node(state: MasterAgentState) -> Dict[str, Any]:
        failure_ctx: Optional[FailureContext] = state.get("failure_context")

        if failure_ctx is None:
            logger.warning("[RecoveryNode] Invoked without failure_context.")
            return {"is_terminal": True}

        current_attempts = state.get("_recovery_attempts", 0) 
        tracking_updates: Dict[str, Any] = {
            "_recovery_attempts": current_attempts,
            "_last_failed_node": failure_ctx.failed_stage,
        }

        # 2. 调度异常恢复责任链
        outcome: RecoveryOutcome = await recovery_manager.handle_failure(failure_ctx)

        # 3. 自愈成功分支：查表校验类型并回填状态机字段
        if outcome.is_recovered and outcome.recovered_data is not None:
            rule = restore_rules.get(failure_ctx.failed_stage)
            if rule is not None and isinstance(outcome.recovered_data, rule[1]):
                state_key = rule[0]
                logger.info(
                    "[RecoveryNode] Self-healed (%s) at stage '%s' (attempt #%d), resuming pipeline.",
                    outcome.action_taken,
                    failure_ctx.failed_stage,
                    current_attempts,
                )
                return {
                    **tracking_updates,
                    state_key: outcome.recovered_data,
                    "recovery_outcome": outcome,
                    "failure_context": None,
                    "is_terminal": False,
                }

            logger.error(
                "[RecoveryNode] Recovered data type mismatch for stage=%s, actual=%s",
                failure_ctx.failed_stage,
                type(outcome.recovered_data).__name__,
            )
            return _build_fallback_updates(
                outcome,
                "抱歉，系统内部状态还原异常，请稍后再试。",
                tracking_updates,
            )

        # 4. 无法自愈 / 降级终止分支
        logger.warning(
            "[RecoveryNode] Degraded (%s) at stage '%s' (attempt #%d), aborting turn safely.",
            outcome.action_taken,
            failure_ctx.failed_stage,
            current_attempts,
        )
        fallback_text = (
            outcome.fallback_message
            or "抱歉，系统处理您的请求时遇到了一点小波动，请稍后再试。"
        )
        return _build_fallback_updates(outcome, fallback_text, tracking_updates)

    return recovery_node
