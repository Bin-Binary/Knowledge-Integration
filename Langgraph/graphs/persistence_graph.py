# /graphs/persistence_graph.py
import logging
from typing import Callable, Awaitable, Dict, Any

from graphs.state import MasterAgentState
from protocols.persistence import (
    ContextWindowGuardProtocol,
    MemoryCommitterProtocol,
)
from infra.observability import log_execution

logger = logging.getLogger(__name__)


def create_context_guard_node(
    guard: ContextWindowGuardProtocol,
) -> Callable[[MasterAgentState], Awaitable[Dict[str, Any]]]:
    """构建入口上下文窗口治理节点（位于 START 与 intent_recognition 之间）"""

    @log_execution("context_guard_node", level=logging.DEBUG)
    async def _node(state: MasterAgentState) -> Dict[str, Any]:
        return await guard.prepare_context(dict(state))

    return _node


def create_memory_commit_node(
    committer: MemoryCommitterProtocol,
) -> Callable[[MasterAgentState], Awaitable[Dict[str, Any]]]:
    """构建出口记忆持久化沉淀节点（位于业务收尾与 END 之间）"""

    @log_execution("memory_commit_node", level=logging.DEBUG)
    async def _node(state: MasterAgentState) -> Dict[str, Any]:
        return await committer.commit_turn(dict(state))

    return _node
