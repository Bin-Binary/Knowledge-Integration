# /infra/adapters.py
from typing import Type, TypeVar, List, Dict
from pydantic import BaseModel, ValidationError
from langchain_core.language_models import BaseChatModel

from protocols.llm import StructuredLLMProtocol
T = TypeVar("T", bound=BaseModel)

class LangChainStructuredAdapter(StructuredLLMProtocol):
    """将任意 LangChain ChatModel 适配为 StructuredLLMProtocol"""
    def __init__(self, chat_model: BaseChatModel) -> None:
        self.chat_model = chat_model

    def generate_structured(self, messages: List[Dict[str, str]], response_schema: Type[T]) -> T:
        """LangChain 原生支持直接传入 Pydantic BaseModel 类
            structured_llm = llm.with_structured_output(AnswerWithJustification, include_raw=True)

            structured_llm.invoke("What weighs more a pound of bricks or a pound of feathers")
            # -> {
            #     'raw': AIMessage(content='', additional_kwargs={'tool_calls': [{'id': 'call_Ao02pnFYXD6GN1yzc0uXPsvF', 'function': {'arguments': '{"answer":"They weigh the same.","justification":"Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume or density of the objects may differ."}', 'name': 'AnswerWithJustification'}, 'type': 'function'}]}),
            #     'parsed': AnswerWithJustification(answer='They weigh the same.', justification='Both a pound of bricks and a pound of feathers weigh one pound. The weight is the same, but the volume or density of the objects may differ.'),
            #     'parsing_error': None
            # }

        """
        structured_llm = self.chat_model.with_structured_output(response_schema, include_raw=True)
        """对于本地开源推理模型，建议显式指定 method="json_mode" 或捕获 SDK 原生异常
        但是！！！-> OpenAI 规范和绝大多数推理引擎规定：当使用 json_mode 时，传入的 messages（通常是 System Prompt）中必须明确包含 "JSON"（或 "json"）这个单词，
        否则部分网关会直接返回 400 Bad Request: 'messages' must contain the word 'json' in some form。
        确保你的 `System Prompt` 里有类似 "请以 JSON 格式输出..." 的字样
        """
        structured_llm = self.chat_model.with_structured_output(response_schema, include_raw=True, method="json_mode")
        
        try:
            """异常1. 拦截 SDK 提前报错 
            openai SDK 在 parse() 阶段直接抛出的 ValidationError，原始字符串就在 errors()[0]["input"] 中
            使用 langchain_openai 且默认走 OpenAI 原生 json_schema 响应格式时，底层的 openai Python SDK 会在反序列化阶段直接调用 Pydantic 校验并抛出 ValidationError，
            导致 invoke() 还没返回字典就直接中断
            """
            result = structured_llm.invoke(messages)
        except ValidationError as sdk_val_err:
            errors = sdk_val_err.errors()
            if errors and isinstance(errors[0].get("input"), str):
                sdk_val_err.raw_output = errors[0]["input"]
            raise sdk_val_err        
        """异常2.拦截 LangChain 内部解析器吞掉的错误
        切换到支持Tool Calling（函数调用）的模型（如 标准 GPT-4o 走 function_calling模式
        或在 with_structured_output 中指定 method="function_calling" / method="json_mode"）时，
        LangChain 内部的 PydanticToolsParser 或 JsonOutputParser 会捕获校验异常，把错误塞进 result["parsing_error"] 并正常返回字典
        """
        # 如果pydantic解析异常时保存AI返回的原始输出后抛出，交给上游处理
        if result.get('parsing_error') is not None:
            err = result["parsing_error"]
            raw_msg = result.get('raw')
            # 提取原始文本，动态挂载到异常对象上
            err.raw_output = raw_msg.content if getattr(raw_msg, "content", None) else str(raw_msg)
            raise err
        # 正常情况解包返回 parsed，保持返回类型依然是response_schema 实例
        return result["parsed"]            
