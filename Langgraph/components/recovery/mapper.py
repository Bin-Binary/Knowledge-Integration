# /recovery/mapper.py
"""异常标准化,负责 Exception -> FailureContext"""
import json
import asyncio
from typing import Any, Dict, Optional
import httpx
from pydantic import ValidationError
from langchain_core.exceptions import OutputParserException

from schemas.recovery import FailureCategory, FailureContext

class ExceptionMapper:
    """异常标准化映射器：负责将运行时 Exception 转换为标准的 FailureContext"""

    @classmethod
    def to_failure_context(
        cls,
        exc: Exception,
        *,
        trace_id: str,
        failed_stage: str,
        target_schema_name: Optional[str] = None,
        user_query: Optional[str] = None,
        retry_count: int = 0,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> FailureContext:
        """
        核心映射入口：根据异常类型归一分类，提取原始输出与诊断元数据。
        """
        category = cls._classify_exception(exc)
        raw_output = cls._extract_raw_output(exc)
        error_message = cls._format_error_message(exc, category)
        metadata = cls._build_metadata(exc, extra_metadata)

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

    @staticmethod
    def _classify_exception(exc: Exception) -> FailureCategory:
        """将具体异常映射到标准 FailureCategory"""
        # 1. 模型调用超时（涵盖 httpx、标准库超时及常见 SDK 超时命名）
        if isinstance(exc, (httpx.TimeoutException, asyncio.TimeoutError, TimeoutError)):
            return FailureCategory.LLM_CALL_TIMEOUT_ERROR
        if "timeout" in type(exc).__name__.lower():
            return FailureCategory.LLM_CALL_TIMEOUT_ERROR

        # 2. Pydantic 业务字段校验不通过（如枚举值越界、必填字段缺失、类型错误）
        if isinstance(exc, ValidationError):
            return FailureCategory.VALIDATION_ERROR

        # 3. 输出格式污染（如夹带 Markdown 代码块、思维链文本导致 JSON 解析失败）
        if isinstance(exc, (OutputParserException, json.JSONDecodeError)):
            return FailureCategory.OUTPUT_FORMAT_ERROR

        # 4. 兜底为未知运行时异常
        return FailureCategory.UNKNOWN_ERROR

    @staticmethod
    def _extract_raw_output(exc: Exception) -> Optional[str]:
        """
        从异常对象（及其异常链 __cause__）中提取大模型的原始响应文本
        """
        # 依次检查当前异常和底层原始异常
        candidates = [exc]
        if exc.__cause__ and isinstance(exc.__cause__, Exception):
            candidates.append(exc.__cause__)

        for err in candidates:
            # 优先读取在适配器层动态挂载或自定义异常中携带的 raw_output
            raw = getattr(err, "raw_output", None)
            if raw is not None:
                return str(raw)

            # 其次读取 LangChain OutputParserException 原生自带的 llm_output
            llm_out = getattr(err, "llm_output", None)
            if llm_out is not None:
                return str(llm_out)

        return None

    @staticmethod
    def _format_error_message(exc: Exception, category: FailureCategory) -> str:
        """生成清晰、适合日志记录与 Prompt 反馈的错误摘要（受全局脱敏开关控制）"""
        if category == FailureCategory.VALIDATION_ERROR and isinstance(exc, ValidationError):
            # 将 Pydantic 冗长的堆栈精简为具体的字段报错列表，方便喂给修复模型
            details = [
                f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                for err in exc.errors()
            ]
            return f"Schema 字段校验失败 ({len(details)}处): " + "; ".join(details)

        if category == FailureCategory.LLM_CALL_TIMEOUT_ERROR:
            return f"LLM 服务调用超时 ({type(exc).__name__}): {exc}"

        return f"[{type(exc).__name__}] {str(exc)}"

    @staticmethod
    def _build_metadata(
        exc: Exception, extra_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """收集异常类型、HTTP状态码等诊断信息存入 metadata"""
        meta: Dict[str, Any] = {
            "exception_class": f"{type(exc).__module__}.{type(exc).__name__}",
        }
        # 如果是 HTTP 错误，顺便记录状态码（如 429 限流 / 502 网关错误）
        if isinstance(exc, httpx.HTTPStatusError):
            meta["http_status_code"] = exc.response.status_code

        if extra_metadata:
            meta.update(extra_metadata)
        return meta
