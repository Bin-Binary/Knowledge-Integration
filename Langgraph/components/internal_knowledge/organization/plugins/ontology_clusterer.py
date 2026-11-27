# /components/internal_knowledge/organization/plugins/ontology_clusterer.py
import asyncio
import inspect
import logging
import re
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple
from pydantic import Field

from schemas.base import LLMOutputSchema
from components.internal_knowledge.schemas.labeling import Labeling
from components.internal_knowledge.schemas.ontology import Ontology
from components.internal_knowledge.schemas.relating_concepts import RelatingConcepts
from protocols.llm import StructuredLLMProtocol
from components.internal_knowledge.protocols import OntologyClustererProtocol
from components.internal_knowledge.organization.organizer import KnowledgeOrganizer
from components.internal_knowledge.organization.registry import OrganizationPluginRegistry, OrgStage
from infra.exceptions import KnowledgePipelineError

logger = logging.getLogger(__name__)


class _OntologySynthesisOutput(LLMOutputSchema):
    """单个高内聚子图的本体抽象摘要输出"""

    semantic_slug: str = Field(
        ...,
        description="全小写英文蛇形短标识（2~4个词，单数形式，如 ci_artifact_fallback_pipeline，严禁带 ont_ 前缀）",
    )
    canonical_name: str = Field(
        ...,
        description="高度凝练的中文知识本体名称（如 制品拉取回退与容错闭环体系）",
    )
    core_summary: str = Field(
        ...,
        description="1~3句话概括该知识闭环体的核心运作机理、解决的业务痛点及内部节点协同关系",
    )


@OrganizationPluginRegistry.register(OrgStage.CLUSTER, name="llm_graph_cluster", is_default=True)
class LLMGraphOntologyClusterer(OntologyClustererProtocol):
    """3.4 基于图连通分量与结构化大模型的本体聚拢算子

    核心机制：
    1. 图拓扑子图划分：基于概念节点与有效关系边构建连通分量，剔除无法形成闭环的孤立碎片。
    2. 超大子图度数裁剪：若单个连通分量超过 max_cluster_size，按局部连接度保留核心骨干子图。
    3. 结构化本体抽象：并发调用 LLM 为每个子图生成规范名称、英文 slug 与核心机理摘要。
    4. 确定性 ID 与异常熔断：生成 `ont_<slug>_<hash>` 合规 ID；单簇失败局部跳过，全簇失败抛出业务异常。
    """

    def __init__(
        self,
        llm_client: StructuredLLMProtocol,
        min_cluster_size: int = 2,
        max_cluster_size: int = 15,
        max_concurrency: int = 3,
        cluster_timeout_seconds: Optional[float] = None,
    ):
        if min_cluster_size < 2:
            raise ValueError("min_cluster_size 必须 >= 2（至少包含2个概念节点才能构成关系闭环）")
        if max_cluster_size < min_cluster_size:
            raise ValueError("max_cluster_size 必须 >= min_cluster_size")

        self.llm = llm_client
        self.min_cluster_size = min_cluster_size
        self.max_cluster_size = max_cluster_size
        self.max_concurrency = max_concurrency
        self.cluster_timeout_seconds = cluster_timeout_seconds
    def _partition_subgraphs(
        self,
        unique_labels: Dict[str, Labeling],
        relations: List[RelatingConcepts],
    ) -> List[Tuple[List[Labeling], List[RelatingConcepts]]]:
        """基于无向连通分量划分候选知识子图，并对超大规模子图按度数裁剪"""
        adj: Dict[str, Set[str]] = defaultdict(set)
        valid_relations: List[RelatingConcepts] = []

        for rel in relations:
            if (
                rel.label_1_id in unique_labels
                and rel.label_2_id in unique_labels
                and rel.label_1_id != rel.label_2_id
            ):
                adj[rel.label_1_id].add(rel.label_2_id)
                adj[rel.label_2_id].add(rel.label_1_id)
                valid_relations.append(rel)

        visited: Set[str] = set()
        subgraphs: List[Tuple[List[Labeling], List[RelatingConcepts]]] = []

        for start_id in unique_labels:
            if start_id in visited or start_id not in adj:
                continue

            # BFS 遍历获取完整连通分量
            comp_ids: List[str] = []
            queue: deque[str] = deque([start_id])
            visited.add(start_id)

            while queue:
                curr = queue.popleft()
                comp_ids.append(curr)
                for nxt in adj[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)

            if len(comp_ids) < self.min_cluster_size:
                continue

            # 若单个连通分量过大，按节点局部度数降序保留核心骨干节点
            if len(comp_ids) > self.max_cluster_size:
                comp_ids = sorted(comp_ids, key=lambda nid: len(adj[nid]), reverse=True)[
                    : self.max_cluster_size
                ]

            comp_id_set = set(comp_ids)
            comp_labels = [unique_labels[nid] for nid in comp_ids]
            comp_relations = [
                rel
                for rel in valid_relations
                if rel.label_1_id in comp_id_set and rel.label_2_id in comp_id_set
            ]

            if len(comp_labels) >= self.min_cluster_size and comp_relations:
                subgraphs.append((comp_labels, comp_relations))

        # 按子图节点规模降序排列，优先聚拢核心大闭环
        subgraphs.sort(key=lambda item: len(item[0]), reverse=True)
        return subgraphs


    @staticmethod
    def _normalize_ontology_slug(raw_slug: str) -> str:
        """规范化本体英文蛇形标识"""
        slug = re.sub(r"[^a-z0-9_]+", "_", raw_slug.strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("_")
        for prefix in ("ont_", "ontology_", "cluster_", "complex_"):
            if slug.startswith(prefix):
                slug = slug[len(prefix) :]
        return re.sub(r"_+", "_", slug).strip("_")

    @staticmethod
    def _build_compliant_ontology_id(clean_slug: str, node_ids: List[str]) -> str:
        """生成确定性本体 ID（ont_<slug>_<4位指纹>）"""
        sorted_seed = "|".join(sorted(node_ids))
        return KnowledgeOrganizer.generate_deterministic_id(
            prefix="ont",
            semantic_key=sorted_seed,
            semantic_slug=clean_slug,
        )

    async def _synthesize_one_cluster(
        self,
        cluster_idx: int,
        total_clusters: int,
        semaphore: asyncio.Semaphore,
        comp_labels: List[Labeling],
        comp_relations: List[RelatingConcepts],
    ) -> Optional[Ontology]:
        """并发提炼单个子图的知识本体；调用异常时返回 None 以区分正常过滤"""
        async with semaphore:
            start_ts = time.perf_counter()
            label_map = {lbl.label_id: lbl for lbl in comp_labels}

            # 组装节点清单（附带 3.2 阶段提炼的 core_definition）
            node_lines: List[str] = []
            for lbl in comp_labels:
                core_def = ""
                if isinstance(lbl.rich_semantics, dict):
                    core_def = lbl.rich_semantics.get("core_definition", "")
                desc_part = f" —— {core_def}" if core_def else ""
                node_lines.append(f"- `{lbl.label_id}` {lbl.label}{desc_part}")

            # 组装有向语义边清单
            edge_lines: List[str] = []
            for rel in comp_relations:
                src_name = label_map[rel.label_1_id].label
                tgt_name = label_map[rel.label_2_id].label
                verb = (
                    rel.relationship_type.value
                    if hasattr(rel.relationship_type, "value")
                    else str(rel.relationship_type)
                )
                edge_lines.append(f"- {src_name} --[{verb}]--> {tgt_name}")

            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是一个知识图谱本体架构师。请根据给定的一组高内聚概念节点及其有向语义关系网络，"
                        "将其抽象为一个结构化的知识闭环体（Ontology）。\n"
                        "约束：名称必须高度概括该子图所表达的完整业务机制或系统流程；"
                        "semantic_slug 必须使用 2~4 个全小写英文单数词的蛇形命名。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"### 子图概念节点 ({len(comp_labels)} 个)：\n"
                        + "\n".join(node_lines)
                        + f"\n\n### 子图语义关系边 ({len(comp_relations)} 条)：\n"
                        + "\n".join(edge_lines)
                    ),
                },
            ]

            try:
                raw_call = self.llm.generate_structured(
                    messages=messages,
                    response_schema=_OntologySynthesisOutput,
                )
                coro = raw_call if inspect.isawaitable(raw_call) else asyncio.sleep(0, result=raw_call)
                if self.cluster_timeout_seconds is not None:
                    result = await asyncio.wait_for(coro, timeout=self.cluster_timeout_seconds)
                else:
                    result = await coro
            except Exception:
                logger.exception(
                    "本体聚拢子图 [%d/%d] 调用 LLM 失败（节点数=%d, 边数=%d），已跳过该子图",
                    cluster_idx,
                    total_clusters,
                    len(comp_labels),
                    len(comp_relations),
                )
                return None

            clean_slug = self._normalize_ontology_slug(result.semantic_slug) or "knowledge_cluster"
            clean_name = result.canonical_name.strip()
            clean_summary = result.core_summary.strip()
            if not clean_name:
                logger.warning("本体聚拢子图 [%d/%d] 返回空名称，已丢弃", cluster_idx, total_clusters)
                return None

            node_ids = [lbl.label_id for lbl in comp_labels]
            relation_ids = [rel.relation_id for rel in comp_relations]
            complex_id = self._build_compliant_ontology_id(clean_slug, node_ids)

            # 组合宏观定性摘要（兼顾 Ontology._render_body 标题与 OntologyArtifact 单行摘要渲染）
            descriptor_text = f"{clean_name}：{clean_summary}" if clean_summary else clean_name

            elapsed = time.perf_counter() - start_ts
            logger.debug(
                "本体聚拢子图 [%d/%d] 完成: 耗时=%.2fs, complex_id=%s, descriptor=%s (节点=%d, 边=%d)",
                cluster_idx,
                total_clusters,
                elapsed,
                complex_id,
                descriptor_text,
                len(node_ids),
                len(relation_ids),
            )

            return Ontology(
                complex_id=complex_id,
                label_ids=node_ids,
                relation_ids=relation_ids,
                descriptor=descriptor_text,
            )

    async def cluster(
        self,
        labels: List[Labeling],
        relations: List[RelatingConcepts],
    ) -> List[Ontology]:
        """本体聚拢主入口：图连通分量划分 -> 并发 LLM 抽象 -> 全灭熔断校验 -> ID 去重合并"""
        if len(labels) < self.min_cluster_size or not relations:
            logger.info(
                "本体聚拢跳过: 节点或关系边不足以形成闭环 (labels=%d, relations=%d)",
                len(labels),
                len(relations),
            )
            return []

        unique_labels: Dict[str, Labeling] = {}
        for lbl in labels:
            unique_labels.setdefault(lbl.label_id, lbl)

        subgraphs = self._partition_subgraphs(unique_labels, relations)
        if not subgraphs:
            logger.info(
                "本体聚拢跳过: 未发现满足最小规模 (>=%d) 的有效连通子图",
                self.min_cluster_size,
            )
            return []

        start_ts = time.perf_counter()
        total_clusters = len(subgraphs)
        logger.info(
            "开始知识本体聚拢: 独立节点=%d, 有效关系边=%d, 待抽象连通子图=%d (concurrency=%d)",
            len(unique_labels),
            len(relations),
            total_clusters,
            self.max_concurrency,
        )

        semaphore = asyncio.Semaphore(self.max_concurrency)
        batch_results = await asyncio.gather(
            *(
                self._synthesize_one_cluster(
                    idx + 1,
                    total_clusters,
                    semaphore,
                    comp_labels,
                    comp_relations,
                )
                for idx, (comp_labels, comp_relations) in enumerate(subgraphs)
            )
        )

        failed_clusters = sum(1 for res in batch_results if res is None)
        if total_clusters > 0 and failed_clusters == total_clusters:
            raise KnowledgePipelineError(
                message=f"所有 {total_clusters} 个知识子图本体抽象均调用失败",
                stage="organization",
                user_friendly_hint="知识本体归纳服务暂时不可用，已为您保留概念节点与语义关系边。",
                metadata={"total_clusters": total_clusters},
            )

        merged_ontologies: Dict[str, Ontology] = {}
        for ont in batch_results:
            if ont is not None:
                merged_ontologies[ont.complex_id] = ont

        elapsed = time.perf_counter() - start_ts
        logger.info(
            "知识本体聚拢完成: 耗时=%.2fs, 成功子图=%d/%d, 最终产出本体=%d",
            elapsed,
            total_clusters - failed_clusters,
            total_clusters,
            len(merged_ontologies),
        )
        return list(merged_ontologies.values())
