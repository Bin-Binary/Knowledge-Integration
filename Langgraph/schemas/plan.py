# /schemas/plan.py
from typing import List, Optional, Set
from pydantic import Field, model_validator
from schemas.base import ImmutableSchema


class PlanStep(ImmutableSchema):
    """规划拆解出的单个原子子任务"""
    step_id: int = Field(..., ge=1, description="步骤唯一递增编号（从 1 开始）")
    description: str = Field(..., min_length=1, description="子任务具体目标与执行指令描述")
    assigned_node: str = Field(..., min_length=1, description="负责执行该步骤的原子执行器 ID")
    expected_output: Optional[str] = Field(
        default=None, description="期望该步骤产出的核心信息摘要（供后续依赖步骤参考）"
    )
    tool_hints: List[str] = Field(default_factory=list, description="建议使用的工具名称提示")
    depends_on: List[int] = Field(default_factory=list, description="前置依赖的 step_id 列表")
    requires_approval: bool = Field(
        default=False, 
        description="预留扩展：该步骤执行前是否需要人工审批确认（默认 False）"
    )    


class ExecutionPlan(ImmutableSchema):
    """规划器输出的完整执行蓝图（内置 DAG 依赖合法性校验）"""
    goal: str = Field(..., min_length=1, description="本次任务的总体终极目标")
    steps: List[PlanStep] = Field(..., min_length=1, description="有序原子执行步骤列表")
    is_replan: bool = Field(default=False, description="是否为遇到异常后的重规划方案")
    replan_count: int = Field(default=0, ge=0, description="当前累计重规划次数")

    @model_validator(mode="after")
    def validate_dag_dependencies(self) -> "ExecutionPlan":
        step_ids = [s.step_id for s in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("ExecutionPlan 校验失败：存在重复的 step_id。")

        valid_ids: Set[int] = set(step_ids)
        adj: dict[int, list[int]] = {s.step_id: [] for s in self.steps}

        for step in self.steps:
            for dep in step.depends_on:
                if dep not in valid_ids:
                    raise ValueError(f"Step {step.step_id} 依赖了不存在的步骤 ID: {dep}")
                if dep == step.step_id:
                    raise ValueError(f"Step {step.step_id} 不能依赖自身。")
                adj[dep].append(step.step_id)

        # Kahn 算法检测 DAG 是否存在循环依赖
        in_degree = {s.step_id: len(s.depends_on) for s in self.steps}
        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            curr = queue.pop(0)
            visited_count += 1
            for nxt in adj[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        if visited_count != len(self.steps):
            raise ValueError("ExecutionPlan 校验失败：步骤依赖关系中存在循环依赖（Cycle）。")

        return self
