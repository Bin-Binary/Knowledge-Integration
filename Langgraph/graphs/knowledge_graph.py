# /graphs/knowledge_graph.py
import logging
from typing import Any, Dict, Literal, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import AIMessage

from graphs.state import MasterAgentState, extract_domain_context_from_state
from infra import log_execution
from protocols import ExceptionMapperProtocol
from components.internal_knowledge import (
    InternalKnowledgeEngineProtocol,
    PipelineEnvelope,
    ResolveProblem,
    ResolutionOutcome
)
from schemas import TargetDomain

logger = logging.getLogger(__name__)

def _unpack_state_to_envelope(
    state: MasterAgentState, prefix: str, max_iterations: int = 3
) -> PipelineEnvelope:
    """【统一入站拆包】MasterAgentState -> PipelineEnvelope"""
    trace_id = state.get("trace_id") or "unknown_trace"
    session_id = state.get("session_id") or "default_agent"
    current_input, _ = extract_domain_context_from_state(state)

    intent_res = state.get("intent_result")
    decision = state.get("route_decision")
    # 优先复用 IntentResult.primary_query 屏蔽不同匹配器的槽位键名差异
    slot_topic = (
        (intent_res.primary_query if intent_res else None)
        or (decision.params.get("topic") if decision else None)
        or (decision.params.get("raw_arg") if decision else None)
    )

    problem_text = (
        slot_topic
        or getattr(intent_res, "rewritten_query", None)
        or current_input
    ).strip()

    return PipelineEnvelope(
        trace_id=trace_id,
        max_iterations=max_iterations,  # 透传配置的最大闭环轮次
        problem_resolution=ResolveProblem(
            problem_id=f"{prefix}_{trace_id}",
            problem=problem_text or "未指定明确问题",
            agent_id=session_id,
        ),
    )

def _pack_retrieval_to_state(envelope: PipelineEnvelope) -> Dict[str, Any]:
    """【出站封包：快速检索】提取只读背景资料写入 rag_context"""
    resolution = envelope.problem_resolution
    if not resolution:
        return {"rag_context": None, "failure_context": None, "recovery_outcome": None}

    if getattr(resolution, "resultant_situation", None):
        rag_text = resolution.resultant_situation
    else:
        items = getattr(resolution, "resolutions", None) or []
        snippets = [getattr(i, "content", None) or str(i) for i in items if i]
        rag_text = "\n\n---\n\n".join(snippets) if snippets else None

    return {"rag_context": rag_text, "failure_context": None, "recovery_outcome": None}

def _pack_learning_to_state(envelope: PipelineEnvelope) -> Dict[str, Any]:
    """【出站封包：持续学习】同时支持 SUCCESS 完整答案与 PARTIAL 语义降级答案"""
    resolution = envelope.problem_resolution
    has_answer = (
        resolution
        and resolution.outcome in (ResolutionOutcome.SUCCESS, ResolutionOutcome.PARTIAL)
        and bool(resolution.resultant_situation)
    )
    summary = (
        resolution.resultant_situation
        if has_answer
        else "已完成本轮知识切片归档，但暂未形成完整解答。"
    )
    return {
        "rag_context": summary,
        "final_response": summary,
        "messages": [AIMessage(content=summary)],
        "failure_context": None,
        "recovery_outcome": None,
    }

def _route_knowledge_mode(state: MasterAgentState) -> Literal["fast_retrieve", "deep_learn"]:
    decision = state.get("route_decision")
    if (
        decision
        and decision.params.get("target_domain") == TargetDomain.KNOWLEDGE
        and decision.target_node == "deep_learn"
    ):
        return "deep_learn"
    return "fast_retrieve"

def build_knowledge_domain_subgraph(
    engine: InternalKnowledgeEngineProtocol,
    map_exception: ExceptionMapperProtocol,
    checkpointer: Optional[Any] = None,
    max_iterations: int = 3,  # 新增默认向后兼容参数
) -> CompiledStateGraph:
    """
    知识领域防腐层子图：
    仅依赖单一总控协议 InternalKnowledgeEngineProtocol，对主图暴露为单一黑盒节点。
    """
    subgraph = StateGraph(MasterAgentState)

    @log_execution("knowledge.fast_retrieve_node")
    async def fast_retrieve_node(state: MasterAgentState) -> Dict[str, Any]:
        envelope = _unpack_state_to_envelope(state, prefix="read", max_iterations=max_iterations)
        try:
            updated_env = await engine.fast_retrieve(envelope)
            return _pack_retrieval_to_state(updated_env)
        except Exception as exc:
            logger.exception("[KnowledgeGraph] knowledge:fast_retrieve 执行中断 (trace_id=%s): %s", state.get("trace_id"), exc)
            retry_count=state.get("_recovery_attempts", 0)
            return {
                "failure_context": map_exception(
                    exc,
                    trace_id=state.get("trace_id", "unknown"),
                    failed_stage="knowledge:fast_retrieve",
                    target_schema_name="PipelineEnvelope",
                    user_query=envelope.problem_resolution.problem if envelope.problem_resolution else "",
                    retry_count=retry_count
                ),
                "recovery_outcome": None,
            }


    @log_execution("knowledge.deep_learn_node")
    async def deep_learn_node(state: MasterAgentState) -> Dict[str, Any]:
        envelope = _unpack_state_to_envelope(state, prefix="learn", max_iterations=max_iterations)
        try:
            final_env = await engine.execute(envelope)
            return _pack_learning_to_state(final_env)
        except Exception as exc:
            logger.exception("[KnowledgeGraph] knowledge:deep_learn 执行中断 (trace_id=%s): %s", state.get("trace_id"), exc)
            retry_count=state.get("_recovery_attempts", 0)
            return {
                "failure_context": map_exception(
                    exc,
                    trace_id=state.get("trace_id", "unknown"),
                    failed_stage="knowledge:deep_learn",
                    target_schema_name="PipelineEnvelope",
                    user_query=envelope.problem_resolution.problem if envelope.problem_resolution else "",
                    retry_count=retry_count
                ),
                "recovery_outcome": None,
            }

    subgraph.add_node("fast_retrieve", fast_retrieve_node)
    subgraph.add_node("deep_learn", deep_learn_node)

    subgraph.add_conditional_edges(
        START,
        _route_knowledge_mode,
        {
            "fast_retrieve": "fast_retrieve",
            "deep_learn": "deep_learn",
        },
    )
    subgraph.add_edge("fast_retrieve", END)
    subgraph.add_edge("deep_learn", END)

    return subgraph.compile(checkpointer=checkpointer)
