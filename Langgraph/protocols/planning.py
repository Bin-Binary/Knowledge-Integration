from typing import List, Protocol, runtime_checkable
from schemas.context import RouteContext
from schemas.decision import RouteDecision
from schemas.execution import AgentStep
from schemas.plan import ExecutionPlan


@runtime_checkable
class PlannerProtocol(Protocol):
    """3. 任务规划组件协议"""

    async def create_plan(
        self, context: RouteContext, decision: RouteDecision
    ) -> ExecutionPlan:
        ...

    async def replan(
        self,
        context: RouteContext,
        original_plan: ExecutionPlan,
        completed_steps: List[AgentStep],
        error_reason: str,
    ) -> ExecutionPlan:
        ...
