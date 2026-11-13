import inspect
import logging
from typing import Any, Callable, Dict
from pydantic import ValidationError
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from schemas.context import RouteContext
from schemas.recovery import FailureCategory, FailureContext
from protocols.components import IntentRecognizerProtocol
from graphs.state import MasterAgentState, extract_domain_context_from_state

logger = logging.getLogger(__name__)


def create_intent_node(
    recognizer: IntentRecognizerProtocol,
) -> Callable[[MasterAgentState], Any]:
    """意图识别节点：捕获 LLMOutputParseError 与 Pydantic ValidationError 并转为 FailureContext"""

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
                f"[IntentNode] Session={session_id} | "
                f"Intent={intent_result.intent if intent_result else 'NONE'} | "
                f"Conf={intent_result.confidence if intent_result else 0.0:.2f}"
            )
            return {
                "route_context": context,
                "intent_result": intent_result,
                "failure_context": None,
            }

        except (LLMOutputParseError, ValidationError) as parse_err:
            raw_text = (
                getattr(parse_err, "raw_output", None)
                if isinstance(parse_err, LLMOutputParseError)
                else _extract_raw_from_validation_error(parse_err)
            )
            logger.warning(
                f"[IntentNode] Session={session_id} Output format error captured, "
                f"routing to recovery_node. Error: {parse_err}"
            )
            return {
                "route_context": context,
                "intent_result": None,
                "failure_context": FailureContext(
                    trace_id=trace_id,
                    failed_stage="intent_recognition",
                    category=FailureCategory.OUTPUT_FORMAT_ERROR,
                    error_message=str(parse_err),
                    raw_output=raw_text,
                    target_schema_name="IntentResult",
                ),
            }

        except Exception as exc:
            logger.error(f"[IntentNode] Session={session_id} unexpected error: {exc}", exc_info=True)
            return {
                "route_context": context,
                "intent_result": None,
                "failure_context": FailureContext(
                    trace_id=trace_id,
                    failed_stage="intent_recognition",
                    category=FailureCategory.UNKNOWN_ERROR,
                    error_message=str(exc),
                ),
            }

    return intent_recognition_node
