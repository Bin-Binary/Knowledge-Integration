# /components/internal_knowledge/organization/info_evaluator.py
import inspect
import re
from typing import Hashable, Optional
from pydantic import Field

from components.evaluation.base_evaluator import BaseQualityEvaluator
from components.internal_knowledge.organization.registry import OrganizationPluginRegistry, OrgStage
from protocols.llm import StructuredLLMProtocol
from schemas.base import LLMOutputSchema
from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.source_uri import SourceScheme


class _InfoQualityOutput(LLMOutputSchema):
    reason: str = Field(..., description="一句话评估理由")
    score: float = Field(..., ge=0.0, le=1.0, description="知识价值密度评分 [0.0, 1.0]")


@OrganizationPluginRegistry.register(OrgStage.EVALUATE, name="llm_hybrid", is_default=True)
class InformationQualityEvaluator(BaseQualityEvaluator[Information]):
    """3.1 知识库切片两级评估器：第一级按协议规则快筛 -> 第二级结构化 LLM 语义打分"""

    def __init__(self, llm_client: StructuredLLMProtocol, min_valid_length: int = 20):
        super().__init__(min_valid_length=min_valid_length)
        self.llm = llm_client

    def _resolve_routing_key(self, item: Information) -> Optional[Hashable]:
        """钩子重写：提取采集源协议枚举作为快筛策略路由键"""
        return item.source.scheme if item.source else None

    async def _semantic_score(self, item: Information) -> float:
        """第二级语义深度评分"""
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个知识库质量评估专家。请评估给定信息片段作为长期知识沉淀的价值密度 [0.0, 1.0]。\n"
                    "0.0~0.3 为无上下文噪声/样板代码；0.4~0.6 为常规实现；0.7~1.0 为核心规则/架构/根因知识。"
                ),
            },
            {
                "role": "user",
                "content": f"主题: {item.topic or '通用'}\n内容:\n{item.information[:2000]}",
            },
        ]
        raw_call = self.llm.generate_structured(
            messages=messages,
            response_schema=_InfoQualityOutput,
        )
        result: _InfoQualityOutput = await raw_call if inspect.isawaitable(raw_call) else raw_call
        return result.score


# 注册各采集协议的第一级零成本快筛策略
@InformationQualityEvaluator.register_heuristic(SourceScheme.REPO, SourceScheme.FILE)
def _heuristic_code_and_file(info: Information) -> Optional[float]:
    lines = [line.strip() for line in info.information.splitlines() if line.strip()]
    if not lines:
        return 0.0
    if all(line.startswith(("import ", "from ", "#", "//", "/*")) for line in lines):
        return 0.1
    return None


@InformationQualityEvaluator.register_heuristic(SourceScheme.CHAT)
def _heuristic_chat(info: Information) -> Optional[float]:
    valid_chars = len(re.findall(r"[\w\u4e00-\u9fa5]", info.information))
    if valid_chars / max(len(info.information), 1) < 0.30:
        return 0.1
    return None


@InformationQualityEvaluator.register_heuristic(SourceScheme.HTTP, SourceScheme.HTTPS)
def _heuristic_web(info: Information) -> Optional[float]:
    text = info.information.lower()
    markers = ("all rights reserved", "copyright ©", "隐私政策", "用户协议")
    if sum(1 for m in markers if m in text) >= 2 and len(text) < 200:
        return 0.1
    return None
