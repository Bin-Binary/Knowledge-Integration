# /components/internal_knowledge/organization/factory.py
import asyncio
from typing import Any, Dict, List, Optional

from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.labeling import Labeling
from schemas.internal_knowledge.relating_concepts import RelatingConcepts
from protocols.internal_knowledge import LabelExtractorProtocol, RelationBuilderProtocol
from components.internal_knowledge.organization.registry import OrganizationPluginRegistry, OrgStage
from components.internal_knowledge.organization.organizer import KnowledgeOrganizer

class _CompositeLabelExtractor(LabelExtractorProtocol):
    """内部复合适配器：并发调度多个 3.2 特征提取器，按 label_id 自动去重合并"""

    def __init__(self, extractors: List[LabelExtractorProtocol]):
        if not extractors:
            raise ValueError("阶段 [3.2_extract] 至少需要激活一个特征提取器")
        self.extractors = extractors

    async def extract(self, info: Information) -> List[Labeling]:
        batches = await asyncio.gather(*(ext.extract(info) for ext in self.extractors))
        merged: Dict[str, Labeling] = {
            lbl.label_id: lbl for batch in batches for lbl in batch
        }
        return list(merged.values())


class _CompositeRelationBuilder(RelationBuilderProtocol):
    """内部复合适配器：并发调度多个 3.3 关系建模器，按 relation_id 去重（保留最高置信度边）"""

    def __init__(self, builders: List[RelationBuilderProtocol]):
        self.builders = builders

    async def build(
        self, labels: List[Labeling], context_infos: List[Information]
    ) -> List[RelatingConcepts]:
        if len(labels) < 2 or not self.builders:
            return []

        batches = await asyncio.gather(
            *(bld.build(labels, context_infos) for bld in self.builders)
        )
        merged: Dict[str, RelatingConcepts] = {}
        for batch in batches:
            for edge in batch:
                existing = merged.get(edge.relation_id)
                if existing is None or (edge.degree or 0.0) > (existing.degree or 0.0):
                    merged[edge.relation_id] = edge
        return list(merged.values())

def build_knowledge_organizer(
    *,
    evaluator_name: Optional[str] = None,          # 不传则自动选 is_default=True 的评估器
    clusterer_name: Optional[str] = None,          # 不传则自动选 is_default=True 的聚类器
    enabled_extractors: Optional[List[str]] = None,# 不传则自动激活所有 3.2 提取器
    enabled_builders: Optional[List[str]] = None,  # 不传则自动激活所有 3.3 建边器
    plugin_kwargs: Optional[Dict[str, Dict[str, Any]]] = None,
    quality_threshold: float = 0.5,
    max_concurrency: int = 5,
) -> KnowledgeOrganizer:
    """一键自动发现并装配四阶知识组织器"""
    # 1. 自动扫描当前 organization 包下的所有插件模块，触发装饰器注册
    OrganizationPluginRegistry.discover("components.internal_knowledge.organization")
    kw = plugin_kwargs or {}

    # 2. 单选阶段仲裁（3.1 评估 & 3.4 聚类）
    evaluator = OrganizationPluginRegistry.resolve_single(
        OrgStage.EVALUATE,
        active_name=evaluator_name,
        init_kwargs=kw.get(evaluator_name or "llm_hybrid"),
    )
    clusterer = OrganizationPluginRegistry.resolve_single(
        OrgStage.CLUSTER,
        active_name=clusterer_name,
        init_kwargs=kw.get(clusterer_name or "connected_component"),
    )

    # 3. 多算子合并阶段装配（3.2 提特征 & 3.3 建边）
    extractors = OrganizationPluginRegistry.resolve_composite(
        OrgStage.EXTRACT, enabled_names=enabled_extractors, kwargs_map=kw
    )
    builders = OrganizationPluginRegistry.resolve_composite(
        OrgStage.RELATE, enabled_names=enabled_builders, kwargs_map=kw
    )

    return KnowledgeOrganizer(
        quality_evaluator=evaluator,
        label_extractor=_CompositeLabelExtractor(extractors),
        relation_builder=_CompositeRelationBuilder(builders),
        ontology_clusterer=clusterer,
        quality_threshold=quality_threshold,
        max_concurrency=max_concurrency,
    )
