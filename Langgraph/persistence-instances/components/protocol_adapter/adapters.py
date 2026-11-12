# components/protocol_adapter/adapters.py
import copy
from typing import List, Dict, Set, Any, Tuple
from core.interfaces import LLMProtocolAdapter


class OpenAIProtocolAdapter(LLMProtocolAdapter):
    """兼容 OpenAI / LiteLLM / OpenCode / GLM 等标准 ChatCompletions 格式"""

    def can_handle(self, payload: Dict[str, Any]) -> bool:
        if "messages" in payload:
            tools = payload.get("tools", [])
            if not tools:
                return True
            return any(t.get("type") == "function" and "function" in t for t in tools)
        return False

    def extract_context(self, payload: Dict[str, Any]) -> Tuple[str, Set[str]]:
        messages = payload.get("messages", [])
        current_context = ""

        # 提取最新一条 user 消息
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    current_context = content
                elif isinstance(content, list):
                    current_context = "\n".join(
                        b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
                    )
                break

        # 提取历史 tool_calls
        active_history: Set[str] = set()
        for msg in messages:
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls", []):
                    fn_name = tc.get("function", {}).get("name")
                    if fn_name:
                        active_history.add(fn_name)

        return current_context, active_history

    def parse_tools(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for rt in payload.get("tools", []):
            if rt.get("type") == "function" and isinstance(rt.get("function"), dict):
                fn = rt["function"]
                normalized.append({
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
                    "raw_tool": rt,
                })
        return normalized

    def inject_pruned_tools(
        self,
        payload: Dict[str, Any],
        pruned_schemas: List[Dict[str, Any]],
        registry_lookup: Dict[str, Any]
    ) -> Dict[str, Any]:
        new_payload = copy.copy(payload)
        new_payload["tools"] = [
            registry_lookup[item["name"]]["raw_tool"]
            for item in pruned_schemas
            if item["name"] in registry_lookup
        ]
        return new_payload


class AnthropicProtocolAdapter(LLMProtocolAdapter):
    """兼容 Anthropic Claude Messages API 格式 (input_schema 与 tool_use 块)"""

    def can_handle(self, payload: Dict[str, Any]) -> bool:
        tools = payload.get("tools", [])
        return any("input_schema" in t and "type" not in t for t in tools)

    def extract_context(self, payload: Dict[str, Any]) -> Tuple[str, Set[str]]:
        messages = payload.get("messages", [])
        current_context = ""

        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    current_context = content
                elif isinstance(content, list):
                    current_context = "\n".join(
                        b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
                    )
                break

        active_history: Set[str] = set()
        for msg in messages:
            content = msg.get("content")
            if msg.get("role") == "assistant" and isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use" and "name" in block:
                        active_history.add(block["name"])

        return current_context, active_history

    def parse_tools(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "name": rt["name"],
                "description": rt.get("description", ""),
                "input_schema": rt.get("input_schema", {"type": "object", "properties": {}}),
                "raw_tool": rt,
            }
            for rt in payload.get("tools", [])
            if "name" in rt
        ]

    def inject_pruned_tools(
        self,
        payload: Dict[str, Any],
        pruned_schemas: List[Dict[str, Any]],
        registry_lookup: Dict[str, Any]
    ) -> Dict[str, Any]:
        new_payload = copy.copy(payload)
        new_payload["tools"] = [
            registry_lookup[item["name"]]["raw_tool"]
            for item in pruned_schemas
            if item["name"] in registry_lookup
        ]
        return new_payload
