# /components/intent/hybrid_recognizer.py
import re
import logging
from typing import Dict, Optional, List, Any, Tuple, Pattern

from schemas import RouteContext, Message, IntentResult, IntentCatalog
from protocols import IntentRecognizerProtocol, StructuredLLMProtocol

logger = logging.getLogger(__name__)


class HybridIntentRecognizer(IntentRecognizerProtocol):
    """混合意图识别器：
    1. 快路径（Tier 1）：O(1) 静态前缀指令精确匹配，零大模型开销。
    2. 慢路径（Tier 2）：基于 IntentCatalog 动态生成的自省 Schema Prompt 进行语义分类。
    """

    def __init__(
        self,
        catalog: IntentCatalog,
        llm_client: Optional[StructuredLLMProtocol] = None,
        context_window_turns: int = 5,
    ) -> None:
        self._catalog = catalog
        self._command_map = catalog.command_map
        self._llm_client = llm_client
        self._context_window_turns = context_window_turns
        self._static_cache: Dict[str, IntentResult] = {}
        # 启动期预编译动态 System Prompt，复用 IntentResult.to_prompt_guide()
        self._compiled_system_prompt = self._build_system_prompt(catalog)
        # 启动时预编译所有正则规则，避免运行期重复编译开销
        self._compiled_rules: List[Tuple[str, float, List[Pattern[str]]]] = [
            (
                rule.intent,
                rule.confidence,
                [re.compile(p, re.IGNORECASE) for p in rule.patterns],
            )
            for rule in catalog.fast_rules
        ]        

    @staticmethod
    def _build_system_prompt(catalog: IntentCatalog) -> str:
        catalog_block = catalog.format_catalog_block()
        output_schema_guide = IntentResult.to_prompt_guide()

        return (
            "不要推理\n"
            "你是一个精准的意图分类器。请根据【可选意图列表】，将用户最新消息归类为最匹配的一项，并提取关键槽位。\n\n"
            f"【输出数据结构要求】\n{output_schema_guide}\n\n"
            "【约束条件】\n"
            "1. 严格以合法的单行 JSON 对象输出，严禁输出任何分析步骤、Markdown 标记或额外解释。\n"
            "2. `intent` 必须严格命中上述列表中的标识之一。\n\n"
            f"【可选意图列表】\n{catalog_block}\n"
            "/no_think"
        )

    async def recognize(self, ctx: RouteContext) -> Optional[IntentResult]:
        stripped = ctx.current_input.strip()
        if not stripped:
            return None

        # --- Tier 1: Static command lookup ---
        static_result = self._try_static_match(stripped)
        if static_result is not None:
            return static_result

        # Tier 1.5: 非LLM快速正则/关键词匹配（如 "你好"、"把...存入知识库"）
        fast_rule_result = self._try_fast_rules(stripped)
        if fast_rule_result is not None:
            return fast_rule_result

        # --- Tier 2: LLM semantic classification ---
        if self._llm_client is None:
            return None

        return await self._llm_classify(ctx)

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
    # Tier 1.5: fast_rules
    # ------------------------------------------------------------------
    def _try_fast_rules(self, text: str) -> Optional[IntentResult]:
        for intent_label, conf, patterns in self._compiled_rules:
            for pat in patterns:
                match = pat.search(text)
                if match:
                    # 如果正则中使用了命名捕获组 (?P<topic>...)，自动提取为 slots！
                    extracted_slots = {k: v for k, v in match.groupdict().items() if v}
                    return IntentResult(
                        intent=intent_label,
                        confidence=conf,
                        slots=extracted_slots,
                    )
        return None

    # ------------------------------------------------------------------
    # Tier 2: LLM semantic classification
    # ------------------------------------------------------------------

    async def _llm_classify(self, ctx: RouteContext) -> Optional[IntentResult]:
        messages = self._build_llm_messages(ctx)
        result = await self._llm_client.generate_structured(messages, IntentResult)
        if isinstance(result, IntentResult):
            return result
        logger.warning("[HybridRecognizer] LLM returned non-IntentResult; discarding.")
        return None
    
    def _build_llm_messages(self, ctx: RouteContext) -> List[Dict[str, str]]:
        system_msg = {"role": "system", "content": self._compiled_system_prompt}
        payload: List[Dict[str, str]] = [system_msg]

        recent = self._truncate_history(ctx.safe_history)
        for msg in recent:
            payload.append({"role": msg.role, "content": msg.content})

        payload.append({"role": "user", "content": ctx.current_input})
        return payload

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
