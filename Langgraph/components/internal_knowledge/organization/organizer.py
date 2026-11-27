# /components/internal_knowledge/organization/organizer.py
import asyncio
import hashlib
import logging
import time
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple

from components.internal_knowledge.schemas.artifacts import build_compliant_artifact_id
from components.internal_knowledge.schemas.information import Information
from components.internal_knowledge.schemas.labeling import Labeling
from components.internal_knowledge.schemas.ontology import Ontology
from components.internal_knowledge.schemas.pipeline_envelope import PipelineEnvelope
from components.internal_knowledge.schemas.relating_concepts import RelatingConcepts
from protocols.evaluation import QualityEvaluatorProtocol
from components.internal_knowledge.protocols import (
    KnowledgeOrganizationProtocol,
    LabelExtractorProtocol,
    RelationBuilderProtocol,
    OntologyClustererProtocol,
)
from infra import emit_component_status
from infra.exceptions import KnowledgePipelineError

logger = logging.getLogger(__name__)


class KnowledgeOrganizer(KnowledgeOrganizationProtocol):
    """3. 【组织】环节统一编排器

    职责闭环：
    - 3.1 信息密度评估过滤（单条异常隔离 + 阈值门控）
    - 3.2 并发特征提取（全量切片归属保留 + 独立节点去重）
    - P1-1 背压规模门控（按跨切片频次采样 Top-K，保留全量出现记录供关系推理）
    - 3.3 关系建模 & 3.4 本体聚拢（阶段超时控制 + P1-2 部分持久化异常兜底）
    - 产物幂等合并写回 PipelineEnvelope
    """

    def __init__(
        self,
        quality_evaluator: QualityEvaluatorProtocol[Information],
        label_extractor: LabelExtractorProtocol,
        relation_builder: RelationBuilderProtocol,
        ontology_clusterer: OntologyClustererProtocol,
        quality_threshold: float = 0.5,
        max_concurrency: int = 5,
        max_labels_for_relation: int = 50,
        stage_timeout_seconds: Optional[float] = None,
        relation_window_timeout_seconds: Optional[float] = None,
    ):
        if not (0.0 <= quality_threshold <= 1.0):
            raise ValueError("quality_threshold 必须在 [0.0, 1.0] 区间内")
        if max_concurrency < 1:
            raise ValueError("max_concurrency 必须 >= 1")
        if max_labels_for_relation < 2:
            raise ValueError("max_labels_for_relation 必须 >= 2")
        if stage_timeout_seconds is not None and stage_timeout_seconds <= 0:
            raise ValueError("stage_timeout_seconds 必须 > 0")
        if relation_window_timeout_seconds is not None and relation_window_timeout_seconds <= 0:
            raise ValueError("relation_window_timeout_seconds 必须 > 0")

        self.quality_evaluator = quality_evaluator
        self.label_extractor = label_extractor
        self.relation_builder = relation_builder
        self.ontology_clusterer = ontology_clusterer
        self.quality_threshold = quality_threshold
        self.max_concurrency = max_concurrency
        self.max_labels_for_relation = max_labels_for_relation
        self.stage_timeout_seconds = stage_timeout_seconds
        self.relation_window_timeout_seconds = relation_window_timeout_seconds

    @staticmethod
    def generate_deterministic_id(
        prefix: str,
        semantic_key: str,
        semantic_slug: Optional[str] = None,
    ) -> str:
        """统一确定性 ID 生成器：优先生成 `语义主干_4位指纹` 闭合 ID；无 slug 时退化为 12 位哈希。"""
        if semantic_slug and prefix in ("info", "lbl", "rel", "ont"):
            return build_compliant_artifact_id(
                prefix=prefix,  # type: ignore[arg-type]
                semantic_slug=semantic_slug,
                fingerprint_seed=semantic_key,
            )
        normalized = semantic_key.strip().lower()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
        return f"{prefix}_{digest}"

    async def _run_with_stage_timeout(self, coro, stage_name: str, trace_id: str):
        """统一阶段超时包装器，超时后转换为标准业务异常供恢复节点捕获"""
        if self.stage_timeout_seconds is None:
            return await coro
        try:
            return await asyncio.wait_for(coro, timeout=self.stage_timeout_seconds)
        except asyncio.TimeoutError as exc:
            logger.error(
                "[KnowledgeOrganizer] 阶段 [%s] 执行超时 (trace_id=%s, timeout=%.1fs)",
                stage_name,
                trace_id,
                self.stage_timeout_seconds,
            )
            raise KnowledgePipelineError(
                message=f"知识组织阶段 [{stage_name}] 执行超时（>{self.stage_timeout_seconds}s）",
                stage="organization",
                user_friendly_hint="知识图谱整理耗时过长，系统正在尝试自动恢复或简化处理。",
                metadata={
                    "trace_id": trace_id,
                    "sub_stage": stage_name,
                    "timeout_seconds": self.stage_timeout_seconds,
                },
            ) from exc


    async def organize(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """端到端异步四阶加工流水线"""
        if not envelope.raw_infos:
            logger.info("[KnowledgeOrganizer] 输入 raw_infos 为空，跳过组织阶段 (trace_id=%s)", envelope.trace_id)
            return envelope

        pipeline_start = time.perf_counter()
        total_raw = len(envelope.raw_infos)
        semaphore = asyncio.Semaphore(self.max_concurrency)
        logger.info(
            "[KnowledgeOrganizer] 启动知识组织流水线 (trace_id=%s, raw_infos=%d, threshold=%.2f, concurrency=%d)",
            envelope.trace_id,
            total_raw,
            self.quality_threshold,
            self.max_concurrency,
        )

        # =========================================================================
        # 3.1 & 3.2 前置核心阶段：发生超时或未预期系统异常时，抛出 KnowledgePipelineError 交由恢复节点处理
        # =========================================================================
        try:
            # --- 3.1 并发评估过滤 ---
            stage_t0 = time.perf_counter()

            async def _eval_one(info: Information) -> Tuple[Information, float]:
                async with semaphore:
                    try:
                        score = await self.quality_evaluator.evaluate(info)
                        return info, score
                    except Exception:
                        logger.exception(
                            "[KnowledgeOrganizer] 单条切片质量评估异常，已降级丢弃 (trace_id=%s, info_id=%s)",
                            envelope.trace_id,
                            info.info_id,
                        )
                        return info, -1.0

            emit_component_status(f" [评估过滤] 正在对 {total_raw} 条切片进行信息密度评分...\n")
            scored = await self._run_with_stage_timeout(
                asyncio.gather(*(_eval_one(info) for info in envelope.raw_infos)),
                stage_name="3.1_quality_evaluation",
                trace_id=envelope.trace_id,
            )
            valid_infos: List[Information] = [
                info for info, score in scored if score >= self.quality_threshold
            ]
            if not valid_infos:
                emit_component_status(f"[评估完成]: 0/{total_raw} 条切片达到质量阈值，终止本轮图谱加工。\n")
                return envelope

            emit_component_status(f"[评估完成]: 保留 {len(valid_infos)}/{total_raw} 条高价值切片。\n")

            # --- 3.2 并发特征提取 ---
            stage_t0 = time.perf_counter()

            async def _extract_one(info: Information) -> List[Labeling]:
                async with semaphore:
                    try:
                        return await self.label_extractor.extract(info)
                    except Exception:
                        logger.exception(
                            "[KnowledgeOrganizer] 单条切片特征提取异常，已跳过 (trace_id=%s, info_id=%s)",
                            envelope.trace_id,
                            info.info_id,
                        )
                        return []

            emit_component_status(f"[特征提取]：正在从 {len(valid_infos)} 条有效切片中并行抽取概念节点...\n")
            label_batches = await self._run_with_stage_timeout(
                asyncio.gather(*(_extract_one(info) for info in valid_infos)),
                stage_name="3.2_label_extraction",
                trace_id=envelope.trace_id,
            )
        except KnowledgePipelineError:
            raise
        except Exception as exc:
            logger.exception(
                "[KnowledgeOrganizer] 前置特征提取阶段发生系统性异常 (trace_id=%s)",
                envelope.trace_id,
            )
            raise KnowledgePipelineError(
                message=f"知识概念提取阶段异常中断: {exc}",
                stage="organization",
                user_friendly_hint="在提取文档核心概念时遇到服务波动，正在调度异常恢复。",
                metadata={"trace_id": envelope.trace_id, "error_type": type(exc).__name__},
            ) from exc

        all_extracted_labels: List[Labeling] = [
            lbl for batch in label_batches for lbl in batch
        ]

        extract_elapsed = time.perf_counter() - stage_t0

        if not all_extracted_labels:
            logger.info(
                "[KnowledgeOrganizer] 3.2 特征提取完成但未产出概念节点 (trace_id=%s, 耗时=%.2fs)",
                envelope.trace_id,
                extract_elapsed,
            )
            emit_component_status(
                " [特征提取]：未提取出有效概念节点，跳过后续建边与聚类。\n",
            )
            return envelope

        freq_counter: Counter[str] = Counter(lbl.label_id for lbl in all_extracted_labels)
        unique_labels_map: Dict[str, Labeling] = {}
        for lbl in all_extracted_labels:
            unique_labels_map.setdefault(lbl.label_id, lbl)

        unique_labels: List[Labeling] = list(unique_labels_map.values())
        logger.info(
            "[KnowledgeOrganizer] 3.2 特征提取完成 (trace_id=%s): 耗时=%.2fs, 原始标注=%d, 独立概念节点=%d",
            envelope.trace_id,
            extract_elapsed,
            len(all_extracted_labels),
            len(unique_labels),
        )
        emit_component_status(
            f" [特征提取]：共提取 {len(all_extracted_labels)} 条标注（去重后 {len(unique_labels)} 个独立概念节点）。\n",
        )

        # =========================================================================
        # P1-1 背压规模门控：按跨切片频次采样 Top-K，并保留全量出现记录供关系上下文聚合
        # =========================================================================
        sampled_labels = unique_labels
        if len(unique_labels) > self.max_labels_for_relation:
            sampled_labels = sorted(
                unique_labels,
                key=lambda x: freq_counter[x.label_id],
                reverse=True,
            )[: self.max_labels_for_relation]
            emit_component_status(
                f" [背压门控]：独立概念数 ({len(unique_labels)}) 超过阈值 {self.max_labels_for_relation}，"
                f"已按跨切片频次采样 Top-{self.max_labels_for_relation} 进入关系建模。\n",
            )

        # [关键闭合] 将命中采样节点的全量 Labeling 出现记录传入 relation_builder，
        # 确保 LLMRelationBuilder 能聚合同一概念在所有文档片段中的上下文与跨切片频次
        sampled_id_set: Set[str] = {lbl.label_id for lbl in sampled_labels}
        candidate_labels_with_all_refs: List[Labeling] = [
            lbl for lbl in all_extracted_labels if lbl.label_id in sampled_id_set
        ]

        # =========================================================================
        # 3.3 关系建模 & 3.4 本体聚拢（阶段超时控制 + P1-2 部分持久化异常兜底）
        # =========================================================================
        extracted_relations: List[RelatingConcepts] = []
        extracted_complexes: List[Ontology] = []

        try:
            if len(sampled_id_set) >= 2:
                stage_t0 = time.perf_counter()
                emit_component_status(
                    f"[关系建模]：正在推导 {len(sampled_id_set)} 个概念节点间的有向语义边...\n",
                )
                raw_relations = await self._run_with_stage_timeout(
                    self.relation_builder.build(candidate_labels_with_all_refs, valid_infos),
                    stage_name="3.3_relation_building",
                    trace_id=envelope.trace_id,
                )
                valid_label_ids: Set[str] = set(unique_labels_map.keys())
                extracted_relations = [
                    rel
                    for rel in raw_relations
                    if rel.label_1_id in valid_label_ids and rel.label_2_id in valid_label_ids
                ]
                logger.info(
                    "[KnowledgeOrganizer] 3.3 关系建模完成 (trace_id=%s): 耗时=%.2fs, 原始边=%d, 校验后有效边=%d",
                    envelope.trace_id,
                    time.perf_counter() - stage_t0,
                    len(raw_relations),
                    len(extracted_relations),
                )
                emit_component_status(
                    f"[关系建模]：构建完成 {len(extracted_relations)} 条有效语义关系边。\n",
                )
            else:
                emit_component_status(
                    " [关系建模]：概念节点不足 2 个，跳过关系边推导。\n",
                )

            stage_t0 = time.perf_counter()
            emit_component_status(
                " [本体聚拢]：正在将离散节点与语义边聚拢为高内聚知识本体...\n",
            )
            extracted_complexes = await self._run_with_stage_timeout(
                self.ontology_clusterer.cluster(unique_labels, extracted_relations),
                stage_name="3.4_ontology_clustering",
                trace_id=envelope.trace_id,
            )
            logger.info(
                "[KnowledgeOrganizer] 3.4 本体聚拢完成 (trace_id=%s): 耗时=%.2fs, 产出本体闭环体=%d",
                envelope.trace_id,
                time.perf_counter() - stage_t0,
                len(extracted_complexes),
            )
            emit_component_status(
                f"[本体聚拢]：成功聚拢 {len(extracted_complexes)} 个成型知识闭环体。\n",
            )

        except Exception as exc:
            logger.warning(
                "[KnowledgeOrganizer] 3.3/3.4 阶段异常降级 (trace_id=%s): %s；"
                "已触发部分持久化保护，保留 %d 条已提取概念节点。",
                envelope.trace_id,
                exc,
                len(all_extracted_labels),
            )
            emit_component_status(
                f" [异常降级]：关系建模或本体聚拢中断（{type(exc).__name__}），"
                f"已保留 {len(unique_labels)} 个已提取概念节点进入存储落盘。\n",
            )

        # 幂等去重合并写回 PipelineEnvelope（防止重入时产生重复边或重复本体）
        merged_relations_map: Dict[str, RelatingConcepts] = {
            r.relation_id: r for r in envelope.relations
        }
        for rel in extracted_relations:
            existing = merged_relations_map.get(rel.relation_id)
            if existing is None or (rel.degree or 0.0) > (existing.degree or 0.0):
                merged_relations_map[rel.relation_id] = rel

        merged_complexes_map: Dict[str, Ontology] = {
            c.complex_id: c for c in envelope.complexes
        }
        for comp in extracted_complexes:
            merged_complexes_map[comp.complex_id] = comp

        total_elapsed = time.perf_counter() - pipeline_start
        logger.info(
            "[KnowledgeOrganizer] 组织流水线闭环完成 (trace_id=%s): 总耗时=%.2fs, 累计标注=%d, 累计关系边=%d, 累计本体=%d",
            envelope.trace_id,
            total_elapsed,
            len(envelope.labels) + len(all_extracted_labels),
            len(merged_relations_map),
            len(merged_complexes_map),
        )

        return envelope.model_copy(
            update={
                "labels": [*envelope.labels, *all_extracted_labels],
                "relations": list(merged_relations_map.values()),
                "complexes": list(merged_complexes_map.values()),
            }
        )
