# /components/internal_knowledge/organization/base_organization.py
import asyncio
import hashlib
from abc import ABC, abstractmethod
from typing import List, Set

from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.labeling import Labeling
from schemas.internal_knowledge.ontology import Ontology
from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope
from schemas.internal_knowledge.relating_concepts import RelatingConcepts
from protocols.internal_knowledge import KnowledgeOrganizationProtocol

class BaseKnowledgeOrganizer(ABC, KnowledgeOrganizationProtocol):
    """3. 【组织】环节抽象基类（实现 KnowledgeOrganizationProtocol）。

    核心职能：
        1. 固化四阶信息密度递增加工模板：3.1 评估过滤 -> 3.2 提取特征 -> 3.3 关系建模 -> 3.4 本体聚拢。
        2. 利用异步并发（Semaphore 限流）加速批量切片的评分与特征提取。
        3. 提供图拓扑完整性清洗与确定性 ID 生成工具，保障下游落盘质量。
    """

    def __init__(self, quality_threshold: float = 0.5, max_concurrency: int = 5):
        """
        Args:
            quality_threshold: 信息质量过滤阈值 [0.0, 1.0]，低于该分值的片段将被丢弃。
            max_concurrency: 并发执行评分与特征抽取的最大协程数（防止触发 LLM 限流）。
        """
        if not (0.0 <= quality_threshold <= 1.0):
            raise ValueError("quality_threshold 必须在 [0.0, 1.0] 区间内")
        if max_concurrency < 1:
            raise ValueError("max_concurrency 必须 >= 1")

        self.quality_threshold = quality_threshold
        self.max_concurrency = max_concurrency

    # ------------------------------------------------------------------
    # 通用确定性 ID 工具（保障跨切片概念对齐，避免重复建点）
    # ------------------------------------------------------------------

    @staticmethod
    def generate_deterministic_id(prefix: str, semantic_key: str) -> str:
        """基于规范化语义键生成确定性 ID（如 lbl_a1b2c3d4e5f6）"""
        normalized = semantic_key.strip().lower()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
        return f"{prefix}_{digest}"

    # ------------------------------------------------------------------
    # 核心四阶加工模板方法
    # ------------------------------------------------------------------

    async def organize(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """端到端异步四阶加工模板方法：读取 raw_infos -> 并发加工 -> 拓扑清洗 -> 写入信封"""
        if not envelope.raw_infos:
            return envelope

        semaphore = asyncio.Semaphore(self.max_concurrency)

        # 3.1 并发评估过滤：剔除低质噪声片段
        async def _eval_one(info: Information) -> tuple[Information, float]:
            async with semaphore:
                score = await self._score_quality(info)
                return info, score

        scored_results = await asyncio.gather(*(_eval_one(info) for info in envelope.raw_infos))
        valid_infos: List[Information] = [
            info for info, score in scored_results if score >= self.quality_threshold
        ]
        if not valid_infos:
            return envelope

        # 3.2 并发提取特征：抽取可检索概念节点
        async def _extract_one(info: Information) -> List[Labeling]:
            async with semaphore:
                return await self._extract_labels(info)

        label_batches = await asyncio.gather(*(_extract_one(info) for info in valid_infos))
        extracted_labels: List[Labeling] = [
            lbl for batch in label_batches for lbl in batch
        ]
        if not extracted_labels:
            return envelope

        # 3.3 关系建模：严格遵守前置约束（概念节点条数 >= 2 才建边）
        extracted_relations: List[RelatingConcepts] = []
        if len(extracted_labels) >= 2:
            raw_relations = await self._build_relations(extracted_labels, valid_infos)
            # 防御性清洗：过滤掉引用了不存在节点 ID 的悬空边
            valid_label_ids: Set[str] = {lbl.label_id for lbl in extracted_labels}
            extracted_relations = [
                rel for rel in raw_relations
                if rel.label_1_id in valid_label_ids and rel.label_2_id in valid_label_ids
            ]

        # 3.4 本体聚拢：将离散节点与有向边聚拢为高内聚知识闭环体
        extracted_complexes: List[Ontology] = await self._cluster_ontology(
            extracted_labels, extracted_relations
        )

        return envelope.model_copy(
            update={
                "labels": [*envelope.labels, *extracted_labels],
                "relations": [*envelope.relations, *extracted_relations],
                "complexes": [*envelope.complexes, *extracted_complexes],
            }
        )

    @abstractmethod
    async def _score_quality(self, info: Information) -> float:
        """3.1 评估过滤：异步评估单条原始信息片段的价值密度，返回 [0.0, 1.0] 标量分值。"""
        ...

    @abstractmethod
    async def _extract_labels(self, info: Information) -> List[Labeling]:
        """3.2 提取特征：从单条有效信息中异步抽取出概念节点列表。"""
        ...

    @abstractmethod
    async def _build_relations(
        self, labels: List[Labeling], context_infos: List[Information]
    ) -> List[RelatingConcepts]:
        """3.3 关系建模：基于已提取的概念节点集合（>=2条）异步推导有向语义边。"""
        ...

    @abstractmethod
    async def _cluster_ontology(
        self, labels: List[Labeling], relations: List[RelatingConcepts]
    ) -> List[Ontology]:
        """3.4 本体聚拢：将概念节点与关系网络异步聚拢成结构化知识闭环体（Ontology）。"""
        ...
