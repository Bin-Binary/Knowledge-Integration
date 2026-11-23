# /graphs/master_graph.py
import inspect
import logging
from typing import Any, Callable, Literal, Optional, Protocol
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from protocols.agent import AgentProtocol
from protocols.components import (
    IntentRecognizerProtocol,
    RouterProtocol,
    ExceptionRecoveryProtocol,
)
from protocols.internal_knowledge import InternalKnowledgeEngineProtocol
from protocols.persistence import (
    ContextWindowGuardProtocol,
    MemoryCommitterProtocol,
)
from protocols.governance import HumanApprovalGateProtocol
from schemas.intent_and_route_catalog import TargetDomain
from schemas.decision import RouteDecision
from graphs.state import MasterAgentState
from graphs.intent_graph import create_intent_node
from graphs.routing_graph import create_routing_node
from graphs.knowledge_graph import build_knowledge_domain_subgraph
from graphs.execution_graph import create_execution_node
from graphs.recovery_graph import create_recovery_node
from graphs.persistence_graph import (
    create_context_guard_node,
    create_memory_commit_node,
)
from graphs.governance_graph import create_approval_gate_node
from infra.observability import log_execution

logger = logging.getLogger(__name__)

# 核心与扩展节点常量标识
CONTEXT_GUARD_NODE = "context_guard"
INTENT_NODE = "intent_recognition"
ROUTING_NODE = "routing"
KNOWLEDGE_NODE = TargetDomain.KNOWLEDGE.value
APPROVAL_GATE_NODE = "approval_gate"
EXECUTION_NODE = TargetDomain.EXECUTION.value
RECOVERY_NODE = "recovery_node"
MEMORY_COMMIT_NODE = "memory_commit"

# 默认最大自愈重试次数（防底层节点未计数导致的死循环）
DEFAULT_MAX_RECOVERY_ATTEMPTS = 3


class _AgentRegistryLike(Protocol):
    """隔离 components.agents.registry 具体实现，保持图编排层零组件耦合"""

    def get(self, agent_id: str) -> AgentProtocol:
        ...


def _resolve_post_routing_stage(
    decision: RouteDecision,
    has_knowledge: bool,
    has_approval_gate: bool,
) -> str:
    """统一路由下游阶段决策：知识子图优先 -> 其次审批门禁 -> 最终执行节点"""
    if has_knowledge and not decision.should_skip_knowledge:
        return KNOWLEDGE_NODE
    if has_approval_gate:
        return APPROVAL_GATE_NODE
    return EXECUTION_NODE


@log_execution("route_after_context_guard", level=logging.DEBUG)
def _route_after_context_guard(
    state: MasterAgentState,
) -> Literal["recovery_node", "intent_recognition", "finish_flow"]:
    """上下文守卫出口边：拦截预处理异常或超限终止"""
    if state.get("failure_context") is not None:
        return RECOVERY_NODE
    if state.get("is_terminal", False):
        return "finish_flow"
    return INTENT_NODE


@log_execution("route_after_intent", level=logging.DEBUG)
def _route_after_intent(
    state: MasterAgentState,
) -> Literal["recovery_node", "routing"]:
    """意图识别出口边：异常转自愈，其余一律进入路由调度"""
    if state.get("failure_context") is not None:
        return RECOVERY_NODE
    return ROUTING_NODE


@log_execution("route_after_execution", level=logging.DEBUG)
def _route_after_execution(
    state: MasterAgentState,
) -> Literal["recovery_node", "finish_flow"]:
    """执行节点出口边：捕获执行期未自愈异常时转入自愈，否则进入收尾阶段"""
    if state.get("failure_context") is not None:
        return RECOVERY_NODE
    return "finish_flow"


def _wrap_recovery_node(
    raw_node: Callable[[MasterAgentState], Any],
    max_attempts: int = DEFAULT_MAX_RECOVERY_ATTEMPTS,
) -> Callable[[MasterAgentState], Any]:
    """
    【风险修复 1】自愈节点状态防火墙（兼容同步 / 异步节点）：
    1. 记录原故障节点快照 _last_failed_node 后强制清理 failure_context，防止下游重试死循环；
    2. 在编排层兜底熔断超过最大重试次数的自愈循环。
    """
    def _post_process(
        state: MasterAgentState,
        raw_result: Any,
        attempts: int,
        last_failed_node: Optional[str],
    ) -> dict[str, Any]:
        update = dict(raw_result or {})
        merged_state = {**state, **update}
        outcome = merged_state.get("recovery_outcome")

        if last_failed_node is not None:
            update["_last_failed_node"] = last_failed_node

        if outcome is not None and getattr(outcome, "is_recovered", False):
            update["failure_context"] = None

        update["_recovery_attempts"] = attempts
        return update

    if inspect.iscoroutinefunction(raw_node):
        async def _async_guarded_recovery(state: MasterAgentState) -> dict[str, Any]:
            attempts = int(state.get("_recovery_attempts", 0)) + 1
            if attempts > max_attempts:
                logger.error(
                    "Max recovery attempts (%d) exceeded; forcing terminal termination.",
                    max_attempts,
                )
                return {"_recovery_attempts": attempts, "is_terminal": True}

            orig_failure = state.get("failure_context")
            # 在 _wrap_recovery_node 中提取 failed_stage（兼容 failed_node）
            last_failed_stage = (
                getattr(orig_failure, "failed_stage", None)
                or getattr(orig_failure, "failed_node", None)
                if orig_failure
                else None
            )
            raw_result = await raw_node(state)
            return _post_process(state, raw_result, attempts, last_failed_stage)

        return _async_guarded_recovery

    def _sync_guarded_recovery(state: MasterAgentState) -> dict[str, Any]:
        attempts = int(state.get("_recovery_attempts", 0)) + 1
        if attempts > max_attempts:
            logger.error(
                "Max recovery attempts (%d) exceeded; forcing terminal termination.",
                max_attempts,
            )
            return {"_recovery_attempts": attempts, "is_terminal": True}

        orig_failure = state.get("failure_context")
        last_failed_stage = (
            getattr(orig_failure, "failed_stage", None)
            or getattr(orig_failure, "failed_node", None)
            if orig_failure
            else None
        )
        raw_result = raw_node(state)
        return _post_process(state, raw_result, attempts, last_failed_stage)


    return _sync_guarded_recovery


def _wrap_memory_commit_node(
    raw_node: Callable[[MasterAgentState], Any],
) -> Callable[[MasterAgentState], Any]:
    """
    【风险修复 2】记忆提交幂等门禁（兼容同步 / 异步节点）：
    当流程因未恢复异常、审批拒绝或参数缺失提前终止且无有效回复时，跳过记忆持久化，避免写入半成品脏数据。
    """
    def _should_skip(state: MasterAgentState) -> bool:
        has_unresolved_error = state.get("failure_context") is not None
        is_aborted_without_response = (
            state.get("is_terminal", False) and not state.get("final_response")
        )
        if has_unresolved_error or is_aborted_without_response:
            logger.warning(
                "Skipping memory_commit due to unresolved error or empty terminal state."
            )
            return True
        return False

    if inspect.iscoroutinefunction(raw_node):
        async def _async_guarded_memory_commit(state: MasterAgentState) -> dict[str, Any]:
            if _should_skip(state):
                return {}
            return await raw_node(state)

        return _async_guarded_memory_commit

    def _sync_guarded_memory_commit(state: MasterAgentState) -> dict[str, Any]:
        if _should_skip(state):
            return {}
        return raw_node(state)

    return _sync_guarded_memory_commit

@log_execution("build_master_agent_graph")
def build_master_agent_graph(
    intent_recognizer: IntentRecognizerProtocol,
    router: RouterProtocol,
    agent_registry: _AgentRegistryLike,
    recovery_manager: ExceptionRecoveryProtocol,
    knowledge_engine: Optional[InternalKnowledgeEngineProtocol] = None,
    context_guard: Optional[ContextWindowGuardProtocol] = None,
    approval_gate: Optional[HumanApprovalGateProtocol] = None,
    memory_committer: Optional[MemoryCommitterProtocol] = None,
    checkpointer: Optional[Any] = None,
    max_recovery_attempts: int = DEFAULT_MAX_RECOVERY_ATTEMPTS,
) -> CompiledStateGraph:
    """
    【封版】生产环境主控状态图构建器（全依赖倒置 + 正交热插拔扩展槽 + 状态防火墙）：
    拓扑主干：
    START -> [context_guard] -> intent_recognition -> routing
          -> [knowledge] -> [approval_gate] -> execution -> [memory_commit] -> END
    """
    workflow = StateGraph(MasterAgentState)

    has_knowledge = knowledge_engine is not None
    has_context_guard = context_guard is not None
    has_approval_gate = approval_gate is not None
    has_memory_commit = memory_committer is not None
    terminal_target = MEMORY_COMMIT_NODE if has_memory_commit else END

    # ------------------------------------------------------------------
    # 1. 注册核心节点与正交扩展槽节点（注入状态防护包装器）
    # ------------------------------------------------------------------
    if has_context_guard:
        workflow.add_node(CONTEXT_GUARD_NODE, create_context_guard_node(context_guard))

    workflow.add_node(INTENT_NODE, create_intent_node(intent_recognizer))
    workflow.add_node(ROUTING_NODE, create_routing_node(router))
    workflow.add_node(EXECUTION_NODE, create_execution_node(agent_registry))  # type: ignore[arg-type]
    workflow.add_node(
        RECOVERY_NODE,
        _wrap_recovery_node(
            create_recovery_node(recovery_manager),
            max_attempts=max_recovery_attempts,
        ),
    )

    if has_knowledge:
        workflow.add_node(
            KNOWLEDGE_NODE,
            build_knowledge_domain_subgraph(knowledge_engine),
        )

    if has_approval_gate:
        workflow.add_node(
            APPROVAL_GATE_NODE,
            create_approval_gate_node(approval_gate),
        )

    if has_memory_commit:
        workflow.add_node(
            MEMORY_COMMIT_NODE,
            _wrap_memory_commit_node(create_memory_commit_node(memory_committer)),
        )

    # ------------------------------------------------------------------
    # 2. 闭包条件边定义（自适应扩展槽开关）
    # ------------------------------------------------------------------
    @log_execution("route_after_routing", level=logging.DEBUG)
    def _route_after_routing(state: MasterAgentState) -> str:
        if state.get("failure_context") is not None:
            return RECOVERY_NODE
        decision = state.get("route_decision")
        if decision is None:
            return "finish_flow"
        return _resolve_post_routing_stage(decision, has_knowledge, has_approval_gate)

    @log_execution("route_after_knowledge", level=logging.DEBUG)
    def _route_after_knowledge(state: MasterAgentState) -> str:
        if state.get("failure_context") is not None:
            return RECOVERY_NODE
        if state.get("final_response"):
            return "finish_flow"
        return APPROVAL_GATE_NODE if has_approval_gate else EXECUTION_NODE

    @log_execution("route_after_approval", level=logging.DEBUG)
    def _route_after_approval(state: MasterAgentState) -> str:
        if state.get("failure_context") is not None:
            return RECOVERY_NODE
        if state.get("is_terminal", False):
            return "finish_flow"
        return EXECUTION_NODE

    @log_execution("route_after_recovery", level=logging.DEBUG)
    def _route_after_recovery(state: MasterAgentState) -> str:
        """异常自愈后的精准续跑路由（产物已还原时直接推进到下一阶段，避免重复调用报错节点）"""
        outcome = state.get("recovery_outcome")
        failure_ctx = state.get("failure_context")
        if (
            outcome is None
            or not getattr(outcome, "is_recovered", False)
            or state.get("is_terminal", False)
            or int(state.get("_recovery_attempts", 0)) > max_recovery_attempts
        ):
            return "finish_flow"

        failed_stage = (
            getattr(outcome, "target_node", None)
            or state.get("_last_failed_node")
            or (
                getattr(failure_ctx, "failed_stage", None)
                or getattr(failure_ctx, "failed_node", None)
                if failure_ctx
                else None
            )
        )

        # 1. 若产物已由 recovery_node 修复填充，直接推进至下一阶段
        if failed_stage == INTENT_NODE and state.get("intent_result") is not None:
            return ROUTING_NODE
        if failed_stage == ROUTING_NODE and state.get("route_decision") is not None:
            return _resolve_post_routing_stage(
                state["route_decision"], has_knowledge, has_approval_gate
            )

        # 2. 若仅做了环境/上下文修复（未直接生成产物），则重入原故障节点
        if failed_stage == CONTEXT_GUARD_NODE and has_context_guard:
            return CONTEXT_GUARD_NODE
        if failed_stage == INTENT_NODE:
            return INTENT_NODE
        if failed_stage == ROUTING_NODE:
            return ROUTING_NODE
        if failed_stage == KNOWLEDGE_NODE and has_knowledge:
            return KNOWLEDGE_NODE
        if failed_stage == APPROVAL_GATE_NODE and has_approval_gate:
            return APPROVAL_GATE_NODE
        if failed_stage == EXECUTION_NODE:
            return EXECUTION_NODE

        # 3. 兜底状态推断推进
        if state.get("route_decision") is not None:
            return _resolve_post_routing_stage(
                state["route_decision"], has_knowledge, has_approval_gate
            )
        if state.get("intent_result") is not None:
            return ROUTING_NODE
        return INTENT_NODE


    # ------------------------------------------------------------------
    # 3. 编排主干与分支拓扑边
    # ------------------------------------------------------------------
    if has_context_guard:
        workflow.add_edge(START, CONTEXT_GUARD_NODE)
        workflow.add_conditional_edges(
            CONTEXT_GUARD_NODE,
            _route_after_context_guard,
            {
                RECOVERY_NODE: RECOVERY_NODE,
                INTENT_NODE: INTENT_NODE,
                "finish_flow": terminal_target,
            },
        )
    else:
        workflow.add_edge(START, INTENT_NODE)

    workflow.add_conditional_edges(
        INTENT_NODE,
        _route_after_intent,
        {
            RECOVERY_NODE: RECOVERY_NODE,
            ROUTING_NODE: ROUTING_NODE,
        },
    )

    routing_targets: dict[str, Any] = {
        RECOVERY_NODE: RECOVERY_NODE,
        EXECUTION_NODE: EXECUTION_NODE,
        "finish_flow": terminal_target,
    }
    if has_knowledge:
        routing_targets[KNOWLEDGE_NODE] = KNOWLEDGE_NODE
    if has_approval_gate:
        routing_targets[APPROVAL_GATE_NODE] = APPROVAL_GATE_NODE

    workflow.add_conditional_edges(
        ROUTING_NODE,
        _route_after_routing,
        routing_targets,
    )

    if has_knowledge:
        knowledge_targets: dict[str, Any] = {
            RECOVERY_NODE: RECOVERY_NODE,
            EXECUTION_NODE: EXECUTION_NODE,
            "finish_flow": terminal_target,
        }
        if has_approval_gate:
            knowledge_targets[APPROVAL_GATE_NODE] = APPROVAL_GATE_NODE

        workflow.add_conditional_edges(
            KNOWLEDGE_NODE,
            _route_after_knowledge,
            knowledge_targets,
        )

    if has_approval_gate:
        workflow.add_conditional_edges(
            APPROVAL_GATE_NODE,
            _route_after_approval,
            {
                RECOVERY_NODE: RECOVERY_NODE,
                EXECUTION_NODE: EXECUTION_NODE,
                "finish_flow": terminal_target,
            },
        )

    workflow.add_conditional_edges(
        EXECUTION_NODE,
        _route_after_execution,
        {
            RECOVERY_NODE: RECOVERY_NODE,
            "finish_flow": terminal_target,
        },
    )

    recovery_targets: dict[str, Any] = {
        INTENT_NODE: INTENT_NODE,
        ROUTING_NODE: ROUTING_NODE,
        EXECUTION_NODE: EXECUTION_NODE,
        "finish_flow": terminal_target,
    }
    if has_context_guard:
        recovery_targets[CONTEXT_GUARD_NODE] = CONTEXT_GUARD_NODE
    if has_knowledge:
        recovery_targets[KNOWLEDGE_NODE] = KNOWLEDGE_NODE
    if has_approval_gate:
        recovery_targets[APPROVAL_GATE_NODE] = APPROVAL_GATE_NODE

    workflow.add_conditional_edges(
        RECOVERY_NODE,
        _route_after_recovery,
        recovery_targets,
    )

    if has_memory_commit:
        workflow.add_edge(MEMORY_COMMIT_NODE, END)

    logger.info(
        "MasterAgentGraph compiled (knowledge=%s, context_guard=%s, approval_gate=%s, memory_commit=%s).",
        has_knowledge,
        has_context_guard,
        has_approval_gate,
        has_memory_commit,
    )
    return workflow.compile(checkpointer=checkpointer)        
