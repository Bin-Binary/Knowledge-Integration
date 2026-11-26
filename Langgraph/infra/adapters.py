# /infra/adapters.py
from typing import Any, AsyncIterator, Dict, List, Literal, Optional, Type, TypeVar
from pydantic import BaseModel
from langchain_core.language_models import BaseChatModel

from protocols import StreamingLLMProtocol, StructuredLLMProtocol
from infra.exceptions import StructuredOutputError  # 统一指向核心自描述异常模块
from infra.observability import log_execution

T = TypeVar("T", bound=BaseModel)


class LangChainStructuredAdapter(StructuredLLMProtocol):
    """纯薄结构化输出适配器：仅负责协议转发与基础解析判空"""

    def __init__(
        self,
        chat_model: BaseChatModel,
        method: Optional[Literal["function_calling", "json_mode", "json_schema"]] = None,
    ) -> None:
        self.chat_model = chat_model
        self.method = method

    def _ensure_json_keyword(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if self.method != "json_mode":
            return messages

        has_json_word = any("json" in msg.get("content", "").lower() for msg in messages)
        if has_json_word:
            return messages

        safe_messages = [dict(m) for m in messages]
        json_hint = "\n请严格以合法的 JSON 格式输出结果。"
        if safe_messages and safe_messages[0].get("role") == "system":
            safe_messages[0]["content"] += json_hint
        else:
            safe_messages.insert(0, {"role": "system", "content": json_hint.strip()})
        return safe_messages

    @staticmethod
    def _extract_raw_info(raw_msg: Any) -> tuple[Optional[str], Dict[str, Any]]:
        """从 LangChain AIMessage 提取原始文本与诊断元数据（如 finish_reason）"""
        if raw_msg is None:
            return None, {}
        raw_str = raw_msg.content if getattr(raw_msg, "content", None) is not None else str(raw_msg)
        meta: Dict[str, Any] = {}
        resp_meta = getattr(raw_msg, "response_metadata", None)
        if isinstance(resp_meta, dict) and "finish_reason" in resp_meta:
            meta["finish_reason"] = resp_meta["finish_reason"]
        return str(raw_str), meta

    @log_execution("LLM.generate_structured")
    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_schema: Type[T],
        **kwargs: Any,
    ) -> T:
        build_kwargs: Dict[str, Any] = {"include_raw": True}
        if self.method is not None:
            build_kwargs["method"] = self.method

        structured_llm = self.chat_model.with_structured_output(
            response_schema, **build_kwargs
        )
        prepared_messages = self._ensure_json_keyword(messages)
        result = await structured_llm.ainvoke(prepared_messages, **kwargs)

        raw_msg = result.get("raw")
        raw_str, diag_meta = self._extract_raw_info(raw_msg)

        if result.get("parsing_error") is not None:
            err = result["parsing_error"]
            raise StructuredOutputError(
                message=f"LangChain parser failed for {response_schema.__name__}: {err}",
                raw_output=raw_str,
                schema_name=response_schema.__name__,
                metadata=diag_meta,
            ) from err

        parsed = result.get("parsed")
        if parsed is None:
            raise StructuredOutputError(
                message=f"LLM returned empty parsed result for {response_schema.__name__}.",
                raw_output=raw_str,
                schema_name=response_schema.__name__,
                metadata=diag_meta,
            )

        return parsed


class HybridLangChainAdapter(LangChainStructuredAdapter, StreamingLLMProtocol):
    """同时具备强类型结构化输出与纯文本流式能力的复合适配器"""

    async def astream_text(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        async for chunk in self.chat_model.astream(messages, **kwargs):
            if chunk.content:
                yield str(chunk.content)
