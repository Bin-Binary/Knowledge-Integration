# /infra/adapters.py
from typing import Type, TypeVar, List, Dict
from pydantic import BaseModel
from langchain_core.language_models import BaseChatModel

T = TypeVar("T", bound=BaseModel)

class LangChainStructuredAdapter:
    """将任意 LangChain ChatModel 适配为 StructuredLLMProtocol"""
    def __init__(self, chat_model: BaseChatModel) -> None:
        self.chat_model = chat_model

    def generate_structured(self, messages: List[Dict[str, str]], response_schema: Type[T]) -> T:
        # LangChain 原生支持直接传入 Pydantic BaseModel 类
        structured_llm = self.chat_model.with_structured_output(response_schema)
        return structured_llm.invoke(messages)
