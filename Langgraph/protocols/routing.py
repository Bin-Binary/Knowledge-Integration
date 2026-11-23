from typing import Optional, Protocol, runtime_checkable
from schemas.context import RouteContext
from schemas.decision import IntentResult, RouteDecision


@runtime_checkable
class IntentRecognizerProtocol(Protocol):
    """1. 意图识别组件协议"""

    async def recognize(self, context: RouteContext) -> Optional[IntentResult]:
        ...


@runtime_checkable
class RouterProtocol(Protocol):
    """2. 路由调度组件协议"""

    async def dispatch(
        self, context: RouteContext, intent: Optional[IntentResult]
    ) -> RouteDecision:
        ...
