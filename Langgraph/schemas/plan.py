# /schemas/plan.py
from typing import List, Dict, Any, Optional
from pydantic import Field
from schemas.base import ImmutableSchema

class PlanStep(ImmutableSchema):
    """规划拆解出的单个原子子任务"""
    step_id: int = Field(..., ge=1)
    description: str = Field(..., description="子任务具体目标描述")
    assigned_node: str = Field(..., description="负责执行该步骤的 Executor ID")
    tool_hints: List[str] = Field(default_factory=list, description="建议使用的工具名称提示")
    depends_on: List[int] = Field(default_factory=list, description="前置依赖的 step_id 列表")

class ExecutionPlan(ImmutableSchema):
    """规划器输出的完整执行蓝图"""
    goal: str
    steps: List[PlanStep] = Field(..., min_length=1)
    is_replan: bool = False
