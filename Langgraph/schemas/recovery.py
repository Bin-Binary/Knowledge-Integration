from enum import Enum
from typing import Any, Dict, Optional
from pydantic import Field

from schemas.base import ImmutableSchema


class FailureCategory(str, Enum):
    """标准化故障分类枚举"""
    OUTPUT_FORMAT_ERROR = "output_format_error"  # 模型输出污染（如思维链/Markdown导致JSON解析失败）
    VALIDATION_ERROR = "validation_error"        # Pydantic Schema 业务字段校验不通过
    UNKNOWN_ERROR = "unknown_error"              # 未知运行时异常

class FailureContext(ImmutableSchema):
    """故障现场快照（只读契约，在节点与 Recovery 组件间传递）"""
    trace_id: str = Field(..., description="全链路追踪ID")
    failed_stage: str = Field(..., description="发生故障的图节点名称，如 intent_recognition / routing")
    category: FailureCategory = Field(..., description="归一化故障分类")
    error_message: str = Field(..., description="原始异常描述信息")
    raw_output: Optional[str] = Field(default=None, description="大模型返回的原始文本（用于格式自愈修复）")
    target_schema_name: Optional[str] = Field(default=None, description="期望修复还原的目标 Schema 名称，如 IntentResult")
    user_query: Optional[str] = Field(default=None, description="触发本轮请求的原始用户输入")
    retry_count: int = Field(default=0, ge=0, description="当前已执行的自愈重试次数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加上下文诊断信息")


class RecoveryOutcome(ImmutableSchema):
    """异常恢复组件处理结果"""
    is_recovered: bool = Field(..., description="是否自愈成功（True则重回Happy Path主干道，False则走降级分支）")
    recovered_data: Optional[Any] = Field(default=None, description="自愈还原后的合法强类型业务对象（如 IntentResult）")
    fallback_message: Optional[str] = Field(default=None, description="降级给用户的安全兜底话术或反问澄清话术")
    action_taken: str = Field(..., description="执行的恢复动作说明，便于审计日志追踪")
