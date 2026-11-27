# /internal_knowledge/schemas/ontology.py
from typing import List, Optional
from pydantic import Field, field_validator
from schemas.base import ImmutableSchema


class Ontology(ImmutableSchema):
    """Ontology（子图/本体）数据模型：将相关 Labeling 与 RelatingConcepts 聚拢为高内聚知识闭环体。

    FrameNet v17 (Set_of_interrelated_entities) FE 映射:
        - Component_entities -> `label_ids` + `relation_ids`（共同构成完整子图拓扑）
        - Complex            -> `complex_id`
        - Descriptor         -> `descriptor`
        - Possessor          -> [忽略] 不在本模型中表示

    粒度区分说明:
        - `Labeling.label`（微观）：单个原始片段的特征标签（如 <事件：数据库宕机>）。
        - `Ontology.descriptor`（宏观）：整个关系网络的整体定性摘要（如“一次典型的缓存雪崩事故复盘”）。
    """
    complex_id: str = Field(..., min_length=1, description="知识闭环体唯一标识", json_schema_extra={"frontmatter": True})
    label_ids: List[str] = Field(default_factory=list, description="组成该子图的概念节点 ID 集合", json_schema_extra={"frontmatter": True})
    relation_ids: List[str] = Field(
        default_factory=list,
        description="连接上述节点的语义边 ID 集合（多节点子图必填，否则退化为无序集合）",
        json_schema_extra={"frontmatter": True}
    )
    descriptor: Optional[str] = Field(
        default=None,
        description="对该知识闭环体的宏观概括或摘要（用于子图级检索）",
    )

    @field_validator("label_ids", "relation_ids", mode="before")
    @classmethod
    def coerce_none_components_to_list(cls, v: Optional[List[str]]) -> List[str]:
        """容错：将 null 归一化为空列表。"""
        return v if v is not None else []

    def _render_body(self) -> str:
        """渲染带宏观摘要与双链索引的本体知识卡片"""
        title = self.descriptor or f"知识本体 `{self.complex_id}`"
        lines = [f"# {title}", ""]

        if self.descriptor:
            lines.extend([f"> **宏观摘要**: {self.descriptor}", ""])

        lines.append("## 包含概念节点 (Labels)")
        lines.extend(f"- [[{lid}]]" for lid in self.label_ids)
        lines.append("")

        if self.relation_ids:
            lines.append("## 拓扑语义边 (Relations)")
            lines.extend(f"- [[{rid}]]" for rid in self.relation_ids)
            lines.append("")

        return "\n".join(lines)
