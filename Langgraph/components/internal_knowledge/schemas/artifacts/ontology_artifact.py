# /internal_knowledge/schemas/artifacts/ontology_artifact.py
from typing import List, Optional
from pydantic import Field, computed_field, model_validator

from components.internal_knowledge.schemas.artifacts.base import BaseArtifactView
from components.internal_knowledge.schemas.ontology import Ontology


class OntologyArtifact(BaseArtifactView[Ontology]):
    """模板 D：L4 知识闭环体物化视图（宏观架构全景与复杂系统摘要层）"""

    _frontmatter_fields = ("descriptor",)  # 补充 core.descriptor 进 Frontmatter 供宏观标量检索

    # 底部双链收口字段
    evidence_infos: List[str] = Field(default_factory=list, description="支撑该子图的原始切片 ID 集合")
    architecture_ref: str = Field(
        default="Unclassified_Architecture",
        min_length=1,
        description="支撑顶层架构节点",
    )

    # 固定三段式 H2 骨架内容：闭环总结 -> 逻辑拓扑 -> 演进与约束
    title: str = Field(..., min_length=1, description="知识本体闭环体标题")
    one_line_summary: Optional[str] = Field(
        default=None,
        description="首节闭环总结单行摘要（缺省时自动复用 core.descriptor）",
    )
    logical_topology: Optional[str] = Field(default=None, description="逻辑拓扑代码块或结构描述")
    evolution_constraints: List[str] = Field(default_factory=list, description="演进与约束条目列表")

    @computed_field
    @property
    def descriptor(self) -> Optional[str]:
        return self.core.descriptor

    @model_validator(mode="after")
    def _validate_l4_invariants(self) -> "OntologyArtifact":
        self.validate_wiki_id(self.core.complex_id, "ont")
        if not (self.one_line_summary or self.core.descriptor):
            raise ValueError("OntologyArtifact 必须提供 `one_line_summary` 或 `core.descriptor` 作为首节单行总结")
        for lid in self.core.label_ids:
            self.validate_wiki_id(lid, "lbl")
        for rid in self.core.relation_ids:
            self.validate_wiki_id(rid, "rel")
        for iid in self.evidence_infos:
            self.validate_wiki_id(iid, "info")
        return self

    def _render_body(self) -> str:
        summary_text = self.one_line_summary or self.core.descriptor or ""
        sec1 = "\n\n".join([
            "## 闭环总结",
            self.render_single_line_callout("abstract", "一句话总结", summary_text),
        ])

        if self.logical_topology:
            sec2 = f"## 逻辑拓扑\n\n{self.logical_topology.strip()}"
        else:
            nodes_str = "\n".join(f"- [[{lid}]]" for lid in self.core.label_ids)
            rels_str = "\n".join(f"- [[{rid}]]" for rid in self.core.relation_ids)
            sec2 = f"## 逻辑拓扑\n\n### 聚拢节点\n{nodes_str}\n\n### 拓扑语义边\n{rels_str}"

        constraints = self.evolution_constraints or ["核心 Schema 变更需经 release/ 审核后合入"]
        sec3 = "\n".join(["## 演进与约束", *(f"- {c}" for c in constraints)])

        link_rows: List[str] = []
        if self.evidence_infos:
            ev_links = " | ".join(f"[[{iid}]]" for iid in self.evidence_infos)
            link_rows.append(f"**证据切片**：{ev_links}")
        if self.architecture_ref:
            link_rows.append(f"**支撑总纲**：[[{self.architecture_ref}]]")

        return "\n\n".join([
            f"# {self.title}",
            sec1,
            sec2,
            sec3,
            self.build_graph_footer(link_rows),
        ])
