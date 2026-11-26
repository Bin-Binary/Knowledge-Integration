# protocols/llm.py
from typing import Protocol, runtime_checkable, AsyncIterator, Type, TypeVar, List, Dict, Any
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

@runtime_checkable
class StructuredLLMProtocol(Protocol):
    """结构化输出大模型协议：屏蔽 OpenAI / LangChain / vLLM 底层调用差异"""

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_schema: Type[T],
        **kwargs: Any,
    ) -> T:
        """异步生成符合 Pydantic 模型约束的结构化输出。

        Args:
            messages: 标准对话消息列表，如 [{"role": "user", "content": "..."}]
            response_schema: 目标输出的 Pydantic BaseModel 类
            **kwargs: 可选推理参数透传（如 temperature, max_tokens, timeout 等）
        """
        ...

@runtime_checkable
class StreamingLLMProtocol(Protocol):
    """流式自然语言输出协议：专用于面向用户的最终答复生成"""

    def astream_text(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        ...        
