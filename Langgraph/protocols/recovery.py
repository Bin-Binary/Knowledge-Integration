from typing import Any, Dict, Optional, Protocol, runtime_checkable
from schemas.recovery import FailureContext, RecoveryOutcome


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
    """4. 异常恢复与回退组件标准协议（供自愈节点使用）"""

    async def handle_failure(self, context: FailureContext) -> RecoveryOutcome:
        ...
