# /components/internal_knowledge/organization/plugins/info_evaluator.py
import asyncio
import inspect
import logging
import time
from typing import Dict, Hashable, Optional
from pydantic import Field

from infra.quality_evaluator import TwoStageQualityEvaluator, HeuristicRuleFn
from components.internal_knowledge.organization.heuristics import DEFAULT_INFO_HEURISTIC_RULES
from components.internal_knowledge.organization.registry import OrganizationPluginRegistry, OrgStage
from protocols.llm import StructuredLLMProtocol
from infra.quality_evaluator import QualityEvaluatorProtocol
from schemas.base import LLMOutputSchema
from components.internal_knowledge.schemas.information import Information

logger = logging.getLogger(__name__)


class _InfoQualityOutput(LLMOutputSchema):
    """单条切片语义质量评估输出"""

    reason: str = Field(..., description="一句话评估理由（先分析信息密度与业务价值，再给出分数）")
    score: float = Field(..., ge=0.0, le=1.0, description="知识价值密度评分 [0.0, 1.0]")


@OrganizationPluginRegistry.register(OrgStage.EVALUATE, name="heuristic_llm", is_default=True)
class InformationQualityEvaluator(QualityEvaluatorProtocol[Information]):
    """3.1 知识库切片两级评估器：组合第一级协议规则快筛 -> 第二级结构化 LLM 语义打分"""

    def __init__(
        self,
        llm_client: StructuredLLMProtocol,
        min_valid_length: int = 20,
        max_input_chars: int = 2000,
        timeout_seconds: Optional[float] = None,
        extra_rules: Optional[Dict[Hashable, HeuristicRuleFn[Information]]] = None,
    ) -> None:
        self._llm = llm_client
        self._max_input_chars = max_input_chars
        self._timeout_seconds = timeout_seconds

        merged_rules = {**DEFAULT_INFO_HEURISTIC_RULES, **(extra_rules or {})}
        self._engine = TwoStageQualityEvaluator[Information](
            semantic_scorer=self._semantic_score,
            min_valid_length=min_valid_length,
            text_extractor=lambda item: item.information or "",
            routing_key_resolver=lambda item: item.source.scheme if item.source else None,
            heuristic_rules=merged_rules,
        )

    async def evaluate(self, item: Information) -> float:
        """委托给组合的通用两级评估引擎（启发式命中直接返回，未命中进入 LLM 语义打分）"""
        start_ts = time.perf_counter()
        score = await self._engine.evaluate(item)
        elapsed = time.perf_counter() - start_ts
        logger.debug(
            "切片质量评估完成 (info_id=%s, scheme=%s): score=%.2f, 耗时=%.3fs",
            item.info_id,
            item.source.scheme.value if item.source else "none",
            score,
            elapsed,
        )
        return score

    async def _semantic_score(self, item: Information) -> float:
        """第二级语义深度评分（底层超时或调用异常直接向上抛出，交由编排器统一隔离/熔断）"""
        content = (item.information or "")[: self._max_input_chars]
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个知识库质量评估专家。请评估给定信息片段作为长期知识沉淀的价值密度 [0.0, 1.0]。\n"
                    "评分标准：\n"
                    "- 0.0~0.3：无上下文噪声、纯样板配置、无意义寒暄；\n"
                    "- 0.4~0.6：常规业务逻辑实现、一般操作步骤；\n"
                    "- 0.7~1.0：核心架构设计、关键业务规则、故障根因与容错机制。"
                ),
            },
            {
                "role": "user",
                "content": f"主题: {item.topic or '通用'}\n内容:\n{content}",
            },
        ]

        raw_call = self._llm.generate_structured(
            messages=messages,
            response_schema=_InfoQualityOutput,
        )
        coro = raw_call if inspect.isawaitable(raw_call) else asyncio.sleep(0, result=raw_call)
        if self._timeout_seconds is not None:
            result: _InfoQualityOutput = await asyncio.wait_for(coro, timeout=self._timeout_seconds)
        else:
            result = await coro

        clamped_score = max(0.0, min(1.0, float(result.score)))
        logger.debug(
            "LLM 语义打分明细 (info_id=%s): score=%.2f, reason=%s",
            item.info_id,
            clamped_score,
            result.reason.strip(),
        )
        return clamped_score

