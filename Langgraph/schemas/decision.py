# /schemas/decision.py
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import Field, field_validator
from schemas.base import ImmutableSchema, LLMOutputSchema

class FallbackTrigger(str, Enum):
    """触发回退/降级的标准原因枚举"""
    NONE = "none"
    LOW_CONFIDENCE = "low_confidence"
    TIMEOUT_OR_ERROR = "timeout_or_error"
    CONTEXT_TRUNCATED = "context_truncated"
    NODE_UNAVAILABLE = "node_unavailable"

class IntentResult(LLMOutputSchema):
    """意图识别器标准化输出（继承 LLMOutputSchema 自动忽略大模型多吐出的冗余字段）"""
    intent: str = Field(..., description="识别出的标准化意图标签")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度区间 [0.0, 1.0]")
    slots: Dict[str, Any] = Field(default_factory=dict, description="提取的关键槽位参数")
    reasoning: Optional[str] = Field(default=None, description="模型分类推理依据，提升准确率")

    @field_validator("slots", mode="before")
    @classmethod
    def coerce_none_slots_to_dict(cls, v: Any) -> Dict[str, Any]:
        """容错处理：当模型输出 "slots": null 时自动转为空字典"""
        return v if v is not None else {}


class FallbackPlan(ImmutableSchema):
    """回退执行计划"""
    trigger: FallbackTrigger
    fallback_node: str = Field(..., description="降级目标节点 ID")
    clarification_prompt: Optional[str] = Field(default=None, description="反问澄清话术")
    retry_budget: int = Field(default=0, ge=0, le=3)


class RouteDecision(ImmutableSchema):
    """路由引擎最终生成的调度契约"""
    target_node: str = Field(..., description="首选执行节点 ID")
    params: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str = Field(default="")
    fallback_plan: Optional[FallbackPlan] = None
