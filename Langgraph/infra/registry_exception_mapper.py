# /infra/registry_exception_mapper.py
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Type

from protocols.recovery import ClassifiableErrorProtocol, ExceptionMapperProtocol
from schemas.recovery import FailureContext

_SENSITIVE_PATTERN = re.compile(
    r"(sk-[a-zA-Z0-9]{16,}|Bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ExceptionMappingSpec:
    """声明式异常映射规格（纯标准库数据契约）"""
    exc_types: Tuple[Type[BaseException], ...]
    error_code: str
    message_template: str = "[{exc_name}] {exc}"
    user_friendly_hint: Optional[str] = None
    formatter: Optional[Callable[[BaseException], str]] = None
    metadata_extractor: Optional[Callable[[BaseException], Dict[str, Any]]] = None
    static_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class _MatchResult:
    """内部匹配结果载体（替代对原始异常实例的 setattr 篡改）"""
    error_code: str
    message: str
    user_friendly_hint: Optional[str] = None
    raw_output: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


ExceptionRule = Callable[[BaseException], Optional[_MatchResult]]


class RegistryExceptionMapper(ExceptionMapperProtocol):
    """符合开闭原则的异常标准化映射器（支持原生 Spec 注册与协议自省）"""

    def __init__(
        self,
        *,
        default_category: str = "system.unknown_error",
        max_error_length: int = 1000,
        enable_sanitization: bool = True,
    ) -> None:
        self._default_category = default_category
        self._max_error_length = max_error_length
        self._enable_sanitization = enable_sanitization
        self._rules: list[ExceptionRule] = []

    def register_rule(self, rule: ExceptionRule) -> "RegistryExceptionMapper":
        """注册底层自定义匹配函数"""
        self._rules.append(rule)
        return self

    def register_spec(self, spec: ExceptionMappingSpec) -> "RegistryExceptionMapper":
        """原生注册单条声明式映射规格（零副作用，不修改异常实例）"""
        def _rule(exc: BaseException) -> Optional[_MatchResult]:
            if not isinstance(exc, spec.exc_types):
                return None

            msg = (
                spec.formatter(exc)
                if spec.formatter is not None
                else spec.message_template.format(exc_name=type(exc).__name__, exc=exc)
            )

            extra = dict(spec.static_metadata)
            if spec.metadata_extractor is not None:
                extra.update(spec.metadata_extractor(exc))

            # 若提取器中包含了 raw_output，单独剥离到顶层字段
            raw_out = extra.pop("raw_output", None)

            return _MatchResult(
                error_code=spec.error_code,
                message=msg,
                user_friendly_hint=spec.user_friendly_hint,
                raw_output=str(raw_out) if raw_out is not None else None,
                metadata=extra,
            )

        return self.register_rule(_rule)

    def register_specs(self, specs: Iterable[ExceptionMappingSpec]) -> "RegistryExceptionMapper":
        """批量注册声明式规格表"""
        for spec in specs:
            self.register_spec(spec)
        return self

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
        matched = self._match_exception(exc)

        category = matched.error_code if matched else self._default_category
        raw_msg = matched.message if matched else f"[{type(exc).__name__}] {exc}"
        error_message = self._sanitize_and_truncate(raw_msg)

        raw_output = (matched.raw_output if matched and matched.raw_output is not None else None) or self._extract_raw_output(exc)
        metadata = self._build_metadata(exc, matched, extra_metadata)

        return FailureContext(
            trace_id=trace_id,
            failed_stage=failed_stage,
            category=category,
            error_message=error_message,
            raw_output=raw_output,
            target_schema_name=target_schema_name,
            user_query=user_query,
            retry_count=retry_count,
            metadata=metadata,
        )

    def _match_exception(self, exc: Exception) -> Optional[_MatchResult]:
        for curr in self._iter_exception_chain(exc):
            # 1. 自描述协议直通（优先级最高）
            if isinstance(curr, ClassifiableErrorProtocol):
                return _MatchResult(
                    error_code=curr.error_code,
                    message=f"[{type(curr).__name__}] {curr}",
                    user_friendly_hint=curr.user_friendly_hint,
                    raw_output=getattr(curr, "raw_output", None),
                    metadata=curr.to_failure_metadata(),
                )

            # 2. 遍历注册的规则
            for rule in self._rules:
                result = rule(curr)
                if result is not None:
                    return result
        return None

    def _sanitize_and_truncate(self, msg: str) -> str:
        if self._enable_sanitization:
            msg = _SENSITIVE_PATTERN.sub("[REDACTED]", msg)
        if len(msg) > self._max_error_length:
            return msg[: self._max_error_length] + "... [log_truncated]"
        return msg

    @staticmethod
    def _iter_exception_chain(exc: BaseException):
        visited: set[int] = set()
        curr: Optional[BaseException] = exc
        while curr is not None and id(curr) not in visited:
            visited.add(id(curr))
            yield curr
            curr = curr.__cause__ or curr.__context__

    @staticmethod
    def _extract_raw_output(exc: Exception) -> Optional[str]:
        for curr in RegistryExceptionMapper._iter_exception_chain(exc):
            for attr in ("raw_output", "llm_output"):
                val = getattr(curr, attr, None)
                if val is not None:
                    return str(val)
        return None

    @staticmethod
    def _build_metadata(
        exc: Exception,
        matched: Optional[_MatchResult],
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        meta: Dict[str, Any] = {
            "exception_class": f"{type(exc).__module__}.{type(exc).__name__}",
        }
        # 1. 注入匹配规则或自描述协议的元数据与提示
        if matched is not None:
            meta.update(matched.metadata)
            if matched.user_friendly_hint:
                meta["user_friendly_hint"] = matched.user_friendly_hint

        # 2. 鸭子类型补充提取异常链上的通用诊断字段
        for curr in RegistryExceptionMapper._iter_exception_chain(exc):
            resp = getattr(curr, "response", None)
            if resp is not None and hasattr(resp, "status_code"):
                meta.setdefault("http_status_code", resp.status_code)

            for attr in ("finish_reason", "status_code", "is_rate_limit"):
                val = getattr(curr, attr, None)
                if val is not None:
                    meta.setdefault(attr, val)

        if extra_metadata:
            meta.update(extra_metadata)
        return meta
