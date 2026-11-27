# /components/internal_knowledge/organization/plugins/relation_builder.py
import asyncio
import inspect
import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional, Set, Type
from pydantic import Field, create_model

from schemas.base import DocumentedEnum, LLMOutputSchema
from components.internal_knowledge.schemas.artifacts import StandardRelationVerb
from components.internal_knowledge.schemas.information import Information
from components.internal_knowledge.schemas.labeling import Labeling
from components.internal_knowledge.schemas.relating_concepts import RelatingConcepts
from protocols.llm import StructuredLLMProtocol
from components.internal_knowledge.protocols import RelationBuilderProtocol
from components.internal_knowledge.organization.organizer import KnowledgeOrganizer
from components.internal_knowledge.organization.registry import OrganizationPluginRegistry, OrgStage
from infra.exceptions import KnowledgePipelineError 

logger = logging.getLogger(__name__)


class _RelationEdgeItem(LLMOutputSchema):
    """单条候选语义关系边结构（供结构化 LLM 输出校验）"""

    source_label_id: str = Field(..., description="起点概念节点 ID（必须严格来自给定候选列表）")
    target_label_id: str = Field(..., description="终点概念节点 ID（必须严格来自给定候选列表）")
    relation_type: str = Field(..., description="关系枚举值（必须严格匹配给定关系字典中的 value）")
    degree: float = Field(default=0.8, ge=0.0, le=1.0, description="语义关联置信度 [0.0, 1.0]")


@OrganizationPluginRegistry.register(OrgStage.RELATE, name="llm_relation", is_default=True)
class LLMRelationBuilder(RelationBuilderProtocol):
    """3.3 基于结构化大模型的关系建模算子（滑动窗口 + 全局核心节点补全 + 动态上下文预算）"""

    def __init__(
        self,
        llm_client: StructuredLLMProtocol,
        relation_enum_cls: Type[DocumentedEnum] = StandardRelationVerb,
        min_confidence: float = 0.65,
        window_size: int = 20,
        overlap: int = 5,
        max_edges_per_window: int = 8,
        max_concurrency: int = 3,
        context_char_budget: int = 6000,
        enable_hub_window: bool = True,
        window_timeout_seconds: Optional[float] = None,
    ):
        if overlap >= window_size:
            raise ValueError("overlap 必须小于 window_size")
        self.llm = llm_client
        self.relation_enum_cls = relation_enum_cls
        self.min_confidence = min_confidence
        self.window_size = window_size
        self.overlap = overlap
        self.max_edges_per_window = max_edges_per_window
        self.max_concurrency = max_concurrency
        self.context_char_budget = context_char_budget
        self.enable_hub_window = enable_hub_window
        self.window_timeout_seconds = window_timeout_seconds

        schema_name = f"_RelationBatchOutput_Max{self.max_edges_per_window}"
        self._output_schema = create_model(
            schema_name,
            __base__=LLMOutputSchema,
            edges=(
                List[_RelationEdgeItem],
                Field(
                    default_factory=list,
                    max_length=self.max_edges_per_window,
                    description=f"推导出的高置信度有向语义边列表（单窗口最多 {self.max_edges_per_window} 条，按置信度降序）",
                ),
            ),
        )

    def _create_windows(
        self,
        labels: List[Labeling],
        label_to_info_ids: Dict[str, List[str]],
    ) -> List[List[Labeling]]:
        """构建局部滑动窗口，并在满足跨文档共现条件时追加全局核心节点（Hub）窗口"""
        grouped: Dict[str, List[Labeling]] = defaultdict(list)
        for lbl in labels:
            grouped[lbl.info_id].append(lbl)

        ordered_labels: List[Labeling] = [lbl for group in grouped.values() for lbl in group]
        if len(ordered_labels) <= self.window_size:
            return [ordered_labels]

        step = self.window_size - self.overlap
        windows: List[List[Labeling]] = []
        for start in range(0, len(ordered_labels), step):
            window = ordered_labels[start : start + self.window_size]
            if len(window) >= 2:
                windows.append(window)
            if start + self.window_size >= len(ordered_labels):
                break

        if self.enable_hub_window and len(windows) > 1:
            hub_candidates = sorted(
                ordered_labels,
                key=lambda lbl: len(label_to_info_ids.get(lbl.label_id, [])),
                reverse=True,
            )[: self.window_size]

            if (
                len(hub_candidates) >= 2
                and len(label_to_info_ids.get(hub_candidates[0].label_id, [])) > 1
            ):
                windows.append(hub_candidates)
                logger.debug(
                    "已追加全局核心节点窗口（Hub Window），包含 %d 个高频概念",
                    len(hub_candidates),
                )

        return windows

    def _build_window_context(
        self,
        window_labels: List[Labeling],
        label_to_info_ids: Dict[str, List[str]],
        info_map: Dict[str, Information],
    ) -> str:
        """动态分配上下文字符预算，并围绕目标概念词命中位置居中截取原文证据"""
        info_to_terms: Dict[str, List[str]] = defaultdict(list)
        relevant_info_ids: List[str] = []

        for lbl in window_labels:
            for iid in label_to_info_ids.get(lbl.label_id, []):
                if iid in info_map:
                    if iid not in info_to_terms:
                        relevant_info_ids.append(iid)
                    info_to_terms[iid].append(lbl.label)

        if not relevant_info_ids:
            return "无对应原始上下文"

        per_info_chars = max(300, self.context_char_budget // len(relevant_info_ids))
        snippets: List[str] = []

        for iid in relevant_info_ids:
            text = info_map[iid].information
            if len(text) <= per_info_chars:
                snippets.append(text)
                continue

            hit_pos = -1
            for term in info_to_terms[iid]:
                pos = text.find(term)
                if pos != -1:
                    hit_pos = pos
                    break

            if hit_pos == -1:
                snippets.append(text[:per_info_chars])
            else:
                half = per_info_chars // 2
                start = max(0, hit_pos - half)
                end = min(len(text), start + per_info_chars)
                if end - start < per_info_chars:
                    start = max(0, end - per_info_chars)
                snippets.append(text[start:end])

        return "\n---\n".join(snippets)

    @staticmethod
    def _build_compliant_relation_id(
        src_label_id: str, verb: str, tgt_label_id: str
    ) -> str:
        """生成符合系统规范的确定性关系边 ID"""
        src_core = src_label_id.removeprefix("lbl_")
        tgt_core = tgt_label_id.removeprefix("lbl_")
        src_stem = src_core[:-5] if len(src_core) > 6 and src_core[-5] == "_" else src_core
        tgt_stem = tgt_core[:-5] if len(tgt_core) > 6 and tgt_core[-5] == "_" else tgt_core

        raw_slug = f"{src_stem}_{verb}_{tgt_stem}"
        sig = f"{src_label_id}->{verb}->{tgt_label_id}"
        return KnowledgeOrganizer.generate_deterministic_id(
            prefix="rel",
            semantic_key=sig,
            semantic_slug=raw_slug,
        )

    async def _process_window(
        self,
        window_idx: int,
        total_windows: int,
        semaphore: asyncio.Semaphore,
        window_labels: List[Labeling],
        label_to_info_ids: Dict[str, List[str]],
        info_map: Dict[str, Information],
        relation_guide: str,
        valid_enum_map: Dict[str, DocumentedEnum],
    ) -> Optional[List[RelatingConcepts]]:
        """并发处理单个候选窗口；调用异常时返回 None 以区分于正常的空边列表 []"""
        async with semaphore:
            start_ts = time.perf_counter()
            valid_node_ids: Set[str] = {lbl.label_id for lbl in window_labels}
            nodes_catalog = "\n".join(f"- `{lbl.label_id}`: {lbl.label}" for lbl in window_labels)
            context_summary = self._build_window_context(window_labels, label_to_info_ids, info_map)

            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一个知识图谱关系推理专家。请根据候选概念节点列表及原始上下文，推导节点间的有向语义关系。\n"
                        f"允许使用的关系类型字典（必须严格输出反引号内的英文 value）：\n{relation_guide}\n"
                        f"约束：单次最多输出 {self.max_edges_per_window} 条最高置信度核心边；严禁捏造不在候选列表中的节点 ID，严禁自环。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"### 候选概念节点列表：\n{nodes_catalog}\n\n### 原始上下文参考：\n{context_summary}",
                },
            ]

            try:
                raw_call = self.llm.generate_structured(
                    messages=messages,
                    response_schema=self._output_schema,
                )
                coro = raw_call if inspect.isawaitable(raw_call) else asyncio.sleep(0, result=raw_call)
                if self.window_timeout_seconds is not None:
                    result = await asyncio.wait_for(coro, timeout=self.window_timeout_seconds)
                else:
                    result = await coro
            except Exception:
                logger.exception(
                    "关系抽取窗口 [%d/%d] 调用 LLM 失败（节点数=%d），已跳过该窗口",
                    window_idx,
                    total_windows,
                    len(window_labels),
                )
                return None

            window_relations: List[RelatingConcepts] = []
            dropped_low_conf = 0
            dropped_invalid = 0

            for edge in result.edges[: self.max_edges_per_window]:
                if edge.degree < self.min_confidence:
                    dropped_low_conf += 1
                    continue
                if (
                    edge.source_label_id == edge.target_label_id
                    or edge.source_label_id not in valid_node_ids
                    or edge.target_label_id not in valid_node_ids
                ):
                    dropped_invalid += 1
                    continue

                rel_enum = valid_enum_map.get(edge.relation_type.strip())
                if not rel_enum:
                    dropped_invalid += 1
                    continue

                rel_id = self._build_compliant_relation_id(
                    edge.source_label_id, rel_enum.value, edge.target_label_id
                )
                window_relations.append(
                    RelatingConcepts(
                        relation_id=rel_id,
                        label_1_id=edge.source_label_id,
                        label_2_id=edge.target_label_id,
                        relationship_type=rel_enum,
                        degree=edge.degree,
                    )
                )

            elapsed = time.perf_counter() - start_ts
            logger.debug(
                "关系抽取窗口 [%d/%d] 完成: 耗时=%.2fs, 原始边=%d, 保留=%d, 低置信丢弃=%d, 非法幻觉丢弃=%d",
                window_idx,
                total_windows,
                elapsed,
                len(result.edges),
                len(window_relations),
                dropped_low_conf,
                dropped_invalid,
            )
            return window_relations

    async def build(
        self, labels: List[Labeling], context_infos: List[Information]
    ) -> List[RelatingConcepts]:
        """关系建模主入口：节点去重与多文档映射 -> 窗口划分 -> 并发抽取 -> 全灭熔断校验 -> 最高置信度合并"""
        if len(labels) < 2:
            logger.info("关系抽取跳过: 输入标签数量不足 2 个 (count=%d)", len(labels))
            return []

        unique_labels_map: Dict[str, Labeling] = {}
        label_to_info_ids: Dict[str, List[str]] = defaultdict(list)

        for lbl in labels:
            unique_labels_map.setdefault(lbl.label_id, lbl)
            if lbl.info_id and lbl.info_id not in label_to_info_ids[lbl.label_id]:
                label_to_info_ids[lbl.label_id].append(lbl.info_id)

        unique_labels = list(unique_labels_map.values())
        if len(unique_labels) < 2:
            logger.info("关系抽取跳过: 去重后唯一概念节点不足 2 个 (count=%d)", len(unique_labels))
            return []

        start_ts = time.perf_counter()
        relation_guide = self.relation_enum_cls.to_prompt_guide()
        valid_enum_map: Dict[str, DocumentedEnum] = {e.value: e for e in self.relation_enum_cls}
        info_map: Dict[str, Information] = {info.info_id: info for info in context_infos}

        windows = self._create_windows(unique_labels, label_to_info_ids)
        total_windows = len(windows)
        logger.info(
            "开始知识关系建模: 唯一节点=%d, 上下文片段=%d, 窗口总数=%d (window_size=%d, overlap=%d, hub_window=%s, concurrency=%d)",
            len(unique_labels),
            len(info_map),
            total_windows,
            self.window_size,
            self.overlap,
            self.enable_hub_window,
            self.max_concurrency,
        )

        semaphore = asyncio.Semaphore(self.max_concurrency)
        batch_results = await asyncio.gather(
            *(
                self._process_window(
                    idx + 1,
                    total_windows,
                    semaphore,
                    win,
                    label_to_info_ids,
                    info_map,
                    relation_guide,
                    valid_enum_map,
                )
                for idx, win in enumerate(windows)
            )
        )

        # 统计调用失败的窗口数；若 100% 全部失败则抛出业务异常触发编排器降级/恢复
        failed_windows = sum(1 for res in batch_results if res is None)
        if total_windows > 0 and failed_windows == total_windows:
            raise KnowledgePipelineError(
                message=f"所有 {total_windows} 个关系推理窗口均调用失败",
                stage="organization",
                user_friendly_hint="概念关系推理服务暂时不可用，已为您保留基础概念节点。",
                metadata={"total_windows": total_windows},
            )

        merged_relations: Dict[str, RelatingConcepts] = {}
        raw_edge_total = 0
        for win_rels in batch_results:
            if win_rels is None:
                continue
            raw_edge_total += len(win_rels)
            for rel in win_rels:
                existing = merged_relations.get(rel.relation_id)
                if existing is None or (rel.degree or 0.0) > (existing.degree or 0.0):
                    merged_relations[rel.relation_id] = rel

        elapsed = time.perf_counter() - start_ts
        logger.info(
            "知识关系建模完成: 耗时=%.2fs, 成功窗口=%d/%d, 窗口产出边总计=%d, 去重合并后最终关系边=%d",
            elapsed,
            total_windows - failed_windows,
            total_windows,
            raw_edge_total,
            len(merged_relations),
        )
        return list(merged_relations.values())
