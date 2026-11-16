# /graphs/intent_graph.py
import inspect
import logging
from typing import Any, Callable, Dict

from schemas.context import RouteContext
from protocols.components import IntentRecognizerProtocol
from components.recovery.mapper import ExceptionMapper
from graphs.state import MasterAgentState, extract_domain_context_from_state
from infra.observability import log_execution

logger = logging.getLogger(__name__)

def create_intent_node(
    recognizer: IntentRecognizerProtocol,
) -> Callable[[MasterAgentState], Any]:
    """意图识别节点：捕获 LLMOutputParseError 与 Pydantic ValidationError 并转为 FailureContext"""

    @log_execution("intent_recognition_node")
    async def intent_recognition_node(state: MasterAgentState) -> Dict[str, Any]:
        trace_id = state.get("trace_id", "unknown_trace")
        session_id = state.get("session_id", "unknown_session")
        current_input, safe_history = extract_domain_context_from_state(state)

        if not current_input.strip():
            logger.warning(f"[IntentNode] Session={session_id} received empty input.")
            return {"intent_result": None, "failure_context": None}

        context = RouteContext(
            session_id=session_id,
            current_input=current_input,
            safe_history=safe_history,
            rag_context=state.get("rag_context"),
            window_metrics=state.get("window_metrics"),
            session_state=state.get("session_state"),
            user_profile=state.get("user_profile", {}),
        )

        try:
            raw_call = recognizer.recognize(context)
            intent_result = await raw_call if inspect.isawaitable(raw_call) else raw_call

            logger.info(
                f"[IntentNode] Intent={intent_result.intent if intent_result else 'NONE'} | "
                f"Conf={intent_result.confidence if intent_result else 0.0:.2f}"
            )
            # 显式清空 failure_context 和 recovery_outcome，防止重试成功后残留脏状态
            return {
                "intent_result": intent_result,
                "failure_context": None,
                "recovery_outcome": None,
            }
        except Exception as exc:
            # 从上一个 failure_context 中提取当前的 retry_count
            prev_failure = state.get("failure_context")
            current_retry = prev_failure.retry_count if prev_failure else 0            
            failure_ctx = ExceptionMapper.to_failure_context(
                exc,
                trace_id=trace_id,
                failed_stage="intent_recognition",
                target_schema_name="IntentResult",
                user_query=current_input,
                retry_count=current_retry,
            )
            # 仅打印脱敏后的错误分类和摘要，不打印包含原始用户对话/模型输出的 exc 和冗长堆栈
            logger.warning(f"[IntentNode] Caught [{failure_ctx.category.value}]: {failure_ctx.error_message}")

            return {
                "intent_result": None,
                "failure_context": failure_ctx,
            }

    return intent_recognition_node
