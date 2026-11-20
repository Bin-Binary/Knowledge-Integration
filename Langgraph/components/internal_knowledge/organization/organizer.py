# /components/internal_knowledge/organization/organizer.py
import asyncio
import hashlib
from typing import List, Set

from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.labeling import Labeling
from schemas.internal_knowledge.ontology import Ontology
from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope
from schemas.internal_knowledge.relating_concepts import RelatingConcepts
from protocols.evaluation import QualityEvaluatorProtocol
from protocols.internal_knowledge import (
    KnowledgeOrganizationProtocol,
    LabelExtractorProtocol,
    RelationBuilderProtocol,
    OntologyClustererProtocol,
)


class KnowledgeOrganizer(KnowledgeOrganizationProtocol):
    """3. 【组织】环节统一编排器（基于微算子组合模式，零继承负担）。

    核心职能：
        1. 通过依赖注入聚合 3.1~3.4 四个正交微算子，彻底消除抽象基类与子类重写样板代码。
        2. 统一控制异步并发限流（Semaphore）、前置条数校验（>=2 才建边）及悬空边拓扑清洗。
        3. 不可变地将四阶加工产物追加回 PipelineEnvelope。
    """

    def __init__(
        self,
        quality_evaluator: QualityEvaluatorProtocol[Information],
        label_extractor: LabelExtractorProtocol,
        relation_builder: RelationBuilderProtocol,
        ontology_clusterer: OntologyClustererProtocol,
        quality_threshold: float = 0.5,
        max_concurrency: int = 5,
    ):
        if not (0.0 <= quality_threshold <= 1.0):
            raise ValueError("quality_threshold 必须在 [0.0, 1.0] 区间内")
        if max_concurrency < 1:
            raise ValueError("max_concurrency 必须 >= 1")

        self.quality_evaluator = quality_evaluator
        self.label_extractor = label_extractor
        self.relation_builder = relation_builder
        self.ontology_clusterer = ontology_clusterer
        self.quality_threshold = quality_threshold
        self.max_concurrency = max_concurrency

    @staticmethod
    def generate_deterministic_id(prefix: str, semantic_key: str) -> str:
        """公共静态工具：供各微算子生成规范化确定性 ID（如 lbl_a1b2c3d4e5f6）"""
        normalized = semantic_key.strip().lower()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
        return f"{prefix}_{digest}"

    async def organize(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """端到端异步四阶加工流水线"""
        if not envelope.raw_infos:
            return envelope

        semaphore = asyncio.Semaphore(self.max_concurrency)

        # 3.1 并发评估过滤
        async def _eval_one(info: Information) -> tuple[Information, float]:
            async with semaphore:
                return info, await self.quality_evaluator.evaluate(info)

        scored = await asyncio.gather(*(_eval_one(info) for info in envelope.raw_infos))
        valid_infos: List[Information] = [
            info for info, score in scored if score >= self.quality_threshold
        ]
        if not valid_infos:
            return envelope

        # 3.2 并发特征提取
        async def _extract_one(info: Information) -> List[Labeling]:
            async with semaphore:
                return await self.label_extractor.extract(info)

        label_batches = await asyncio.gather(*(_extract_one(info) for info in valid_infos))
        # 跨切片同名概念节点的确定性去重
        merged_labels_map = {
            lbl.label_id: lbl for batch in label_batches for lbl in batch
        }
        extracted_labels: List[Labeling] = list(merged_labels_map.values())
        if not extracted_labels:
            return envelope

        # 3.3 关系建模（前置约束 >= 2 个节点 + 悬空边清洗）
        extracted_relations: List[RelatingConcepts] = []
        if len(extracted_labels) >= 2:
            raw_relations = await self.relation_builder.build(extracted_labels, valid_infos)
            valid_label_ids: Set[str] = {lbl.label_id for lbl in extracted_labels}
            extracted_relations = [
                rel for rel in raw_relations
                if rel.label_1_id in valid_label_ids and rel.label_2_id in valid_label_ids
            ]

        # 3.4 本体聚拢
        extracted_complexes: List[Ontology] = await self.ontology_clusterer.cluster(
            extracted_labels, extracted_relations
        )

        return envelope.model_copy(
            update={
                "labels": [*envelope.labels, *extracted_labels],
                "relations": [*envelope.relations, *extracted_relations],
                "complexes": [*envelope.complexes, *extracted_complexes],
            }
        )
