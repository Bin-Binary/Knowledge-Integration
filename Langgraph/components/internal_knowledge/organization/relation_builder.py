# /components/internal_knowledge/organization/relation_builder.py
from typing import Dict, List, Type
from pydantic import Field

from schemas.base import DocumentedEnum, LLMOutputSchema
from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.labeling import Labeling
from schemas.internal_knowledge.relating_concepts import GeneralRelationType, RelatingConcepts
from protocols.llm import StructuredLLMProtocol
from protocols.internal_knowledge import RelationBuilderProtocol
from components.internal_knowledge.organization.organizer import KnowledgeOrganizer
from components.internal_knowledge.organization.registry import OrganizationPluginRegistry, OrgStage

class _RelationEdgeItem(LLMOutputSchema):
    source_label_id: str = Field(..., description="起点概念节点 ID（必须严格来自给定候选列表）")
    target_label_id: str = Field(..., description="终点概念节点 ID（必须严格来自给定候选列表）")
    relation_type: str = Field(..., description="关系枚举值（必须严格匹配给定关系字典中的 value）")
    degree: float = Field(default=0.8, ge=0.0, le=1.0, description="语义关联置信度 [0.0, 1.0]")

class _RelationBatchOutput(LLMOutputSchema):
    edges: List[_RelationEdgeItem] = Field(
        default_factory=list,
        description="推导出的高置信度有向语义边列表",
    )

@OrganizationPluginRegistry.register(OrgStage.RELATE, name="llm_relation", is_default=True)
class LLMRelationBuilder(RelationBuilderProtocol):
    """3.3 基于结构化大模型的关系建模算子（支持动态注入领域关系枚举）"""

    def __init__(
        self,
        llm_client: StructuredLLMProtocol,
        relation_enum_cls: Type[DocumentedEnum] = GeneralRelationType,
        min_confidence: float = 0.6,
    ):
        self.llm = llm_client
        self.relation_enum_cls = relation_enum_cls
        self.min_confidence = min_confidence

    async def build(
        self, labels: List[Labeling], context_infos: List[Information]
    ) -> List[RelatingConcepts]:
        if len(labels) < 2:
            return []

        # 1. 自动调用 DocumentedEnum.to_prompt_guide() 生成自省枚举说明书
        relation_guide = self.relation_enum_cls.to_prompt_guide()
        nodes_catalog = "\n".join(f"- `{lbl.label_id}`: {lbl.label}" for lbl in labels)
        context_summary = "\n---\n".join(info.information[:800] for info in context_infos[:10])

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个知识图谱关系推理专家。请根据候选概念节点列表及原始上下文，推导节点间的有向语义关系。\n"
                    f"允许使用的关系类型字典（必须严格输出反引号内的英文 value）：\n{relation_guide}\n"
                    "注意：严禁捏造不在候选列表中的节点 ID，严禁自环（起点与终点相同）。"
                ),
            },
            {
                "role": "user",
                "content": f"### 候选概念节点列表：\n{nodes_catalog}\n\n### 原始上下文参考：\n{context_summary}",
            },
        ]

        result: _RelationBatchOutput = await self.llm.generate_structured(
            messages=messages,
            response_schema=_RelationBatchOutput,
        )

        # 建立合法枚举值映射表
        valid_enum_map: Dict[str, DocumentedEnum] = {e.value: e for e in self.relation_enum_cls}
        relations: List[RelatingConcepts] = []
        seen_rel_ids: set[str] = set()

        for edge in result.edges:
            if edge.degree < self.min_confidence:
                continue
            if edge.source_label_id == edge.target_label_id:
                continue
            rel_enum = valid_enum_map.get(edge.relation_type.strip())
            if not rel_enum:
                continue

            # 基于 (起点 + 关系类型 + 终点) 生成确定性 relation_id
            sig = f"{edge.source_label_id}->{rel_enum.value}->{edge.target_label_id}"
            rel_id = KnowledgeOrganizer.generate_deterministic_id("rel", sig)
            if rel_id in seen_rel_ids:
                continue
            seen_rel_ids.add(rel_id)

            relations.append(
                RelatingConcepts(
                    relation_id=rel_id,
                    label_1_id=edge.source_label_id,
                    label_2_id=edge.target_label_id,
                    relationship_type=rel_enum,
                    degree=edge.degree,
                )
            )

        return relations
