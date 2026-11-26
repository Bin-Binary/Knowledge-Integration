# /infra/middlewares/local_json_healer.py
import json
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from protocols import StreamingLLMProtocol, StructuredLLMProtocol
from infra.exceptions import StructuredOutputError

T = TypeVar("T", bound=BaseModel)
_MARKDOWN_JSON_RE = re.compile(r"```(?:json)?\s*([\s\(\S\)]*?)\s*```", re.IGNORECASE)


class LocalJsonHealerMiddleware(StructuredLLMProtocol, StreamingLLMProtocol):
    """切面 2：拦截 StructuredOutputError 并执行零延迟 L1 本地格式清洗（直接实现协议，零基类继承）"""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    @staticmethod
    def _try_heal(raw_text: Optional[str], response_schema: Type[T]) -> Optional[T]:
        if not raw_text or not isinstance(raw_text, str):
            return None

        text = raw_text.split("</think>", 1)[-1] if "</think>" in raw_text else raw_text
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip()).strip()

        candidates: List[str] = []
        md_match = _MARKDOWN_JSON_RE.search(text)
        if md_match:
            candidates.append(md_match.group(1).strip())

        end_idx = text.rfind("}")
        if end_idx != -1:
            start_idx = text.find("{")
            while start_idx != -1 and start_idx < end_idx:
                cand = text[start_idx : end_idx + 1].strip()
                if cand not in candidates:
                    candidates.append(cand)
                start_idx = text.find("{", start_idx + 1)

        for cand in candidates:
            try:
                return response_schema.model_validate(json.loads(cand))
            except Exception:
                continue
        return None

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_schema: Type[T],
        **kwargs: Any,
    ) -> T:
        try:
            return await self._inner.generate_structured(messages, response_schema, **kwargs)
        except StructuredOutputError as err:
            healed = self._try_heal(err.raw_output, response_schema)
            if healed is not None:
                return healed
            raise

    async def astream_text(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        async for chunk in self._inner.astream_text(messages, **kwargs):
            yield chunk
