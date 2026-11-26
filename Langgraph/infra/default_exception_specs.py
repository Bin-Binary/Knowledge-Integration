# /infra/default_exception_specs.py
import asyncio
import json
from typing import Any, Dict, Tuple

import httpx
from langchain_core.exceptions import OutputParserException
from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    LengthFinishReasonError,
    RateLimitError,
)
from pydantic import ValidationError

from infra.registry_exception_mapper import ExceptionMappingSpec


def _format_pydantic_error(exc: BaseException) -> str:
    assert isinstance(exc, ValidationError)
    details = [f"{'.'.join(str(x) for x in item['loc'])}: {item['msg']}" for item in exc.errors()]
    return f"Schema 字段校验失败 ({len(details)}处): " + "; ".join(details)


def _extract_length_error_meta(exc: BaseException) -> Dict[str, Any]:
    assert isinstance(exc, LengthFinishReasonError)
    raw = (
        exc.completion.choices[0].message.content
        if getattr(exc, "completion", None) and exc.completion.choices
        else None
    )
    return {"finish_reason": "length", "raw_output": raw}


# 声明式异常映射配置表（按匹配优先级排列）
DEFAULT_EXCEPTION_SPECS: Tuple[ExceptionMappingSpec, ...] = (
    # 1. 模型限流与服务不可用
    ExceptionMappingSpec(
        exc_types=(RateLimitError,),
        error_code="model.rate_limited",
        message_template="大模型服务触发并发限流 (429): {exc}",
        user_friendly_hint="当前模型服务请求过于频繁（触发限流），请稍等几秒后重试。",
        static_metadata={"status_code": 429, "is_rate_limit": True},
    ),
    ExceptionMappingSpec(
        exc_types=(APITimeoutError, httpx.TimeoutException, asyncio.TimeoutError, TimeoutError),
        error_code="model.unavailable",
        message_template="网络或模型服务请求超时 ({exc_name}): {exc}",
        user_friendly_hint="模型服务响应超时，请稍后重试。",
        static_metadata={"status_code": 504},
    ),
    ExceptionMappingSpec(
        exc_types=(InternalServerError, APIConnectionError, httpx.ConnectError),
        error_code="model.unavailable",
        message_template="大模型网关或上游连接不可用 ({exc_name}): {exc}",
        user_friendly_hint="模型服务暂时不可用，请稍后重试。",
        metadata_extractor=lambda e: {"status_code": getattr(e, "status_code", 503)},
    ),
    # 2. 结构化输出与校验异常
    ExceptionMappingSpec(
        exc_types=(LengthFinishReasonError,),
        error_code="output.truncated",
        message_template="LLM 输出达到 max_tokens 上限被截断: {exc}",
        metadata_extractor=_extract_length_error_meta,
    ),
    ExceptionMappingSpec(
        exc_types=(ValidationError,),
        error_code="output.validation_error",
        formatter=_format_pydantic_error,
    ),
    ExceptionMappingSpec(
        exc_types=(OutputParserException, json.JSONDecodeError),
        error_code="output.format_error",
        message_template="输出格式解析失败 ({exc_name}): {exc}",
    ),
)
