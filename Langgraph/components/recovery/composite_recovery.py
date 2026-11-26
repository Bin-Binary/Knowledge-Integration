# /components/recovery/composite_recovery.py
import logging
from typing import Sequence

from protocols.recovery import ExceptionRecoveryProtocol
from schemas.recovery import FailureContext, RecoveryOutcome
from infra import emit_component_status

logger = logging.getLogger(__name__)

class CompositeRecoveryManager(ExceptionRecoveryProtocol):
    """异常恢复责任链分发器（与子插件共享同一协议，零基类、零多余协议）"""

    def __init__(
        self,
        handlers: Sequence[ExceptionRecoveryProtocol],
        default_fallback_message: str = "抱歉，系统处理您的请求时遇到了一点小问题，请稍后再试。",
    ) -> None:
        self._handlers = list(handlers)
        self._default_fallback_message = default_fallback_message

    async def handle_failure(self, context: FailureContext) -> RecoveryOutcome:
        for handler in self._handlers:
            try:
                outcome = await handler.handle_failure(context)
            except Exception as plugin_err:
                logger.exception(
                    "[RecoveryManager] Plugin %s raised an unexpected error while handling [%s]: %s",
                    type(handler).__name__,
                    context.category,
                    plugin_err,
                )
                continue

            if outcome is not None:
                if outcome.is_recovered:
                    emit_component_status(
                        f"[自愈检测] 自动修复成功（{outcome.action_taken}），正在恢复主流程...\n",
                    )
                return outcome

        friendly_hint = context.metadata.get("user_friendly_hint")
        return RecoveryOutcome(
            is_recovered=False,
            fallback_message=friendly_hint or self._default_fallback_message,
            action_taken=f"safe_fallback_{context.category}",
        )
