# /internal_knowledge/schemas/resolve_problem.py
"""运用层（Resolve_problem）数据模型。

以问题为驱动，检索已有知识（Means / resolutions），未解决时产出知识缺口（remaining_gap）驱动采集。
对应 FrameNet v17 Resolve_problem 的 FE 同构映射：
    Core FE:
        Agent               -> `agent_id`
        Problem             -> `problem`
        Cause               -> [设计忽略] 当前系统均由 Agent 主动触发，不引入自然原因分支
    Peripheral FE:
        Means               -> `resolutions`（检索命中的知识 ID 列表，如 ont_xxx / info_xxx）
        Purpose             -> [设计忽略] 已收敛至 problem 描述中
        Medium              -> [设计忽略] 不在本模型中表示
        Degree              -> [设计忽略] 已由 outcome 枚举定性表达，无需额外浮点数
    Extra-Thematic FE:
        Resultant_situation -> `resultant_situation`
        Outcome             -> `outcome`
"""
from typing import List, Optional
from pydantic import Field, field_validator, model_validator
from schemas.base import DocumentedEnum, ImmutableSchema

class ResolutionOutcome(DocumentedEnum):
    """问题解决结果（对应 Resolve_problem.Outcome）"""
    PENDING = ("pending", "运用状态", "任务已初始化，待检索与求解评估")
    SUCCESS = ("success", "运用结果", "问题已解决，目标状态达成，闭环终止")
    PARTIAL = ("partial", "运用结果", "部分解决，存在明确知识缺口，需补充采集")
    FAILURE = ("failure", "运用结果", "未检索到有效知识，需启动全新采集")

class ResolveProblem(ImmutableSchema):
    """运用层契约：记录单次问题求解过程及遗留的知识缺口"""
    problem_id: str = Field(..., min_length=1, description="问题追踪唯一标识")
    problem: str = Field(..., min_length=1, description="待解决的具体问题或目标")
    agent_id: str = Field(default="default_agent", description="触发求解的主体标识")

    # 【存储.retrieve】阶段填充
    resolutions: List[str] = Field(default_factory=list, description="检索命中的关联知识 ID 集合（如 ont_xxx / info_xxx）")

    # 【运用.resolve】阶段填充
    outcome: ResolutionOutcome = Field(
        default=ResolutionOutcome.PENDING, description="本次知识运用的评估结果状态"
    )
    resultant_situation: Optional[str] = Field(
        default=None, description="达成的结果状态或生成的最终答案"
    )
    remaining_gap: Optional[str] = Field(
        default=None, description="未解决的知识缺口描述（PARTIAL 或 FAILURE 时必填，用于驱动采集）"
    )

    @field_validator("resolutions", mode="before")
    @classmethod
    def coerce_none_resolutions_to_list(cls, v: Optional[List[str]]) -> List[str]:
        """容错：将 null 归一化为空列表。"""
        return v if v is not None else []

    @model_validator(mode="after")
    def validate_closed_loop(self) -> "ResolveProblem":
        """闭环约束：求解评估完成后，只要未彻底解决，就必须提供 remaining_gap 触发下一轮采集"""
        if self.outcome in (ResolutionOutcome.PARTIAL, ResolutionOutcome.FAILURE) and not self.remaining_gap:
            raise ValueError(f"outcome 为 {self.outcome.value} 时，必须提供 remaining_gap 以驱动采集")
        return self
