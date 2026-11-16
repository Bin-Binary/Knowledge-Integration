# core/exceptions.py
from typing import Any, Dict, Optional
from schemas.recovery import FailureCategory

class AgentBusinessError(Exception):
    """所有业务层预期异常的统一基类
    示例：：意图置信度过低，需要触发澄清反问恢复策略
    class LowConfidenceIntentError(AgentBusinessError):
    def __init__(self, intent: str, confidence: float):
        super().__init__(
            message=f"Intent '{intent}' confidence {confidence:.2f} below threshold",
            category=FailureCategory.VALIDATION_ERROR,
            metadata={"intent": intent, "confidence": confidence},
        )
    """
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

