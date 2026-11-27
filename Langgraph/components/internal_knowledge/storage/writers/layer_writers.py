# /components/internal_knowledge/storage/writers/layer_writers.py
import re
from typing import Any, Dict, List, Sequence

from components.internal_knowledge.schemas.artifacts import (
    InformationArtifact,
    LabelingArtifact,
    OntologyArtifact,
    RelatingArtifact,
)
from components.internal_knowledge.schemas.information import Information
from components.internal_knowledge.schemas.labeling import Labeling, NodeCategory
from components.internal_knowledge.schemas.ontology import Ontology
from components.internal_knowledge.schemas.relating_concepts import RelatingConcepts
from components.internal_knowledge.schemas.wiki_governance import WikiArtifactLayer
from components.internal_knowledge.storage.writers.base_writer import (
    BaseMarkdownArtifactWriter,
    GraphBatchContext,
)

_CATEGORY_TO_META_TYPE = {
    NodeCategory.ENTITY: "component",
    NodeCategory.CONCEPT: "mechanism",
    NodeCategory.EVENT: "failure_mode",
    NodeCategory.RULE: "principle",
}


class InformationArtifactWriter(BaseMarkdownArtifactWriter[Information]):
    """L1 原始符号切片落盘器（支持增量代码刷新并保留历史提炼概念）"""

    LAYER = WikiArtifactLayer.INFORMATION

    def _get_artifact_id(self, item: Information) -> str:
        return item.info_id

    def _extract_link_updates(self, item: Information, ctx: GraphBatchContext) -> Dict[str, List[str]]:
        return {"提炼概念": ctx.info_to_labels.get(item.info_id, [])}

    def _render_new_markdown(self, item: Information, ctx: GraphBatchContext) -> str:
        art = InformationArtifact(
            core=item,
            trace_id=ctx.trace_id,
            one_line_summary=ctx.info_summaries.get(item.info_id),
            derived_labels=ctx.info_to_labels.get(item.info_id, []),
        )
        return art.to_markdown()

    def _on_debug_file_exists(
        self,
        item: Information,
        existing_md: str,
        link_updates: Dict[str, List[str]],
        ctx: GraphBatchContext,
    ) -> str:
        # 防止直接传 None 会导致旧文件里原本已经生成的业务摘要被抹除
        _OLD_SUMMARY_RE = re.compile(r"^>\s*\[!abstract\]\s*一句话摘要\s*\n>\s*(.+)$", re.MULTILINE)
        # L1 特殊钩子：代码/文档源文件更新时刷新原始切片正文，同时继承合并旧文件的提炼概念与归属架构
        old_links = self.extract_bottom_links(existing_md)
        merged_labels = list(dict.fromkeys([*old_links.get("提炼概念", []), *link_updates.get("提炼概念", [])]))
        arch_refs = old_links.get("归属架构", [])
        arch_ref = arch_refs[-1] if arch_refs else "Unclassified_Architecture"

        summary = ctx.info_summaries.get(item.info_id)
        if not summary:
            m = _OLD_SUMMARY_RE.search(existing_md)
            if m:
                summary = m.group(1).strip()

        art = InformationArtifact(
            core=item,
            trace_id=ctx.trace_id,
            derived_labels=merged_labels,
            one_line_summary=summary,
            architecture_ref=arch_ref,
        )

        return art.to_markdown()


class LabelingArtifactWriter(BaseMarkdownArtifactWriter[Labeling]):
    """L2 概念节点落盘器（多切片同名概念自动收敛并聚合多源语义，已存在时严格只读正文追加双链）"""

    LAYER = WikiArtifactLayer.LABELING

    @staticmethod
    def _extract_rich_semantics(lbl: Labeling) -> Dict[str, Any]:
        """兼容读取公开 rich_semantics 与私有 _rich_semantics"""
        sem = getattr(lbl, "rich_semantics", None)
        if not isinstance(sem, dict):
            sem = getattr(lbl, "_rich_semantics", None)
        return dict(sem) if isinstance(sem, dict) else {}

    def _prepare_items(self, items: Sequence[Labeling]) -> List[Labeling]:
        unique_map: Dict[str, Labeling] = {}
        merged_sem_map: Dict[str, Dict[str, Any]] = {}

        for lbl in items:
            lid = lbl.label_id
            sem = self._extract_rich_semantics(lbl)
            if lid not in unique_map:
                unique_map[lid] = lbl
                merged_sem_map[lid] = {
                    "label_type": sem.get("label_type"),
                    "core_definition": sem.get("core_definition") or "",
                    "trigger_criteria": list(sem.get("trigger_criteria") or []),
                    "boundaries": list(sem.get("boundaries") or []),
                }
            else:
                acc = merged_sem_map[lid]
                if not acc["label_type"] and sem.get("label_type"):
                    acc["label_type"] = sem["label_type"]
                if not acc["core_definition"] and sem.get("core_definition"):
                    acc["core_definition"] = sem["core_definition"]
                acc["trigger_criteria"] = list(
                    dict.fromkeys([*acc["trigger_criteria"], *(sem.get("trigger_criteria") or [])])
                )
                acc["boundaries"] = list(
                    dict.fromkeys([*acc["boundaries"], *(sem.get("boundaries") or [])])
                )

        # 将聚合后的完整语义写回代表节点（兼容不可变模型）
        results: List[Labeling] = []
        for lid, lbl in unique_map.items():
            merged_sem = merged_sem_map[lid]
            if hasattr(lbl, "rich_semantics"):
                lbl = lbl.model_copy(update={"rich_semantics": merged_sem})
            else:
                object.__setattr__(lbl, "_rich_semantics", merged_sem)
            results.append(lbl)
        return results

    def _get_artifact_id(self, item: Labeling) -> str:
        return item.label_id

    def _extract_link_updates(self, item: Labeling, ctx: GraphBatchContext) -> Dict[str, List[str]]:
        # 自动兜底当前 Labeling 自带的 info_id（支持单独调用 L2 落盘而无需构造完整 ctx）
        base_infos = [item.info_id] if item.info_id else []
        infos = list(dict.fromkeys([*base_infos, *ctx.label_to_infos.get(item.label_id, [])]))
        return {
            "溯源切片": infos,
            "发出关系": ctx.label_to_out_rels.get(item.label_id, []),
            "汇聚闭环": ctx.label_to_onts.get(item.label_id, []),
        }

    def _render_new_markdown(self, item: Labeling, ctx: GraphBatchContext) -> str:
        links = self._extract_link_updates(item, ctx)
        sem = self._extract_rich_semantics(item)
        label_type = sem.get("label_type") or _CATEGORY_TO_META_TYPE.get(item.category, "mechanism")

        art = LabelingArtifact(
            core=item,
            label_type=label_type,
            tags=["layer/labeling", f"type/{label_type}"],
            core_definition=sem.get("core_definition") or f"关于 `{item.label}` 的核心领域概念节点。",
            trigger_criteria=sem.get("trigger_criteria") or [],
            boundaries_and_counterexamples=sem.get("boundaries") or [],
            source_infos=links["溯源切片"],
            outgoing_relations=links["发出关系"],
            parent_ontologies=links["汇聚闭环"],
        )
        return art.to_markdown()


class RelatingArtifactWriter(BaseMarkdownArtifactWriter[RelatingConcepts[Any]]):
    """L3 有向语义边落盘器"""

    LAYER = WikiArtifactLayer.RELATING

    def _get_artifact_id(self, item: RelatingConcepts[Any]) -> str:
        return item.relation_id

    def _extract_link_updates(self, item: RelatingConcepts[Any], ctx: GraphBatchContext) -> Dict[str, List[str]]:
        return {"汇聚闭环": ctx.rel_to_onts.get(item.relation_id, [])}

    def _render_new_markdown(self, item: RelatingConcepts[Any], ctx: GraphBatchContext) -> str:
        rel_val = item.relationship_type.value if hasattr(item.relationship_type, "value") else str(item.relationship_type)
        art = RelatingArtifact(
            core=item,
            title=f"{item.label_1_id} → {rel_val} → {item.label_2_id}",
            relation_assertion=f"`{item.label_1_id}` 与 `{item.label_2_id}` 之间存在 `{rel_val}` 语义关联。",
            parent_ontologies=ctx.rel_to_onts.get(item.relation_id, []),
        )
        return art.to_markdown()


class OntologyArtifactWriter(BaseMarkdownArtifactWriter[Ontology]):
    """L4 知识本体闭环体落盘器"""

    LAYER = WikiArtifactLayer.ONTOLOGY

    def _get_artifact_id(self, item: Ontology) -> str:
        return item.complex_id

    def _extract_link_updates(self, item: Ontology, ctx: GraphBatchContext) -> Dict[str, List[str]]:
        evidence_set: List[str] = []
        for lid in item.label_ids:
            for iid in ctx.label_to_infos.get(lid, []):
                if iid not in evidence_set:
                    evidence_set.append(iid)
        return {"证据切片": evidence_set}

    def _render_new_markdown(self, item: Ontology, ctx: GraphBatchContext) -> str:
        links = self._extract_link_updates(item, ctx)
        art = OntologyArtifact(
            core=item,
            title=item.descriptor or f"知识本体 `{item.complex_id}`",
            evidence_infos=links["证据切片"],
        )
        return art.to_markdown()
