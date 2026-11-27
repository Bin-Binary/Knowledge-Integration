# /internal_knowledge/schemas/artifacts/label_artifact.py
import re
from typing import List, Literal, Optional, Union
from pydantic import Field, model_validator

from components.internal_knowledge.schemas.artifacts.base import BaseArtifactView
from components.internal_knowledge.schemas.labeling import Labeling

# L2 概念元类型受控词表（6 选 1）
LabelMetaType = Literal["mechanism", "component", "principle", "failure_mode", "metric", "workflow"]


class LabelingArtifact(BaseArtifactView[Labeling]):
    """模板 B：L2 概念节点物化视图（下游语义检索的主力索引层）"""

    label_type: LabelMetaType = Field(
        ...,
        description="L2 概念元类型受控词表（6 选 1）",
        json_schema_extra={"frontmatter": True},
    )
    confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="概念抽取置信度 [0.0, 1.0]",
        json_schema_extra={"frontmatter": True},
    )
    tags: List[Union[str, "dict"]] = Field(
        default_factory=list,
        description="三级分段时间戳标签（layer/domain/topic/type）",
        json_schema_extra={"frontmatter": True},
    )

    # 底部图谱双链收口字段（不写入 YAML，由检索器正则解析做 GraphRAG 扩展）
    source_infos: List[str] = Field(default_factory=list, description="聚合所有提及该概念的原始切片 ID")
    outgoing_relations: List[str] = Field(default_factory=list, description="从该节点发出的有向语义边 ID")
    parent_ontologies: List[str] = Field(default_factory=list, description="所属知识本体闭环体 ID")

    # 固定三段式 H2 骨架内容：核心定义 -> 触发判据 -> 边界与反例
    display_title: Optional[str] = Field(default=None, description="可选显示标题（默认自动解析 core.label）")
    core_definition: str = Field(..., min_length=1, description="首节一句话判据（强制单行渲染）")
    definition_detail: Optional[str] = Field(default=None, description="核心定义补充说明或对比表")
    trigger_criteria: List[str] = Field(default_factory=list, description="触发判据列表")
    boundaries_and_counterexamples: List[str] = Field(default_factory=list, description="边界与反例列表")

    @model_validator(mode="after")
    def _validate_l2_invariants(self) -> "LabelingArtifact":
        self.validate_wiki_id(self.core.label_id, "lbl")
        if self.core.label_id.endswith(("_concept", "_node")):
            raise ValueError(f"L2 ID `{self.core.label_id}` 禁止带 `_concept` 或 `_node` 冗余后缀")
        for iid in self.source_infos:
            self.validate_wiki_id(iid, "info")
        for rid in self.outgoing_relations:
            self.validate_wiki_id(rid, "rel")
        for oid in self.parent_ontologies:
            self.validate_wiki_id(oid, "ont")
        return self

    def _resolve_title(self) -> str:
        if self.display_title:
            return self.display_title.strip()
        match = re.match(r"^<[^：:]+[：:](.+)>$", self.core.label.strip())
        return match.group(1).strip() if match else self.core.label

    def _render_body(self) -> str:
        sec1_parts = [
            "## 核心定义",
            self.render_single_line_callout("quote", "一句话判据", self.core_definition),
        ]
        if self.definition_detail:
            sec1_parts.append(self.definition_detail.strip())

        criteria = self.trigger_criteria or ["待补充触发阈值与观测条件"]
        sec2 = "\n".join(["## 触发判据", *(f"- {item}" for item in criteria)])

        boundaries = self.boundaries_and_counterexamples or ["仅适用于通用领域抽象，排除单次偶发堆栈"]
        sec3 = "\n".join(["## 边界与反例", *(f"- {item}" for item in boundaries)])

        sections = [
            f"# {self._resolve_title()}",
            "\n\n".join(sec1_parts),
            sec2,
            sec3,
        ]

        link_rows: List[str] = []
        if self.source_infos:
            infos = " | ".join(f"[[{iid}]]" for iid in self.source_infos)
            link_rows.append(f"**溯源切片**：{infos}")
        if self.outgoing_relations:
            rels = " | ".join(f"[[{rid}]]" for rid in self.outgoing_relations)
            link_rows.append(f"**发出关系**：{rels}")
        if self.parent_ontologies:
            onts = " | ".join(f"[[{oid}]]" for oid in self.parent_ontologies)
            link_rows.append(f"**汇聚闭环**：{onts}")

        footer = self.build_graph_footer(link_rows)
        if footer:
            sections.append(footer)
        return "\n\n".join(sections)
