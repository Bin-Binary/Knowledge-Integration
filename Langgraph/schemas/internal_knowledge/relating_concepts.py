# /schemas/internal_knowledge/relating_concepts.py
from typing import Generic, Optional, TypeVar
from pydantic import Field, model_validator
from schemas.base import ImmutableSchema, DocumentedEnum

class GeneralRelationType(DocumentedEnum):
    """通用语义关系（核心层只保留领域无关的通用边）"""
    CAUSAL = ("causal", "通用语义", "因果关系（A 导致 B）")
    IS_A = ("is_a", "通用语义", "继承/分类关系（A 是一种 B）")
    PART_OF = ("part_of", "通用语义", "组成/包含关系（A 是 B 的一部分）")
    PRECEDES = ("precedes", "通用语义", "时序/前置关系（A 发生在 B 之前）")
    ASSOCIATED_WITH = ("associated", "通用语义", "通用弱关联")

# 定义泛型变量，约束必须是 DocumentedEnum 的子类
RelTypeT = TypeVar("RelTypeT", bound=DocumentedEnum)

class RelatingConcepts(ImmutableSchema, Generic[RelTypeT]):
    """基于标签（Labeling）构建概念间网络结构，形成可推理的有向关系边"""

    relation_id: str = Field(..., min_length=1, description="语义边全局唯一标识", json_schema_extra={"frontmatter": True})
    label_1_id: str = Field(..., min_length=1, description="有向边的起点概念节点 ID（Concept_1）", json_schema_extra={"frontmatter": True})
    label_2_id: str = Field(..., min_length=1, description="有向边的终点概念节点 ID（Concept_2）", json_schema_extra={"frontmatter": True})
    
    # 默认支持通用关系，具体领域可通过 RelatingConcepts[CodeRelationType] 注入专属枚举
    relationship_type: RelTypeT = Field(..., description="有向边的关系类型", json_schema_extra={"frontmatter": True})
    degree: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="关联强度或置信度 [0.0, 1.0]")

    @model_validator(mode="after")
    def prevent_self_loop(self) -> "RelatingConcepts[RelTypeT]":
        """结构不变式校验：禁止节点指向自身的无效自环边"""
        if self.label_1_id == self.label_2_id:
            raise ValueError(f"语义边不允许自环: label_1_id 与 label_2_id 均为 {self.label_1_id}")
        return self

    def _render_body(self) -> str:
        """重写正文渲染钩子：生成兼顾人类阅读与 Obsidian 双链的图谱关系描述"""
        rel_val = self.relationship_type.value if hasattr(self.relationship_type, "value") else self.relationship_type
        degree_str = f" (置信度: `{self.degree:.2f}`)" if self.degree is not None else ""
        return (
            f"# 语义关系边 `{self.relation_id}`\n\n"
            f"- **拓扑连接**: [[{self.label_1_id}]] ➔ **`{rel_val}`** ➔ [[{self.label_2_id}]]{degree_str}"
        )
