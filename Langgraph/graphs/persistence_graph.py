# /graphs/persistence_graph.py
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from graphs.state import MasterAgentState, extract_domain_context_from_state
from protocols import ExceptionMapperProtocol
from protocols.persistence import (
    ContextWindowGuardProtocol,
    MemoryCommitterProtocol,
)
from infra.observability import log_execution

logger = logging.getLogger(__name__)


def create_context_guard_node(
    guard: ContextWindowGuardProtocol,
    map_exception: Optional[ExceptionMapperProtocol] = None,
) -> Callable[[MasterAgentState], Awaitable[Dict[str, Any]]]:
    """构建入口上下文窗口治理节点（位于 START 与 intent_recognition 之间）"""

    @log_execution("context_guard_node", level=logging.DEBUG)
    async def _node(state: MasterAgentState) -> Dict[str, Any]:
        try:
            return await guard.prepare_context(dict(state))
        except Exception as exc:
            if map_exception is None:
                raise
            current_input, _ = extract_domain_context_from_state(state)
            prev = state.get("failure_context")
            failure_ctx = map_exception(
                exc,
                trace_id=state.get("trace_id", "unknown_trace"),
                failed_stage="context_guard",
                user_query=current_input,
                retry_count=prev.retry_count if prev else 0,
            )
            logger.warning(
                "[ContextGuardNode] Caught [%s]: %s",
                failure_ctx.category.value,
                failure_ctx.error_message,
            )
            return {"failure_context": failure_ctx, "recovery_outcome": None}

    return _node


def create_memory_commit_node(
    committer: MemoryCommitterProtocol,
    map_exception: Optional[ExceptionMapperProtocol] = None,
) -> Callable[[MasterAgentState], Awaitable[Dict[str, Any]]]:
    """构建出口记忆持久化沉淀节点（位于业务收尾与 END 之间）"""

    @log_execution("memory_commit_node", level=logging.DEBUG)
    async def _node(state: MasterAgentState) -> Dict[str, Any]:
        try:
            return await committer.commit_turn(dict(state))
        except Exception as exc:
            # 记忆持久化属于后置旁路动作，失败时记录标准化异常但不阻断已生成的 final_response
            if map_exception is not None:
                current_input, _ = extract_domain_context_from_state(state)
                failure_ctx = map_exception(
                    exc,
                    trace_id=state.get("trace_id", "unknown_trace"),
                    failed_stage="memory_commit",
                    user_query=current_input,
                )
                logger.error(
                    "[MemoryCommitNode] Non-blocking failure [%s]: %s",
                    failure_ctx.category.value,
                    failure_ctx.error_message,
                )
            else:
                logger.exception("[MemoryCommitNode] Failed to commit turn memory.")
            return {}

    return _node
