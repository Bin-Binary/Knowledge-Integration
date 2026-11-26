# /infra/middlewares/model_failover.py
import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Type, TypeVar

import httpx
from langchain_core.exceptions import OutputParserException
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    LengthFinishReasonError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError

from infra.exceptions import ModelServiceUnavailableError, StructuredOutputError
from protocols import StreamingLLMProtocol, StructuredLLMProtocol

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

# 默认触发异构灾备切换的瞬态/格式异常白名单
DEFAULT_FAILOVER_EXCEPTIONS: Tuple[Type[BaseException], ...] = (
    RateLimitError,
    APITimeoutError,
    InternalServerError,
    APIConnectionError,
    APIStatusError,
    LengthFinishReasonError,
    httpx.TimeoutException,
    httpx.ConnectError,
    asyncio.TimeoutError,
    TimeoutError,
    StructuredOutputError,
    ModelServiceUnavailableError,
    OutputParserException,
    ValidationError,
    json.JSONDecodeError,
)


class ModelFailoverMiddleware(StructuredLLMProtocol, StreamingLLMProtocol):
    """
    大模型网关高可用透明灾备切面（Middleware）：
    - 包裹在主模型适配器外层，对上层业务组件与 LangGraph 状态机完全透明；
    - 当主模型（如 GLM-V5.1）遇到限流(429)/超时/网关错误/解析失败时，
      立即在单次调用内部无缝切换至备用模型（如 DeepSeek-v4-Flash-SZ）重跑；
    - 仅当主模型与备用模型双双失败时，才将异常向上抛出，交由状态机 recovery_node 执行静态降级。
    """

    def __init__(
        self,
        primary: Any,
        backup: Optional[Any] = None,
        failover_exceptions: Tuple[Type[BaseException], ...] = DEFAULT_FAILOVER_EXCEPTIONS,
    ) -> None:
        self._primary = primary
        self._backup = backup
        self._failover_exceptions = failover_exceptions

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_schema: Type[T],
        **kwargs: Any,
    ) -> T:
        try:
            return await self._primary.generate_structured(messages, response_schema, **kwargs)
        except self._failover_exceptions as primary_err:
            if self._backup is None:
                raise

            logger.warning(
                "[ModelFailoverMiddleware] Primary LLM failed for [%s] (%s: %s), failing over to backup LLM...",
                response_schema.__name__,
                type(primary_err).__name__,
                primary_err,
            )
            try:
                return await self._backup.generate_structured(messages, response_schema, **kwargs)
            except Exception as backup_err:
                logger.error(
                    "[ModelFailoverMiddleware] Backup LLM also failed for [%s] (%s: %s).",
                    response_schema.__name__,
                    type(backup_err).__name__,
                    backup_err,
                )
                # 保留主异常上下文并抛出备用异常，交由下游 Mapper 与降级插件收尾
                raise backup_err from primary_err

    async def astream_text(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        has_yielded = False
        try:
            async for chunk in self._primary.astream_text(messages, **kwargs):
                has_yielded = True
                yield chunk
        except self._failover_exceptions as primary_err:
            # 仅在尚未向前端吐出任何 Token 时允许无缝切换，避免半截回答拼接乱码
            if self._backup is None or has_yielded:
                raise

            logger.warning(
                "[ModelFailoverMiddleware] Primary stream failed before first token (%s), failing over to backup LLM...",
                type(primary_err).__name__,
            )
            async for chunk in self._backup.astream_text(messages, **kwargs):
                yield chunk
