import logging
from abc import ABC, abstractmethod
from typing import Optional

from schemas.recovery import FailureContext, RecoveryOutcome

logger = logging.getLogger(__name__)

class BaseRecoveryManager(ABC):
    """
    异常恢复基类（实现 ExceptionRecoveryProtocol 契约）：
    采用模板方法模式，统一收敛日志记录、子类判断是否接管（can_handle）以及默认安全兜底。
    """

    def __init__(self, default_fallback_message: str = "抱歉，系统处理您的请求时遇到了一点小问题，请稍后再试。") -> None:
        self._default_fallback_message = default_fallback_message

    def can_handle(self, context: FailureContext) -> bool:
        """子类重写：声明当前恢复器是否支持处理该类型的 FailureContext"""
        return True

    async def handle_failure(self, context: FailureContext) -> RecoveryOutcome:
        """统一对外入口（满足 ExceptionRecoveryProtocol 协议）"""
        if not self.can_handle(context):
            return self._fallback_outcome(
                context=context,
                action_taken=f"unhandled_category_{context.category.value}",
            )

        logger.warning(
            f"[{context.trace_id}] {self.__class__.__name__} handling failure | "
            f"stage={context.failed_stage} | category={context.category.value}"
        )

        outcome = await self._do_recover(context)
        if outcome is not None:
            return outcome

        return self._fallback_outcome(
            context=context,
            action_taken=f"fallback_after_{self.__class__.__name__}",
        )

    @abstractmethod
    async def _do_recover(self, context: FailureContext) -> Optional[RecoveryOutcome]:
        """子类核心扩展点：执行具体的自愈逻辑；若无法修复返回 None 交由基类兜底"""
        ...

    def _fallback_outcome(
        self,
        context: FailureContext,
        action_taken: str,
        custom_message: Optional[str] = None,
    ) -> RecoveryOutcome:
        return RecoveryOutcome(
            is_recovered=False,
            fallback_message=custom_message or self._default_fallback_message,
            action_taken=action_taken,
        )
