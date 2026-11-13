# protocols/components.py
from typing import Protocol, runtime_checkable, Optional, List
from schemas.context import RouteContext
from schemas.decision import IntentResult, RouteDecision
from schemas.plan import ExecutionPlan
from schemas.execution import AgentStep
from schemas.recovery import FailureContext, RecoveryOutcome

@runtime_checkable
class IntentRecognizerProtocol(Protocol):
    """1. 意图识别组件协议"""
    def recognize(self, context: RouteContext) -> Optional[IntentResult]:
        ...

@runtime_checkable
class RouterProtocol(Protocol):
    """2. 路由调度组件协议"""
    def dispatch(self, context: RouteContext, intent: Optional[IntentResult]) -> RouteDecision:
        ...

@runtime_checkable
class PlannerProtocol(Protocol):
    """3. 任务规划组件协议"""
    def create_plan(self, context: RouteContext, decision: RouteDecision) -> ExecutionPlan:
        ...

    def replan(
        self, 
        context: RouteContext, 
        original_plan: ExecutionPlan, 
        completed_steps: List[AgentStep],
        error_reason: str
    ) -> ExecutionPlan:
        ...

@runtime_checkable
class ExceptionRecoveryProtocol(Protocol):
    """4.异常恢复与回退组件标准协议"""

    async def handle_failure(self, context: FailureContext) -> RecoveryOutcome:
        ...
