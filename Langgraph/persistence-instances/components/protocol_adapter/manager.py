# components/protocol_adapter/manager.py
from typing import List, Dict, Any, Optional
from core.interfaces import LLMProtocolAdapter
from components.protocol_adapter.adapters import OpenAIProtocolAdapter, AnthropicProtocolAdapter


class ProtocolAdapterManager:
    """协议适配器自动路由管理器：支持动态注册新模型协议（如 Gemini）"""

    def __init__(self, adapters: Optional[List[LLMProtocolAdapter]] = None) -> None:
        self._adapters: List[LLMProtocolAdapter] = adapters or [
            AnthropicProtocolAdapter(),
            OpenAIProtocolAdapter(),  # 兜底匹配标准 OpenAI 格式
        ]

    def register(self, adapter: LLMProtocolAdapter) -> None:
        """支持外部扩展注册自定义模型协议适配器"""
        self._adapters.insert(0, adapter)

    def resolve(self, payload: Dict[str, Any]) -> LLMProtocolAdapter:
        """根据请求体特征自动匹配对应的协议适配器"""
        for adapter in self._adapters:
            if adapter.can_handle(payload):
                return adapter
        raise ValueError("未找到匹配当前请求体格式的 LLMProtocolAdapter 适配器")
