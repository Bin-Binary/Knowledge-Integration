from typing import Any, Dict, Optional, Protocol, runtime_checkable
from schemas.recovery import FailureContext, RecoveryOutcome

@runtime_checkable
class ClassifiableErrorProtocol(Protocol):
    """自描述异常协议：纯原语 str 契约，完全不依赖任何具体业务枚举"""

    @property
    def error_code(self) -> str:
        """点分命名空间错误路由键，如 'model.unavailable' / 'output.format_error'"""
        ...

    @property
    def user_friendly_hint(self) -> Optional[str]:
        """可选的用户友好降级提示"""
        ...

    def to_failure_metadata(self) -> Dict[str, Any]:
        """导出诊断上下文元数据"""
        ...

@runtime_checkable
class ExceptionMapperProtocol(Protocol):
    """异常标准化映射协议（供各执行节点捕获异常时使用）"""

    def __call__(
        self,
        exc: Exception,
        *,
        trace_id: str,
        failed_stage: str,
        target_schema_name: Optional[str] = None,
        user_query: Optional[str] = None,
        retry_count: int = 0,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> FailureContext:
        ...


@runtime_checkable
class ExceptionRecoveryProtocol(Protocol):
    """异常恢复统一协议（单插件与组合责任链共享同一契约：无法修复时返回 None）"""

    async def handle_failure(self, context: FailureContext) -> Optional[RecoveryOutcome]:
        ...
