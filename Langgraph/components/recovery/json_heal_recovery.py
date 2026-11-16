# /components/recovery/json_heal_recovery.py
import json
import logging
import re
from typing import Dict, List, Optional, Type
from pydantic import BaseModel

from schemas.recovery import FailureCategory, FailureContext, RecoveryOutcome
from schemas.decision import IntentResult
from components.recovery.base import BaseRecoveryManager
from protocols.llm import StructuredLLMProtocol

logger = logging.getLogger(__name__)

# 匹配 Markdown 代码块 ```json ... ``` 或 ``` ... ```
MARKDOWN_JSON_PATTERN = re.compile(r"```(?:json)?\s*([\s\(\S\)]*?)\s*```", re.IGNORECASE)
# 匹配完整的 <think>...</think> 标签块
THINK_BLOCK_PATTERN = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)

class JsonHealRecoveryManager(BaseRecoveryManager):
    """
    JSON 结构化输出自愈处理器：
    - L1（零延迟本地清洗）：剥离推理模型 <think> 标签、Markdown 代码块，并多起点滑动尝试修复畸形前缀。
    - L2（大模型重写修复）：L1 失败后，携带 Schema 规范与错误详情调用修复模型重写，并对修复输出二次套用 L1 清洗。
    """

    SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = {
        "IntentResult": IntentResult,
    }

    def __init__(self, structured_llm: Optional[StructuredLLMProtocol] = None) -> None:
        self._structured_llm = structured_llm

    def can_handle(self, context: FailureContext) -> bool:
        return (
            context.category in {FailureCategory.VALIDATION_ERROR, FailureCategory.OUTPUT_FORMAT_ERROR}
            and bool(context.raw_output)
            and context.target_schema_name in self.SCHEMA_REGISTRY
        )

    @staticmethod
    def _strip_think_tags(text: str) -> str:
        # 如果包含 </think>，直接截取闭合标签之后的内容
        if "</think>" in text:
            text = text.split("</think>", 1)[-1]
        # 清理可能残留的 Markdown 代码块标记
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
        return text.strip()

    @classmethod
    def _extract_candidate_jsons(cls, raw_text: str) -> List[str]:
        """按优先级生成所有候选 JSON 字符串，兼容头部多余左花括号等畸形前缀"""
        text = cls._strip_think_tags(raw_text)
        candidates: List[str] = []

        # 1. 优先提取 Markdown 代码块中的内容
        md_match = MARKDOWN_JSON_PATTERN.search(text)
        if md_match:
            candidates.append(md_match.group(1).strip())

        # 2. 枚举每一个 '{' 到最后一个 '}' 的切片（自动跳过类似 '{"{"intent":...}' 的头部脏字符）
        end_idx = text.rfind("}")
        if end_idx != -1:
            start_idx = text.find("{")
            while start_idx != -1 and start_idx < end_idx:
                candidate = text[start_idx : end_idx + 1].strip()
                if candidate not in candidates:
                    candidates.append(candidate)
                start_idx = text.find("{", start_idx + 1)

        return candidates

    def _try_l1_heal(self, raw_text: str, schema_cls: Type[BaseModel]) -> Optional[BaseModel]:
        """尝试使用 L1 多起点候选清洗并校验为目标 Schema 实例"""
        for candidate in self._extract_candidate_jsons(raw_text):
            try:
                parsed = json.loads(candidate)
                return schema_cls.model_validate(parsed)
            except Exception:
                continue
        return None

    def _build_repair_messages(self, context: FailureContext, schema_cls: Type[BaseModel]) -> List[Dict[str, str]]:
        """构建 L2 修复提示词消息列表"""
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

    async def _do_recover(self, context: FailureContext) -> RecoveryOutcome:
        schema_cls = self.SCHEMA_REGISTRY.get(context.target_schema_name or "")
        if not schema_cls or not context.raw_output:
            return RecoveryOutcome(is_recovered=False, action_taken="json_heal_missing_context")

        # L1：零成本本地多候选清洗
        healed_l1 = self._try_l1_heal(context.raw_output, schema_cls)
        if healed_l1 is not None:
            logger.info(f"[{schema_cls.__name__}] L1 local strip healed.")
            return RecoveryOutcome(
                is_recovered=True,
                recovered_data=healed_l1,
                action_taken="json_l1_regex_healed",
            )

        # L2：大模型兜底修复（兼容修复模型自身也输出 </think> 思考过程的情况）
        if self._structured_llm is not None:
            try:
                repair_messages = self._build_repair_messages(context, schema_cls)
                repaired = self._structured_llm.generate_structured(repair_messages, schema_cls)
                if isinstance(repaired, schema_cls):
                    logger.info(f"[{schema_cls.__name__}] L2 LLM repair healed.")
                    return RecoveryOutcome(
                        is_recovered=True,
                        recovered_data=repaired,
                        action_taken="json_l2_llm_healed",
                    )
            except Exception as llm_err:
                # 关键加固：如果 L2 修复模型自身也带了 </think> 前缀触发解析异常，用 L1 提取其 raw_output 再抢救一次
                raw_repair_text = getattr(llm_err, "raw_output", "") or str(llm_err)
                healed_l2_l1 = self._try_l1_heal(raw_repair_text, schema_cls)
                if healed_l2_l1 is not None:
                    logger.info(f"[{schema_cls.__name__}] L2 LLM + L1 strip healed.")
                    return RecoveryOutcome(
                        is_recovered=True,
                        recovered_data=healed_l2_l1,
                        action_taken="json_l2_llm_healed",
                    )
                logger.warning(
                    f"[{schema_cls.__name__}] L2 LLM repair failed: {llm_err}"
                )

        return RecoveryOutcome(is_recovered=False, action_taken="json_heal_exhausted")
