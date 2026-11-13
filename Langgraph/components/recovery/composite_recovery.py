from typing import List
from components.recovery.base import BaseRecoveryManager
from schemas.recovery import FailureContext, RecoveryOutcome


class CompositeRecoveryManager(BaseRecoveryManager):
    """
    异常恢复责任链组合器（实现 ExceptionRecoveryProtocol）：
    按顺序匹配支持当前 FailureCategory 的子类执行恢复；均未命中时自动走基类安全兜底。
    """

    def __init__(self, handlers: List[BaseRecoveryManager]) -> None:
        super().__init__()
        self._handlers = handlers

    def can_handle(self, context: FailureContext) -> bool:
        return any(h.can_handle(context) for h in self._handlers)

    async def _do_recover(self, context: FailureContext) -> RecoveryOutcome | None:
        for handler in self._handlers:
            if handler.can_handle(context):
                return await handler.handle_failure(context)
        return None
