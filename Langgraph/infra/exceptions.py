# core/exceptions.py
from typing import Any, Dict, Optional
from schemas.recovery import FailureCategory


class AgentBusinessError(Exception):
    """所有业务层预期异常的统一基类"""

    def __init__(
        self,
        message: str,
        category: FailureCategory = FailureCategory.UNKNOWN_ERROR,
        raw_output: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.raw_output = raw_output
        self.metadata = metadata or {}


class LowConfidenceIntentError(AgentBusinessError):
    """意图置信度过低，触发澄清反问恢复策略"""

    def __init__(self, intent: str, confidence: float) -> None:
        super().__init__(
            message=f"Intent '{intent}' confidence {confidence:.2f} below threshold",
            category=FailureCategory.VALIDATION_ERROR,
            metadata={"intent": intent, "confidence": confidence},
        )


class StructuredOutputError(AgentBusinessError):
    """大模型结构化输出解析或 Pydantic 校验失败（供所有 LLM 适配器统一抛出）"""

    def __init__(
        self,
        message: str,
        raw_output: Optional[str] = None,
        schema_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged_meta = {"schema_name": schema_name, **(metadata or {})}
        super().__init__(
            message=message,
            category=FailureCategory.VALIDATION_ERROR,  # 若有专门的 PARSE_ERROR 枚举可替换此处
            raw_output=raw_output,
            metadata=merged_meta,
        )
