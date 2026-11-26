# /core/exceptions.py
from typing import Any, Dict, Optional


class AgentBusinessError(Exception):
    """所有业务层预期异常的统一基类（天然满足 ClassifiableErrorProtocol，无需显式继承 Protocol）"""

    def __init__(
        self,
        message: str,
        error_code: str = "system.unknown_error",
        raw_output: Optional[str] = None,
        user_friendly_hint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self._error_code = error_code
        self.raw_output = raw_output
        self._user_friendly_hint = user_friendly_hint
        self._metadata = dict(metadata or {})

    @property
    def error_code(self) -> str:
        """满足 ClassifiableErrorProtocol"""
        return self._error_code

    @property
    def user_friendly_hint(self) -> Optional[str]:
        """满足 ClassifiableErrorProtocol"""
        return self._user_friendly_hint

    def to_failure_metadata(self) -> Dict[str, Any]:
        """满足 ClassifiableErrorProtocol"""
        return dict(self._metadata)


class LowConfidenceIntentError(AgentBusinessError):
    """意图置信度过低，触发澄清反问恢复策略"""

    def __init__(self, intent: str, confidence: float) -> None:
        super().__init__(
            message=f"Intent '{intent}' confidence {confidence:.2f} below threshold",
            error_code="intent.low_confidence",  # 点分码比笼统的 VALIDATION_ERROR 更精准
            user_friendly_hint="抱歉，我还不太确定您的具体意图，能否再补充说明一下您的需求？",
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
            error_code="output.format_error",
            raw_output=raw_output,
            metadata=merged_meta,
        )


class ModelServiceUnavailableError(AgentBusinessError):
    """大模型网关限流（429）、服务不可用（502/503/504）或请求超时（防腐层统一异常）"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        schema_name: Optional[str] = None,
        is_rate_limit: bool = False,
    ) -> None:
        hint = (
            "当前模型服务请求过于频繁（触发限流），请稍等几秒后重试。"
            if is_rate_limit
            else "模型服务响应超时或暂时不可用，请稍后重试。"
        )
        super().__init__(
            message=message,
            error_code="model.rate_limited" if is_rate_limit else "model.unavailable",
            user_friendly_hint=hint,
            metadata={
                "status_code": status_code,
                "schema_name": schema_name,
                "is_rate_limit": is_rate_limit,
            },
        )


class KnowledgePipelineError(AgentBusinessError):
    """域内知识库采集/组织/检索环节的可预期业务异常"""

    def __init__(
        self,
        message: str,
        stage: str = "acquisition",
        user_friendly_hint: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged_meta = {"pipeline_stage": stage, **(metadata or {})}
        super().__init__(
            message=message,
            error_code=f"knowledge.{stage}_error",  # 动态点分码，如 knowledge.acquisition_error
            user_friendly_hint=user_friendly_hint or message,
            metadata=merged_meta,
        )
