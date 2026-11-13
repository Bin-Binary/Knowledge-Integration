# components/intent/hybrid_recognizer.py
import logging
from typing import Dict, Optional, List, Any, Type, TypeVar, Set
from pydantic import BaseModel

from schemas.context import RouteContext, Message
from schemas.decision import IntentResult
from protocols.components import IntentRecognizerProtocol

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class HybridIntentRecognizer(IntentRecognizerProtocol):
    """Hybrid intent recognizer combining static command matching with LLM semantic classification.

    Two-tier strategy:
    1. Fast path: Exact command-map lookup (O(1), zero LLM cost, singleton cache).
    2. Slow path: LLM structured generation with history truncation & tool-message filtering.
    """

    def __init__(
        self,
        command_map: Dict[str, str],
        llm_client: Optional[Any] = None,
        context_window_turns: int = 5,
    ) -> None:
        self._command_map = command_map
        self._llm_client = llm_client
        self._context_window_turns = context_window_turns
        self._static_cache: Dict[str, IntentResult] = {}

    def recognize(self, ctx: RouteContext) -> Optional[IntentResult]:
        stripped = ctx.current_input.strip()
        if not stripped:
            return None

        # --- Tier 1: Static command lookup ---
        static_result = self._try_static_match(stripped)
        if static_result is not None:
            return static_result

        # --- Tier 2: LLM semantic classification ---
        if self._llm_client is None:
            return None

        return self._llm_classify(ctx)

    # ------------------------------------------------------------------
    # Tier 1: Static command matching
    # ------------------------------------------------------------------

    def _try_static_match(self, text: str) -> Optional[IntentResult]:
        for cmd_prefix, intent_label in self._command_map.items():
            if text == cmd_prefix:
                return self._cached_static(cmd_prefix, intent_label, slots={})
            if text.startswith(cmd_prefix + " "):
                raw_arg = text[len(cmd_prefix):].strip()
                return IntentResult(
                    intent=intent_label,
                    confidence=1.0,
                    slots={"raw_arg": raw_arg},
                )
        return None

    def _cached_static(self, key: str, intent: str, slots: Dict[str, Any]) -> IntentResult:
        if key not in self._static_cache:
            self._static_cache[key] = IntentResult(
                intent=intent, confidence=1.0, slots=slots
            )
        return self._static_cache[key]

    # ------------------------------------------------------------------
    # Tier 2: LLM semantic classification
    # ------------------------------------------------------------------

    def _llm_classify(self, ctx: RouteContext) -> Optional[IntentResult]:
        messages = self._build_llm_messages(ctx)
        # 严格遵循快乐路径（Happy Path）：
        # 不在此处吞掉 LLMOutputParseError 或 TimeoutError，直接向上抛出交由外层 Recovery 体系接管
        result = self._llm_client.generate_structured(messages, IntentResult)
        if isinstance(result, IntentResult):
            return result
        logger.warning("[HybridRecognizer] LLM returned non-IntentResult; discarding.")
        return None

    def _build_llm_messages(self, ctx: RouteContext) -> List[Dict[str, str]]:
        system_msg = {"role": "system", "content": self._system_prompt()}
        payload: List[Dict[str, str]] = [system_msg]

        recent = self._truncate_history(ctx.safe_history)
        for msg in recent:
            payload.append({"role": msg.role, "content": msg.content})

        payload.append({"role": "user", "content": ctx.current_input})
        return payload

    def _system_prompt(self) -> str:
        return (
            "You are an intent classifier. "
            "Classify the user's latest message into one of the predefined intent categories. "
            "Extract key slots if present."
        )

    def _truncate_history(self, history: List[Message]) -> List[Message]:
        non_tool = [m for m in history if m.role != "tool"]
        pair_count = 0
        result: List[Message] = []
        for msg in reversed(non_tool):
            result.insert(0, msg)
            if msg.role == "assistant":
                pair_count += 1
            if pair_count >= self._context_window_turns:
                break
        return result
