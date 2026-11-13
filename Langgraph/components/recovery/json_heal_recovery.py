import inspect
import json
import logging
import re
from typing import Dict, List, Optional, Type

from components.recovery.base import BaseRecoveryManager
from protocols.llm import StructuredLLMProtocol
from schemas.base import LLMOutputSchema
from schemas.decision import IntentResult
from schemas.recovery import FailureCategory, FailureContext, RecoveryOutcome

logger = logging.getLogger(__name__)

THINK_BLOCK_PATTERN = re.compile(r"<think>.*?</think>", flags=re.DOTALL | re.IGNORECASE)
MARKDOWN_JSON_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", flags=re.DOTALL | re.IGNORECASE)


class JsonHealRecoveryManager(BaseRecoveryManager):
    """
    专治大模型输出污染导致 JSON / Pydantic 校验失败的恢复子类：
    - L1: 本地正则剥离 <think> 思维链与 Markdown 标记后重新校验（零延迟、零 Token）；
    - L2: 若结构仍残缺，携带校验报错信息触发 Error-Guided LLM 二次修复。
    """

    def __init__(
        self,
        structured_llm: StructuredLLMProtocol,
        recoverable_schemas: Optional[Dict[str, Type[LLMOutputSchema]]] = None,
    ) -> None:
        super().__init__(
            default_fallback_message="抱歉，刚才理解您的请求时格式解析出现了一点小波动，请您换种说法再试一次。"
        )
        self._llm = structured_llm
        # 支持外部注入可扩展的 Schema 注册表，默认支持 IntentResult
        self._schemas: Dict[str, Type[LLMOutputSchema]] = recoverable_schemas or {
            "IntentResult": IntentResult,
        }

    def can_handle(self, context: FailureContext) -> bool:
        return context.category == FailureCategory.OUTPUT_FORMAT_ERROR

    async def _do_recover(self, context: FailureContext) -> Optional[RecoveryOutcome]:
        schema_cls = self._schemas.get(context.target_schema_name or "")
        if schema_cls is None or not context.raw_output:
            return None

        # L1：零成本本地清洗
        cleaned_json = self._extract_clean_json(context.raw_output)
        if cleaned_json:
            try:
                parsed = json.loads(cleaned_json)
                validated = schema_cls.model_validate(parsed)
                logger.info(f"[{context.trace_id}] L1 local strip healed {schema_cls.__name__}.")
                return RecoveryOutcome(
                    is_recovered=True,
                    recovered_data=validated,
                    action_taken="json_l1_regex_healed",
                )
            except Exception as local_err:
                logger.debug(f"[{context.trace_id}] L1 local strip failed: {local_err}")

        # L2：Error-Guided Prompt 二次修复
        try:
            repair_messages: List[Dict[str, str]] = [
                {
                    "role": "system",
                    "content": (
                        "你是一个严格的 JSON 修复引擎。上游模型输出的 JSON 混入了多余文本或格式错误。"
                        "请根据报错信息修正输出，仅返回合法的纯 JSON 对象，严禁包含任何思考过程或 Markdown 标记。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"【目标 Schema】: {schema_cls.__name__}\n"
                        f"【报错信息】: {context.error_message}\n"
                        f"【原始输出】:\n{context.raw_output[:2000]}\n\n"
                        "请输出修复后的纯 JSON："
                    ),
                },
            ]
            if hasattr(self._llm, "agenerate_structured"):
                call_res = self._llm.agenerate_structured(repair_messages, schema_cls)
            else:
                call_res = self._llm.generate_structured(repair_messages, schema_cls)

            repaired_obj = await call_res if inspect.isawaitable(call_res) else call_res
            logger.info(f"[{context.trace_id}] L2 LLM repair healed {schema_cls.__name__}.")
            return RecoveryOutcome(
                is_recovered=True,
                recovered_data=repaired_obj,
                action_taken="json_l2_llm_healed",
            )
        except Exception as llm_err:
            logger.warning(f"[{context.trace_id}] L2 LLM repair failed: {llm_err}")
            return None

    @staticmethod
    def _extract_clean_json(raw_text: str) -> Optional[str]:
        text = THINK_BLOCK_PATTERN.sub("", raw_text).strip()
        md_match = MARKDOWN_JSON_PATTERN.search(text)
        if md_match:
            return md_match.group(1).strip()

        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx : end_idx + 1]
        return None
