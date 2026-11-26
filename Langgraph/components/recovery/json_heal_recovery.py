# /components/recovery/json_heal_recovery.py
import inspect
import json
import logging
import re
from typing import ClassVar, Dict, List, Optional, Type
from pydantic import BaseModel

from schemas.recovery import FailureContext, RecoveryOutcome
from schemas.decision import IntentResult
from components.recovery.registry import RecoveryPluginRegistry
from protocols.llm import StructuredLLMProtocol

logger = logging.getLogger(__name__)


@RecoveryPluginRegistry.register("llm_json_repair")
class LLMJsonRepairRecovery:
    """
    基于大模型的结构化输出 L2 重写修复插件（实现 ExceptionRecoveryProtocol）：
    - 前置 L1 本地正则清洗已由 LocalJsonHealerMiddleware 完成，本插件专注处理复杂格式错乱与字段校验失败。
    - 不匹配故障类型、缺少上下文或修复失败时返回 None，交由责任链下游继续处理或安全降级。
    """

    DEFAULT_SCHEMAS: ClassVar[Dict[str, Type[BaseModel]]] = {
        "IntentResult": IntentResult,
    }

    def __init__(
        self,
        structured_llm: Optional[StructuredLLMProtocol] = None,
        schema_registry: Optional[Dict[str, Type[BaseModel]]] = None,
    ) -> None:
        self._structured_llm = structured_llm
        self._schemas: Dict[str, Type[BaseModel]] = {
            **self.DEFAULT_SCHEMAS,
            **(schema_registry or {}),
        }

    def register_schema(self, schema_cls: Type[BaseModel]) -> "LLMJsonRepairRecovery":
        """支持外部动态注册可修复的 Pydantic Schema"""
        self._schemas[schema_cls.__name__] = schema_cls
        return self

    @staticmethod
    def _strip_think_tags(text: str) -> str:
        if "</think>" in text:
            text = text.split("</think>", 1)[-1]
        return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip()).strip()

    def _build_repair_messages(self, context: FailureContext, schema_cls: Type[BaseModel]) -> List[Dict[str, str]]:
        schema_json = json.dumps(schema_cls.model_json_schema(), ensure_ascii=False)
        clean_raw = self._strip_think_tags(context.raw_output or "")

        system_prompt = (
            "你是一个 JSON 数据修复器。你的唯一任务是将损坏或不合规的模型输出修复为严格符合目标 JSON Schema 的合法 JSON 对象。\n"
            "【严格约束】\n"
            "1. 仅输出单行合法 JSON 字符串，严禁输出任何分析步骤、思考过程或 Markdown 代码块。\n"
            "2. 所有必填字段必须完整提供，数值与类型必须严格匹配 Schema 定义。"
        )
        user_prompt = (
            f"目标 Schema 定义：\n{schema_json}\n\n"
            f"原始用户输入：\n{context.user_query}\n\n"
            f"校验错误信息：\n{context.error_message}\n\n"
            f"待修复的原始输出：\n{clean_raw}\n\n"
            "请直接输出修复后的合法 JSON："
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    async def handle_failure(self, context: FailureContext) -> Optional[RecoveryOutcome]:
        """实现 ExceptionRecoveryProtocol：仅处理 output.* 类故障，无法修复则返回 None"""
        if not context.category.startswith("output."):
            return None

        if self._structured_llm is None or not context.raw_output:
            return None

        schema_cls = self._schemas.get(context.target_schema_name or "")
        if schema_cls is None:
            return None

        try:
            repair_messages = self._build_repair_messages(context, schema_cls)
            raw_call = self._structured_llm.generate_structured(repair_messages, schema_cls)
            repaired = await raw_call if inspect.isawaitable(raw_call) else raw_call

            if isinstance(repaired, schema_cls):
                logger.info("[%s] L2 LLM repair healed.", schema_cls.__name__)
                return RecoveryOutcome(
                    is_recovered=True,
                    recovered_data=repaired,
                    action_taken="json_l2_llm_healed",
                )
        except Exception as llm_err:
            logger.warning("[%s] L2 LLM repair failed: %s", schema_cls.__name__, llm_err)

        # 修复失败交还责任链下游，由 CompositeRecoveryManager 统一输出友好降级话术
        return None
