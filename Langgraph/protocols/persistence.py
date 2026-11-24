# /protocols/persistence.py
from typing import Protocol, List, Dict, Any, runtime_checkable


@runtime_checkable
class ContextWindowGuardProtocol(Protocol):
    """[子职责 A] 入口上下文窗口治理协议（对接 sliding_window 裁剪与认知记忆召回）"""

    async def prepare_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        在意图识别前裁剪超长历史消息，并按需注入匹配的长期认知记忆。
        返回值：需合并更新到 MasterAgentState 的字段字典（如 {'messages': ..., 'window_metrics': ...}）。
        """
        ...


@runtime_checkable
class ToolPrunerProtocol(Protocol):
    """[子职责 B] 动态工具集裁剪协议（对接 mcp_pruner，按当前意图或目标筛选可用工具）"""

    async def prune_tools(self, query: str, available_tools: List[Any]) -> List[Any]:
        """根据当前查询语义与令牌预算，返回裁剪后的精简工具子集"""
        ...


@runtime_checkable
class MemoryCommitterProtocol(Protocol):
    """[子职责 C] 出口记忆沉淀协议（对接 persistence 状态持久化与异步认知归纳）"""

    async def commit_turn(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        在图执行收尾前沉淀本轮对话状态与认知增量。
        返回值：需合并更新到 MasterAgentState 的字段字典（无状态变更时返回 {}）。
        """
        ...
