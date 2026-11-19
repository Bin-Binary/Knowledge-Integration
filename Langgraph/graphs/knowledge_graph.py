# /graphs/knowledge_graph.py
import logging
from typing import Any, Callable, Dict, Literal, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from graphs.state import MasterAgentState, extract_domain_context_from_state
from components.recovery.mapper import ExceptionMapper
from infra.observability import log_execution

# 仅依赖 protocols 与 schemas（严格遵守依赖倒置 DIP，不导入任何 concrete 算子实现）
from protocols.internal_knowledge import (
    InternalKnowledgeEngineProtocol,
    KnowledgeApplicationProtocol,
    KnowledgeAcquisitionProtocol,
    KnowledgeOrganizationProtocol,
    KnowledgeStorageProtocol,
)
from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope
from schemas.internal_knowledge.resolve_problem import ResolveProblem, ResolutionOutcome

logger = logging.getLogger(__name__)

# ==============================================================================
# 通用出入站翻译器（Bridge / Adapter）：隔离 LangGraph 状态与领域黑板模型
# ==============================================================================

def _build_initial_envelope(state: MasterAgentState) -> PipelineEnvelope:
    """【入站翻译】从 MasterAgentState 提取上下文，构造纯领域 PipelineEnvelope"""
    # 若状态中已存在未完成的信封（例如断点恢复场景），直接复用
    existing_env = state.get("knowledge_envelope")
    if existing_env is not None:
        return existing_env

    trace_id = state.get("trace_id") or "unknown_trace"
    session_id = state.get("session_id") or "default_agent"
    current_input, _ = extract_domain_context_from_state(state)

    # 优先使用上游意图识别阶段改写后的标准 query，否则降级使用原始用户输入
    intent_res = state.get("intent_result")
    problem_text = (
        getattr(intent_res, "rewritten_query", None) or current_input
    ).strip()

    return PipelineEnvelope(
        trace_id=trace_id,
        problem_resolution=ResolveProblem(
            problem_id=f"prob_{trace_id}",
            problem=problem_text or "未指定明确问题",
            agent_id=session_id,
        ),
    )

def _map_envelope_to_state_update(envelope: PipelineEnvelope) -> Dict[str, Any]:
    """【出站翻译】将领域黑板信封的最新状态映射回 MasterAgentState 增量字典"""
    resolution = envelope.problem_resolution
    rag_answer = (
        resolution.resultant_situation
        if resolution and resolution.outcome == ResolutionOutcome.SUCCESS
        else None
    )
    return {
        "rag_context": rag_answer,
        "knowledge_envelope": envelope,
        "knowledge_iteration": envelope.iteration,
        "failure_context": None,
    }

# ==============================================================================
# 模式一：黑盒单节点挂载（Black-Box Single Node）
#
# 【适用场景】：
#   1. 线上实时对话主图（MasterAgentGraph）中的知识检索与动态补全。
#   2. 追求低编排复杂度、希望保持主状态图拓扑简洁清爽的场景。
# 【核心优势】：
#   - 整个闭环由 InternalKnowledgeEngine 内部全权控制，主图只需注册 1 个节点。
#   - 引擎代码脱离 LangGraph 也能在 FastAPI / 定时脚本中 100% 独立复用。
# ==============================================================================

def create_knowledge_blackbox_node(
    engine: InternalKnowledgeEngineProtocol,
) -> Callable[[MasterAgentState], Any]:
    """创建黑盒知识库节点：彻底隐藏内部 PipelineEnvelope，仅输出 rag_context"""

    @log_execution("knowledge_blackbox_node")
    async def knowledge_blackbox_node(state: MasterAgentState) -> Dict[str, Any]:
        trace_id = state.get("trace_id") or "unknown_trace"
        # 作为局部临时变量创建，绝不写入 MasterAgentState
        envelope = _build_initial_envelope(state)

        try:
            final_envelope = await engine.execute(envelope)
            resolution = final_envelope.problem_resolution
            rag_answer = (
                resolution.resultant_situation
                if resolution and resolution.outcome == ResolutionOutcome.SUCCESS
                else None
            )
            return {
                "rag_context": rag_answer,
                "failure_context": None,
            }
        except Exception as exc:
            prev_failure = state.get("failure_context")
            current_retry = prev_failure.retry_count if prev_failure else 0
            failure_ctx = ExceptionMapper.to_failure_context(
                exc,
                trace_id=trace_id,
                failed_stage="internal_knowledge_engine",
                target_schema_name="PipelineEnvelope",
                user_query=envelope.problem_resolution.problem if envelope.problem_resolution else "",
                retry_count=current_retry,
            )
            logger.warning("[KnowledgeNode] 闭环执行异常 [%s]: %s", failure_ctx.category.value, failure_ctx.error_message)
            return {"failure_context": failure_ctx}

    return knowledge_blackbox_node


# ==============================================================================
# 模式二：白盒多节点子图编排（White-Box Multi-Node SubGraph）
#
# 【适用场景】：
#   1. 后台离线重型知识构建流水线、或需要精细化监控每个环节耗时的场景。
#   2. 需要 Human-in-the-loop（人工审核）：例如在 organize 组织完知识后暂停图执行，
#      等待人工审核 debug/ 目录产物后再继续执行 save 或晋升。
#   3. 需要利用 LangGraph Checkpointer 持久化每一轮迭代的中间状态快照。
# 【核心优势】：
#   - 复用完全相同的四大 Protocol，利用 LangGraph 原生条件边替代 while 循环。
# ==============================================================================
class KnowledgeSubGraphState(MasterAgentState, total=False):
    """白盒知识子图私有状态：将内部黑板载体隔离在子图作用域内，不污染主图 MasterAgentState"""
    knowledge_envelope: Optional[PipelineEnvelope]
    knowledge_iteration: int


def _route_after_resolve(state: KnowledgeSubGraphState) -> Literal["end_loop", "acquire_step"]:
    """白盒条件边：判断异常、问题是否解决或达到迭代上限，决定终止还是进入采集补全"""
    if state.get("failure_context") is not None:
        return "end_loop"

    envelope = state.get("knowledge_envelope")
    if not envelope or not envelope.problem_resolution:
        return "end_loop"

    # 1. 问题已解决 -> 终止闭环
    if envelope.problem_resolution.outcome == ResolutionOutcome.SUCCESS:
        return "end_loop"

    # 2. 已达最大迭代上限 -> 熔断退出，防止死循环
    if not envelope.can_continue_loop:
        logger.warning("[KnowledgeSubGraph] 达到最大迭代次数 (%d)，带缺口退出", envelope.max_iterations)
        return "end_loop"

    return "acquire_step"


def build_knowledge_whitebox_subgraph(
    storage: KnowledgeStorageProtocol,
    application: KnowledgeApplicationProtocol,
    acquisition: KnowledgeAcquisitionProtocol,
    organization: KnowledgeOrganizationProtocol,
    checkpointer: Optional[Any] = None,
    interrupt_before_save: bool = False,
) -> CompiledStateGraph:
    """构建白盒知识库编译子图（可直接作为子图节点嵌入 MasterAgentGraph）"""
    # [关键修正] 必须传入私有子图状态 KnowledgeSubGraphState，否则状态更新会被 LangGraph 静默丢弃
    subgraph = StateGraph(KnowledgeSubGraphState)

    # 通用异常包装辅助函数，确保白盒节点出错时能平滑转入主图 recovery_node
    def _wrap_step(stage_name: str, fn: Callable[[KnowledgeSubGraphState], Any]):
        async def wrapped(state: KnowledgeSubGraphState) -> Dict[str, Any]:
            try:
                return await fn(state)
            except Exception as exc:
                trace_id = state.get("trace_id") or "unknown_trace"
                prev_failure = state.get("failure_context")
                current_retry = prev_failure.retry_count if prev_failure else 0
                env = state.get("knowledge_envelope")
                query = env.problem_resolution.problem if (env and env.problem_resolution) else ""

                failure_ctx = ExceptionMapper.to_failure_context(
                    exc,
                    trace_id=trace_id,
                    failed_stage=stage_name,
                    target_schema_name="PipelineEnvelope",
                    user_query=query,
                    retry_count=current_retry,
                )
                logger.warning("[KnowledgeSubGraph:%s] 执行异常 [%s]: %s", stage_name, failure_ctx.category.value, failure_ctx.error_message)
                return {"failure_context": failure_ctx}
        return wrapped

    # 1. 定义五个原子节点（统一接收 KnowledgeSubGraphState）
    async def retrieve_node(state: KnowledgeSubGraphState) -> Dict[str, Any]:
        env = _build_initial_envelope(state)
        updated_env = await storage.retrieve(env)
        return {"knowledge_envelope": updated_env}

    async def resolve_node(state: KnowledgeSubGraphState) -> Dict[str, Any]:
        env = _build_initial_envelope(state)
        updated_env = await application.resolve(env)
        return _map_envelope_to_state_update(updated_env)

    async def acquire_node(state: KnowledgeSubGraphState) -> Dict[str, Any]:
        env = _build_initial_envelope(state)
        updated_env = await acquisition.acquire(env)
        return {"knowledge_envelope": updated_env}

    async def organize_node(state: KnowledgeSubGraphState) -> Dict[str, Any]:
        env = _build_initial_envelope(state)
        updated_env = await organization.organize(env)
        return {"knowledge_envelope": updated_env}

    async def save_and_advance_node(state: KnowledgeSubGraphState) -> Dict[str, Any]:
        env = _build_initial_envelope(state)
        saved_env = await storage.save(env)
        next_iter_env = saved_env.advance_to_next_iteration()
        return {
            "knowledge_envelope": next_iter_env,
            "knowledge_iteration": next_iter_env.iteration,
        }

    # 2. 注册带异常保护的子图节点
    subgraph.add_node("retrieve", _wrap_step("knowledge_retrieve", retrieve_node))
    subgraph.add_node("resolve", _wrap_step("knowledge_resolve", resolve_node))
    subgraph.add_node("acquire", _wrap_step("knowledge_acquire", acquire_node))
    subgraph.add_node("organize", _wrap_step("knowledge_organize", organize_node))
    subgraph.add_node("save_and_advance", _wrap_step("knowledge_save", save_and_advance_node))

    # 3. 编排白盒闭环拓扑边（加入异常熔断检查：一旦任何一步捕获 failure_context 直接结束子图回交主图自愈）
    def _route_or_abort(next_node: str):
        def router(state: KnowledgeSubGraphState) -> str:
            return END if state.get("failure_context") is not None else next_node
        return router

    subgraph.add_edge(START, "retrieve")
    subgraph.add_conditional_edges("retrieve", _route_or_abort("resolve"), {END: END, "resolve": "resolve"})

    subgraph.add_conditional_edges(
        "resolve",
        _route_after_resolve,
        {
            "end_loop": END,
            "acquire_step": "acquire",
        },
    )

    subgraph.add_conditional_edges("acquire", _route_or_abort("organize"), {END: END, "organize": "organize"})
    subgraph.add_conditional_edges("organize", _route_or_abort("save_and_advance"), {END: END, "save_and_advance": "save_and_advance"})
    subgraph.add_conditional_edges("save_and_advance", _route_or_abort("retrieve"), {END: END, "retrieve": "retrieve"})

    interrupt_nodes = ["save_and_advance"] if interrupt_before_save else None
    return subgraph.compile(checkpointer=checkpointer, interrupt_before=interrupt_nodes)
