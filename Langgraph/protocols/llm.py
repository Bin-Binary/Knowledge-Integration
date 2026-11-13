from typing import Protocol, runtime_checkable, Type, TypeVar, List, Dict
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

@runtime_checkable
class StructuredLLMProtocol(Protocol):
    """结构化输出大模型协议：屏蔽 OpenAI / LangChain / vLLM 底层调用差异"""
    def generate_structured(
        self, 
        messages: List[Dict[str, str]], 
        response_schema: Type[T]
    ) -> T:
        ...
