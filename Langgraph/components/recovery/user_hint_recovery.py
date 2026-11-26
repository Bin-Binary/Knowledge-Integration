# /components/recovery/user_hint_recovery.py
from typing import Optional

from components.recovery.registry import RecoveryPluginRegistry
from schemas.recovery import FailureContext, RecoveryOutcome


@RecoveryPluginRegistry.register("user_hint_fallback")
class UserHintFallbackRecovery:
    """
    可预期异常友好引导与终端降级插件（实现 ExceptionRecoveryProtocol）：
    - 承接 intent.* / knowledge.* / model.*（主备双模型全挂后的最终限流/繁忙提示）。
    - 直接提取异常或配置自带的 user_friendly_hint 回复用户，优雅终止本轮执行。
    """

    HANDLED_PREFIXES = ("intent.", "knowledge.", "model.")

    async def handle_failure(self, context: FailureContext) -> Optional[RecoveryOutcome]:
        if not context.category.startswith(self.HANDLED_PREFIXES):
            return None

        hint = context.metadata.get("user_friendly_hint")
        if not hint:
            return None

        return RecoveryOutcome(
            is_recovered=False,
            fallback_message=hint,
            action_taken=f"graceful_hint_reply_{context.category}",
        )
