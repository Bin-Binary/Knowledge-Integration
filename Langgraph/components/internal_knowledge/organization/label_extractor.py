# /components/internal_knowledge/organization/label_extractor.py
import time
from typing import List
from pydantic import Field

from schemas.base import LLMOutputSchema
from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.labeling import Labeling
from protocols.llm import StructuredLLMProtocol
from protocols.internal_knowledge import LabelExtractorProtocol
from components.internal_knowledge.organization.organizer import KnowledgeOrganizer
from components.internal_knowledge.organization.registry import OrganizationPluginRegistry, OrgStage

class _ExtractedConceptItem(LLMOutputSchema):
    concept_tag: str = Field(
        ...,
        description="结构化特征分类标签，格式如 '<实体：Redis>'、'<事件：数据库宕机>'、'<机制：依赖倒置>'",
    )

class _LabelBatchOutput(LLMOutputSchema):
    concepts: List[_ExtractedConceptItem] = Field(
        default_factory=list,
        description="从信息片段中提炼出的核心可检索概念节点集合（去重、高信息密度）",
    )

@OrganizationPluginRegistry.register(OrgStage.EXTRACT, name="llm_label", is_default=True)
class LLMLabelExtractor(LabelExtractorProtocol):
    """3.2 基于结构化大模型的概念节点提取器（实现 LabelExtractorProtocol）"""

    def __init__(self, llm_client: StructuredLLMProtocol):
        self.llm = llm_client

    async def extract(self, info: Information) -> List[Labeling]:
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个知识图谱概念抽取专家。请从给定信息片段中提炼核心可检索概念节点。\n"
                    "要求：\n"
                    "1. 标签格式统一为 `<分类：规范化名称>`，例如 `<实体：Redis>`、`<设计模式：黑板模式>`、`<事件：缓存雪崩>`。\n"
                    "2. 同义词请归一化为标准名称，避免提取无意义的泛化词（如 `<实体：代码>`、`<实体：系统>`）。"
                ),
            },
            {
                "role": "user",
                "content": f"主题: {info.topic or '通用'}\n片段内容:\n{info.information}",
            },
        ]

        result: _LabelBatchOutput = await self.llm.generate_structured(
            messages=messages,
            response_schema=_LabelBatchOutput,
        )

        now_ts = time.time()
        labels: List[Labeling] = []
        seen_ids: set[str] = set()

        for item in result.concepts:
            clean_tag = item.concept_tag.strip()
            if not clean_tag:
                continue
            # 基于规范化标签生成确定性 ID：不同切片提取出相同概念时，自动收敛为同一个 label_id
            lbl_id = KnowledgeOrganizer.generate_deterministic_id("lbl", clean_tag)
            if lbl_id in seen_ids:
                continue
            seen_ids.add(lbl_id)

            labels.append(
                Labeling(
                    label_id=lbl_id,
                    info_id=info.info_id,
                    label=clean_tag,
                    timestamp=now_ts,
                )
            )

        return labels
