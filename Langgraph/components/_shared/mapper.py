# /components/_shared/mapper.py
"""异常标准化实现：负责 Exception -> FailureContext"""
import asyncio
import json
import re
from typing import Any, Dict, Optional, Tuple, Type

import httpx
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

from schemas import FailureCategory, FailureContext
from protocols import ExceptionMapperProtocol

# 基础敏感词脱敏正则（覆盖常见的 API Key、Bearer Token）
_SENSITIVE_PATTERN = re.compile(
    r"(sk-[a-zA-Z0-9]{16,}|Bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*)",
    re.IGNORECASE,
)


class DefaultExceptionMapper(ExceptionMapperProtocol):
    """
    异常标准化映射器默认实现：
    结构化实现 ExceptionMapperProtocol（通过 __call__），支持依赖注入与自定义规则扩展。
    """

    def __init__(
        self,
        *,
        max_error_length: int = 1000,
        enable_sanitization: bool = True,
        custom_rules: Optional[Tuple[Tuple[Type[Exception], FailureCategory], ...]] = None,
    ) -> None:
        self._max_error_length = max_error_length
        self._enable_sanitization = enable_sanitization
        self._custom_rules = custom_rules or ()

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
        """满足 ExceptionMapperProtocol 契约的核心调用入口"""
        category = self._classify_exception(exc)
        raw_output = self._extract_raw_output(exc)
        error_message = self._format_error_message(exc, category)
        metadata = self._build_metadata(exc, extra_metadata)

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

    def _classify_exception(self, exc: Exception) -> FailureCategory:
        """遍历完整异常链，将具体异常映射到标准 FailureCategory"""
        for curr in self._iter_exception_chain(exc):
            # 0. 优先匹配外部注入的自定义业务异常规则（符合 OCP 开闭原则）
            for exc_type, category in self._custom_rules:
                if isinstance(curr, exc_type):
                    return category

            # 1. 模型调用超时（涵盖 httpx、标准库超时及常见 SDK 超时命名）
            if isinstance(curr, (httpx.TimeoutException, asyncio.TimeoutError, TimeoutError)):
                return FailureCategory.LLM_CALL_TIMEOUT_ERROR
            if "timeout" in type(curr).__name__.lower():
                return FailureCategory.LLM_CALL_TIMEOUT_ERROR

            # 2. Pydantic 业务字段校验不通过
            if isinstance(curr, ValidationError):
                return FailureCategory.VALIDATION_ERROR

            # 3. 输出格式污染（JSON 解析失败或 LangChain 解析异常）
            if isinstance(curr, (OutputParserException, json.JSONDecodeError)):
                return FailureCategory.OUTPUT_FORMAT_ERROR

        # 4. 兜底为未知运行时异常
        return FailureCategory.UNKNOWN_ERROR

    def _format_error_message(self, exc: Exception, category: FailureCategory) -> str:
        """生成清晰、脱敏且长度受控的错误摘要"""
        val_err = next(
            (e for e in self._iter_exception_chain(exc) if isinstance(e, ValidationError)),
            None,
        )
        if category == FailureCategory.VALIDATION_ERROR and val_err is not None:
            details = [
                f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                for err in val_err.errors()
            ]
            msg = f"Schema 字段校验失败 ({len(details)}处): " + "; ".join(details)
        elif category == FailureCategory.LLM_CALL_TIMEOUT_ERROR:
            msg = f"LLM 服务调用超时 ({type(exc).__name__}): {exc}"
        else:
            msg = f"[{type(exc).__name__}] {str(exc)}"

        if self._enable_sanitization:
            msg = _SENSITIVE_PATTERN.sub("[REDACTED]", msg)

        if len(msg) > self._max_error_length:
            msg = msg[: self._max_error_length] + "... [log_truncated]"

        return msg

    @staticmethod
    def _iter_exception_chain(exc: BaseException):
        """安全遍历完整异常链（防止循环引用）"""
        visited: set[int] = set()
        curr: Optional[BaseException] = exc
        while curr is not None and id(curr) not in visited:
            visited.add(id(curr))
            yield curr
            curr = curr.__cause__ or curr.__context__

    @staticmethod
    def _extract_raw_output(exc: Exception) -> Optional[str]:
        """遍历完整异常链提取大模型原始响应文本"""
        for curr in DefaultExceptionMapper._iter_exception_chain(exc):
            for attr in ("raw_output", "llm_output"):
                val = getattr(curr, attr, None)
                if val is not None:
                    return str(val)
        return None

    @staticmethod
    def _build_metadata(
        exc: Exception, extra_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """收集异常类型、HTTP状态码、Token截断标记等诊断信息存入 metadata"""
        meta: Dict[str, Any] = {
            "exception_class": f"{type(exc).__module__}.{type(exc).__name__}",
        }
        for curr in DefaultExceptionMapper._iter_exception_chain(exc):
            if isinstance(curr, httpx.HTTPStatusError):
                meta["http_status_code"] = curr.response.status_code
            finish_reason = getattr(curr, "finish_reason", None)
            if finish_reason is not None:
                meta["finish_reason"] = finish_reason

        if extra_metadata:
            meta.update(extra_metadata)
        return meta

