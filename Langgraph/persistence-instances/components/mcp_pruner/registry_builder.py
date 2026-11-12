# components/mcp_pruner/registry_builder.py
import json
import logging
import re
from typing import List, Dict, Any, Optional, Callable
from core.interfaces import LLMProtocolAdapter

logger = logging.getLogger(__name__)


class MCPRegistryBuilder:
    """
    无状态纯内存 MCP 工具注册表构建器（已与具体模型协议及磁盘持久化解耦）。

    职责：
    1. 依赖抽象协议 LLMProtocolAdapter 将不同模型的请求体转化为内部标准中间结构。
    2. 构造富语义文本（semantic_text），供下游向量裁剪策略按需执行批量编码与磁盘持久化。
    3. 自动估算或调用外部 Tokenizer 精确计算工具注入上下文时的 Token 负载 (token_size)。
    4. 自动提取启发式关键词，为规则裁剪策略提供开箱即用的支持。
    """

    def __init__(self, token_counter: Optional[Callable[[str], int]] = None) -> None:
        """
        参数：
            token_counter: 可选的精确 Token 计算函数（如 tiktoken 的 encode 长度函数）。
                           若为 None，则使用内置的字符长度启发式估算。
        """
        self._token_counter = token_counter

    @staticmethod
    def _auto_extract_keywords(tool_name: str, description: str) -> List[str]:
        """
        自动为未显式配置 keywords 的工具提取基础启发式关键词，
        确保接入任何第三方 MCP Server 时规则裁剪器 (RuleHeuristicMCPPruner) 也能直接生效。
        """
        tokens = re.split(r'[_\-\s]+', tool_name)
        stop_words = {"mcp", "tool", "get", "set", "run", "do", "the", "a", "an", "to", "for", "of", "in", "on"}
        keywords = [t.lower() for t in tokens if len(t) >= 3 and t.lower() not in stop_words]

        # 提取描述前 50 字中的中文核心短语作为补充
        zh_phrases = re.findall(r'[\u4e00-\u9fff]{2,4}', description[:50])
        keywords.extend(zh_phrases[:3])
        return list(dict.fromkeys(keywords))

    @staticmethod
    def _build_rich_semantic_text(tool: Dict[str, Any]) -> str:
        """
        构造融合工具名、核心用途描述与一级参数名的富语义文本。
        截取前 300 字符描述，防止长篇说明书（如 bash 工具的数千字语法说明）稀释向量方向。
        """
        name_readable = tool["name"].replace("_", " ").replace("-", " ")
        desc_clean = tool["description"][:300].strip()

        props = tool.get("input_schema", {}).get("properties", {})
        param_names = ", ".join(props.keys()) if isinstance(props, dict) else ""

        if param_names:
            return f"Tool: {name_readable}. Purpose: {desc_clean}. Parameters: {param_names}."
        return f"Tool: {name_readable}. Purpose: {desc_clean}."

    def _estimate_token_size(self, raw_tool: Any) -> int:
        """计算原始工具定义注入请求体时的实际 Token 负载"""
        serialized = json.dumps(raw_tool, ensure_ascii=False) if not isinstance(raw_tool, str) else raw_tool
        if self._token_counter is not None:
            return self._token_counter(serialized)
        return max(50, len(serialized) // 3)

    def build_from_payload(
        self,
        payload: Dict[str, Any],
        adapter: LLMProtocolAdapter
    ) -> List[Dict[str, Any]]:
        """
        [协议解耦入口]
        通过外部传入的 LLMProtocolAdapter 解析原始请求体，并在内存中即时构建标准 mcp_registry。
        """
        normalized_tools = adapter.parse_tools(payload)
        return self.build(normalized_tools)

    def build(self, normalized_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        接收符合标准中间结构的工具列表，加工为下游裁剪器所需的完整 mcp_registry。

        参数：
            normalized_tools: 由 LLMProtocolAdapter.parse_tools() 输出的标准中间列表，
                              每项必须包含 {"name", "description", "input_schema", "raw_tool"}。

        返回：
            List[Dict[str, Any]]: 包含富语义文本、Token 估算值与控制元数据的标准化内存列表。
        """
        if not normalized_tools:
            return []

        standardized_registry: List[Dict[str, Any]] = []

        for item in normalized_tools:
            name = item["name"]
            raw_tool = item.get("raw_tool", {})
            # 兼容提取可能挂载在原始定义或外层的扩展控制字段
            extra_meta = raw_tool.get("function", raw_tool) if isinstance(raw_tool, dict) else {}

            keywords = extra_meta.get("keywords") or self._auto_extract_keywords(name, item["description"])

            entry: Dict[str, Any] = {
                "name": name,
                "description": item["description"],
                "input_schema": item["input_schema"],
                "raw_tool": raw_tool,
                "semantic_text": self._build_rich_semantic_text(item),
                "keywords": keywords,
                "dependencies": set(extra_meta.get("dependencies", [])),
                "is_enabled": extra_meta.get("is_enabled", True),
                "compliance_flag": extra_meta.get("compliance_flag", True),
                "token_size": extra_meta.get("token_size") or self._estimate_token_size(raw_tool),
            }
            # 若上游已预先注入了现成的向量，则予以透传保留
            if "embedding" in item:
                entry["embedding"] = item["embedding"]

            standardized_registry.append(entry)

        return standardized_registry
