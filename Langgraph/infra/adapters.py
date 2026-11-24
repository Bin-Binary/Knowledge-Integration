# infra/adapters.py
from typing import Type, TypeVar, List, Dict, Any, Optional, Literal
from pydantic import BaseModel, ValidationError

from openai import LengthFinishReasonError
from langchain_core.language_models import BaseChatModel

from protocols.llm import StructuredLLMProtocol
from infra.exceptions import StructuredOutputError
from infra.observability import log_execution

T = TypeVar("T", bound=BaseModel)


class LangChainStructuredAdapter(StructuredLLMProtocol):
    """将任意 LangChain ChatModel 适配为 StructuredLLMProtocol"""

    def __init__(
        self,
        chat_model: BaseChatModel,
        method: Optional[Literal["function_calling", "json_mode", "json_schema"]] = None,
    ) -> None:
        self.chat_model = chat_model
        # 允许实例化时按模型能力配置解析策略，默认 None 交由 LangChain 自动选择最优策略
        self.method = method

    def _ensure_json_keyword(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """当使用 json_mode 时，确保 messages 中包含 'json' 关键字，防止网关报 400 错误"""
        if self.method != "json_mode":
            return messages

        has_json_word = any("json" in msg.get("content", "").lower() for msg in messages)
        if has_json_word:
            return messages

        # 复制列表避免污染上游传入的原始数据结构
        safe_messages = [dict(m) for m in messages]
        json_hint = "\n请严格以合法的 JSON 格式输出结果。"
        if safe_messages and safe_messages[0].get("role") == "system":
            safe_messages[0]["content"] += json_hint
        else:
            safe_messages.insert(0, {"role": "system", "content": json_hint.strip()})
        return safe_messages
    @log_execution("LLM.generate_structured")
    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_schema: Type[T],
        **kwargs: Any,
    ) -> T:
        # 1. 按配置构建结构化输出 runnable（仅构建一次）
        build_kwargs: Dict[str, Any] = {"include_raw": True}
        if self.method is not None:
            build_kwargs["method"] = self.method

        structured_llm = self.chat_model.with_structured_output(
            response_schema, **build_kwargs
        )
        prepared_messages = self._ensure_json_keyword(messages)

        # 2. 异步调用并拦截异常1：SDK 底层在反序列化阶段直接抛出的 ValidationError
        try:
            result = await structured_llm.ainvoke(prepared_messages, **kwargs)
        except ValidationError as sdk_val_err:
            errors = sdk_val_err.errors()
            raw_str = (
                errors[0]["input"]
                if errors and isinstance(errors[0].get("input"), str)
                else None
            )
            raise StructuredOutputError(
                message=f"SDK structured output validation failed for {response_schema.__name__}: {sdk_val_err}",
                raw_output=raw_str,
                schema_name=response_schema.__name__,
            ) from sdk_val_err
        # 拦截完成整个输出之前，就已经达到了max_tokens，导致返回内容被截断引发的异常    
        except LengthFinishReasonError as len_err:
            raw_content = None
            if getattr(len_err, "completion", None) and len_err.completion.choices:
                raw_content = len_err.completion.choices[0].message.content

            err = StructuredOutputError(
                message=f"LLM output truncated (max_tokens reached) for {response_schema.__name__}",
                raw_output=raw_content,
                schema_name=response_schema.__name__,
            )
            err.finish_reason = "length"  # 供 Mapper 提取存入 metadata
            raise err from len_err
        # 3. 拦截异常2：LangChain 内部 Parser 捕获并吞掉的解析/校验异常
        if result.get("parsing_error") is not None:
            err = result["parsing_error"]
            raw_msg = result.get("raw")
            raw_str = (
                raw_msg.content
                if getattr(raw_msg, "content", None)
                else str(raw_msg)
            )
            raise StructuredOutputError(
                message=f"LangChain parser failed for {response_schema.__name__}: {err}",
                raw_output=raw_str,
                schema_name=response_schema.__name__,
            ) from err

        # 4. 校验 parsed 兜底并返回强类型实例
        parsed = result.get("parsed")
        if parsed is None:
            raise StructuredOutputError(
                message=f"LLM returned empty parsed result for {response_schema.__name__}.",
                raw_output=str(result.get("raw")),
                schema_name=response_schema.__name__,
            )

        return parsed
