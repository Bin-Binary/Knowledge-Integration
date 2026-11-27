# /internal_knowledge/schemas/artifacts/relation_artifact.py
from typing import Any, List
from pydantic import Field, computed_field, model_validator

from schemas.base import DocumentedEnum
from components.internal_knowledge.schemas.artifacts.base import BaseArtifactView
from components.internal_knowledge.schemas.relating_concepts import RelatingConcepts


class StandardRelationVerb(DocumentedEnum):
    """20-wiki 标准化封闭关系动词词表（8 选 1）"""

    ENABLES = ("enables", "使能", "机制或策略 A 为 B 提供前置保障或使其成为可能")
    REQUIRES = ("requires", "依赖", "A 的成立或运行强依赖于 B")
    BLOCKS = ("blocks", "阻塞", "缺陷或状态 A 导致流程或目标 B 无法推进")
    CONFLICTS = ("conflicts", "冲突", "A 与 B 在约束或目标上互斥")
    MITIGATES = ("mitigates", "缓解", "手段 A 降低故障或风险 B 的概率与影响")
    REFINES = ("refines", "细化", "具体实现 A 是抽象机制 B 的工程落地")
    COMPOSED_OF = ("composed_of", "组成", "整体 A 由子模块或要素 B 构成")
    ANALOGOUS_TO = ("analogous_to", "类比", "A 与 B 在结构或机制上具有同构性")


ALLOWED_RELATION_VERBS = {e.value for e in StandardRelationVerb}


class RelatingArtifact(BaseArtifactView[RelatingConcepts[Any]]):
    """模板 C：L3 有向语义边物化视图（多跳因果推理与机制传导桥）"""

    _frontmatter_fields = ("degree",)  # 补充 core.degree 进 Frontmatter 供 [degree>=0.8] 标量过滤

    # 底部双链收口字段
    parent_ontologies: List[str] = Field(default_factory=list, description="所属知识本体闭环体 ID")

    # 固定三段式 H2 骨架内容：关系语义 -> 传导路径 -> 置信度依据
    title: str = Field(..., min_length=1, description="关系标题，如 `背压 → 使能 → 部分持久化`")
    relation_assertion: str = Field(..., min_length=1, description="首节关系语义单行断言")
    propagation_paths: List[str] = Field(default_factory=list, description="传导路径列表")
    confidence_evidence: List[str] = Field(default_factory=list, description="置信度依据列表")

    @computed_field
    @property
    def degree(self) -> float:
        return self.core.degree if self.core.degree is not None else 0.8

    @model_validator(mode="after")
    def _validate_l3_invariants(self) -> "RelatingArtifact":
        self.validate_wiki_id(self.core.relation_id, "rel")
        self.validate_wiki_id(self.core.label_1_id, "lbl")
        self.validate_wiki_id(self.core.label_2_id, "lbl")
        rel_val = (
            self.core.relationship_type.value
            if hasattr(self.core.relationship_type, "value")
            else str(self.core.relationship_type)
        )
        if rel_val not in ALLOWED_RELATION_VERBS:
            raise ValueError(f"关系动词 `{rel_val}` 不在封闭 8 词表内: {sorted(ALLOWED_RELATION_VERBS)}")
        for oid in self.parent_ontologies:
            self.validate_wiki_id(oid, "ont")
        return self

    def _render_body(self) -> str:
        rel_val = (
            self.core.relationship_type.value
            if hasattr(self.core.relationship_type, "value")
            else str(self.core.relationship_type)
        )
        callout_title = f"关系断言（`{rel_val}` / 置信度 {self.degree:g}）"
        sec1 = "\n\n".join([
            "## 关系语义",
            self.render_single_line_callout("note", callout_title, self.relation_assertion),
        ])

        paths = self.propagation_paths or [f"`{self.core.label_1_id}` ➔ `{self.core.label_2_id}`"]
        sec2 = "\n".join(["## 传导路径", *(f"- {p}" for p in paths)])

        evidences = self.confidence_evidence or ["基于上下文共现与结构化语义推理"]
        sec3 = "\n".join(["## 置信度依据", *(f"- {ev}" for ev in evidences)])

        link_rows = [f"**指向目标**：`{self.core.label_1_id}` ➔ [[{self.core.label_2_id}]]"]
        if self.parent_ontologies:
            onts = " | ".join(f"[[{oid}]]" for oid in self.parent_ontologies)
            link_rows.append(f"**汇聚闭环**：{onts}")

        return "\n\n".join([
            f"# {self.title}",
            sec1,
            sec2,
            sec3,
            self.build_graph_footer(link_rows),
        ])
