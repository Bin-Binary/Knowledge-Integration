# /components/internal_knowledge/storage/local_markdown_storage.py
import asyncio
import logging
import re
import shutil
import threading
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Sequence, Set, Tuple, Union

from components.internal_knowledge.schemas.information import Information
from components.internal_knowledge.schemas.labeling import Labeling
from components.internal_knowledge.schemas.ontology import Ontology
from components.internal_knowledge.schemas.pipeline_envelope import PipelineEnvelope
from components.internal_knowledge.schemas.relating_concepts import RelatingConcepts
from components.internal_knowledge.schemas.wiki_governance import WikiArtifactLayer, WikiMaturityStage
from components.internal_knowledge.storage.base_storage import BaseKnowledgeStorage
from components.internal_knowledge.storage.writers import (
    BaseMarkdownArtifactWriter,
    GraphBatchContext,
    InformationArtifactWriter,
    LabelingArtifactWriter,
    OntologyArtifactWriter,
    RelatingArtifactWriter,
)

logger = logging.getLogger(__name__)

_CALLOUT_LINE_RE = re.compile(r"^>\s*\[!(?:abstract|quote|note)\].*\n>\s*(.+)$", re.MULTILINE)


@dataclass(frozen=True)
class _DocIndexEntry:
    """单张 Markdown 卡片的内存索引条目（支持 mtime 增量失效与 1-Hop 邻接预解析）"""

    mtime_ns: int
    doc_tokens: frozenset[str]
    summary_tokens: frozenset[str]
    bottom_links: Dict[str, List[str]]


class LocalMarkdownStorage(BaseKnowledgeStorage):
    """基于本地文件系统（Obsidian 风格 Markdown + YAML Frontmatter）的知识存储适配器。

    核心特性：
        1. 组合四层独立落盘器（Information / Labeling / Relating / Ontology），支持全链路统一落盘与单层独立落盘。
        2. 严格遵循写入隔离铁律：自动化产物仅写入 `debug/`，命中 `release/` 或 `gold/` 自动写入 `.patch_queue.jsonl`。
        3. 跨层加权检索与生命周期晋升：按 `gold (1.0) > release (0.8) > debug (0.4)` 召回，支持无断链晋升迁移与 mtime 缓存加速。
    """

    BACKEND_TYPE: ClassVar[str] = "local_markdown"

    def __init__(
        self,
        vault_root: Union[str, Path],
        allowed_retrieval_stages: Optional[Sequence[WikiMaturityStage]] = None,
        top_k: int = 8,
    ):
        if top_k < 1:
            raise ValueError("top_k 必须 >= 1")

        self.vault_root = Path(vault_root)
        self.allowed_retrieval_stages = tuple(
            allowed_retrieval_stages
            if allowed_retrieval_stages is not None
            else self.DEFAULT_RETRIEVABLE_STAGES
        )
        self.top_k = top_k

        # 线程安全的路径级内存检索索引缓存（key 为规范化绝对路径字符串）
        self._cache_lock = threading.Lock()
        self._doc_index_cache: Dict[str, _DocIndexEntry] = {}

        # 组合四层独立物化视图写入器，并挂载文件写入后的缓存失效回调
        self.info_writer = InformationArtifactWriter(self.vault_root, on_file_written=self._invalidate_path_cache)
        self.label_writer = LabelingArtifactWriter(self.vault_root, on_file_written=self._invalidate_path_cache)
        self.relation_writer = RelatingArtifactWriter(self.vault_root, on_file_written=self._invalidate_path_cache)
        self.ontology_writer = OntologyArtifactWriter(self.vault_root, on_file_written=self._invalidate_path_cache)

        self._init_vault_directories()

    def _init_vault_directories(self) -> None:
        """初始化 3层生命周期 × 4层抽象粒度 的 12 个标准正交目录"""
        for stage in WikiMaturityStage:
            for layer in WikiArtifactLayer:
                (self.vault_root / stage.value / layer.value).mkdir(parents=True, exist_ok=True)

    def _invalidate_path_cache(self, path: Path) -> None:
        """使指定文件的内存索引条目失效"""
        key = str(path.resolve())
        with self._cache_lock:
            self._doc_index_cache.pop(key, None)

    @staticmethod
    def build_batch_context(envelope: PipelineEnvelope) -> GraphBatchContext:
        """从信封构建跨层双向索引上下文"""
        info_to_labels: Dict[str, List[str]] = defaultdict(list)
        label_to_infos: Dict[str, List[str]] = defaultdict(list)
        for lbl in envelope.labels:
            if lbl.label_id not in info_to_labels[lbl.info_id]:
                info_to_labels[lbl.info_id].append(lbl.label_id)
            if lbl.info_id not in label_to_infos[lbl.label_id]:
                label_to_infos[lbl.label_id].append(lbl.info_id)

        label_to_out_rels: Dict[str, List[str]] = defaultdict(list)
        for rel in envelope.relations:
            if rel.relation_id not in label_to_out_rels[rel.label_1_id]:
                label_to_out_rels[rel.label_1_id].append(rel.relation_id)

        label_to_onts: Dict[str, List[str]] = defaultdict(list)
        rel_to_onts: Dict[str, List[str]] = defaultdict(list)
        for ont in envelope.complexes:
            for lid in ont.label_ids:
                if ont.complex_id not in label_to_onts[lid]:
                    label_to_onts[lid].append(ont.complex_id)
            for rid in ont.relation_ids:
                if ont.complex_id not in rel_to_onts[rid]:
                    rel_to_onts[rid].append(ont.complex_id)

        return GraphBatchContext(
            trace_id=envelope.trace_id,
            info_to_labels=info_to_labels,
            label_to_infos=label_to_infos,
            label_to_out_rels=label_to_out_rels,
            label_to_onts=label_to_onts,
            rel_to_onts=rel_to_onts,
        )

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """轻量级中英文混合分词器（兼容中文双字滑窗与英文/代码标识符提取）"""
        lowered = text.lower()
        en_tokens = set(re.findall(r"[a-z0-9_]{2,}", lowered))
        cn_chunks = re.findall(r"[\u4e00-\u9fa5]+", lowered)
        cn_tokens: Set[str] = set()
        for chunk in cn_chunks:
            if len(chunk) == 1:
                cn_tokens.add(chunk)
            else:
                for i in range(len(chunk) - 1):
                    cn_tokens.add(chunk[i : i + 2])
        return en_tokens | cn_tokens

    # ------------------------------------------------------------------
    # 单层独立落盘与全链路统一落盘
    # ------------------------------------------------------------------
    async def save_informations(self, infos: List[Information], trace_id: str = "standalone") -> List[str]:
        ctx = GraphBatchContext(trace_id=trace_id)
        return await asyncio.to_thread(self.info_writer.write_batch, infos, ctx)

    async def save_labels(self, labels: List[Labeling], trace_id: str = "standalone") -> List[str]:
        ctx = GraphBatchContext(trace_id=trace_id)
        return await asyncio.to_thread(self.label_writer.write_batch, labels, ctx)

    async def save_relations(self, relations: List[RelatingConcepts], trace_id: str = "standalone") -> List[str]:
        ctx = GraphBatchContext(trace_id=trace_id)
        return await asyncio.to_thread(self.relation_writer.write_batch, relations, ctx)

    async def save_ontologies(self, complexes: List[Ontology], trace_id: str = "standalone") -> List[str]:
        ctx = GraphBatchContext(trace_id=trace_id)
        return await asyncio.to_thread(self.ontology_writer.write_batch, complexes, ctx)

    def _sync_write_to_debug(self, envelope: PipelineEnvelope) -> List[str]:
        ctx = self.build_batch_context(envelope)
        saved_relpaths: List[str] = []
        saved_relpaths.extend(self.info_writer.write_batch(envelope.raw_infos, ctx))
        saved_relpaths.extend(self.label_writer.write_batch(envelope.labels, ctx))
        saved_relpaths.extend(self.relation_writer.write_batch(envelope.relations, ctx))
        saved_relpaths.extend(self.ontology_writer.write_batch(envelope.complexes, ctx))
        return saved_relpaths

    async def _persist_artifacts(self, envelope: PipelineEnvelope) -> List[str]:
        return await asyncio.to_thread(self._sync_write_to_debug, envelope)

    # ------------------------------------------------------------------
    # 异步加权记忆召回（mtime 增量索引 + 单行 Callout 高密摘要加权 + 1-Hop 邻域扩展）
    # ------------------------------------------------------------------
    def _get_or_build_index_entry(self, md_file: Path) -> Optional[_DocIndexEntry]:
        """读取或按 mtime 增量刷新单张卡片的内存索引"""
        try:
            stat = md_file.stat()
        except OSError:
            return None

        cache_key = str(md_file.resolve())
        with self._cache_lock:
            cached = self._doc_index_cache.get(cache_key)
            if cached is not None and cached.mtime_ns == stat.st_mtime_ns:
                return cached

        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError:
            return None

        doc_tokens = frozenset(self._tokenize(content))
        if not doc_tokens:
            return None

        summary_tokens: frozenset[str] = frozenset()
        m_callout = _CALLOUT_LINE_RE.search(content)
        if m_callout:
            summary_tokens = frozenset(self._tokenize(m_callout.group(1)))

        bottom_links = BaseMarkdownArtifactWriter.extract_bottom_links(content)
        entry = _DocIndexEntry(
            mtime_ns=stat.st_mtime_ns,
            doc_tokens=doc_tokens,
            summary_tokens=summary_tokens,
            bottom_links=bottom_links,
        )
        with self._cache_lock:
            self._doc_index_cache[cache_key] = entry
        return entry

    async def _query_knowledge_ids(self, problem: str, envelope: PipelineEnvelope) -> List[str]:
        return await asyncio.to_thread(self._sync_search_vault, problem)

    def _sync_search_vault(self, problem: str) -> List[str]:
        query_tokens = self._tokenize(problem)
        if not query_tokens:
            return []

        layer_priority_boost: Dict[WikiArtifactLayer, float] = {
            WikiArtifactLayer.ONTOLOGY: 1.5,
            WikiArtifactLayer.LABELING: 1.3,
            WikiArtifactLayer.RELATING: 1.1,
            WikiArtifactLayer.INFORMATION: 0.9,
        }

        scored_candidates: List[Tuple[float, str, _DocIndexEntry]] = []
        seen_ids: Set[str] = set()
        accessible_ids: Set[str] = set()

        for stage in self.allowed_retrieval_stages:
            stage_weight = self.DEFAULT_STAGE_WEIGHTS.get(stage, 0.5)

            for layer, layer_boost in layer_priority_boost.items():
                layer_dir = self.vault_root / stage.value / layer.value
                if not layer_dir.exists():
                    continue

                for md_file in layer_dir.glob("*.md"):
                    artifact_id = md_file.stem
                    accessible_ids.add(artifact_id)
                    if artifact_id in seen_ids:
                        continue

                    entry = self._get_or_build_index_entry(md_file)
                    if entry is None:
                        continue

                    full_overlap = len(query_tokens & entry.doc_tokens)
                    if full_overlap == 0:
                        continue

                    base_recall = full_overlap / len(query_tokens)
                    summary_bonus = 0.0
                    if entry.summary_tokens:
                        summary_bonus = 0.5 * (len(query_tokens & entry.summary_tokens) / len(query_tokens))

                    final_score = (base_recall + summary_bonus) * stage_weight * layer_boost
                    seen_ids.add(artifact_id)
                    scored_candidates.append((final_score, artifact_id, entry))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        final_ids: List[str] = []
        for _, aid, entry in scored_candidates[: self.top_k]:
            if aid not in final_ids:
                final_ids.append(aid)

            if len(final_ids) <= 4:
                for group_name in ("发出关系", "溯源切片", "提炼概念"):
                    for linked_id in entry.bottom_links.get(group_name, [])[:2]:
                        if (
                            linked_id in accessible_ids
                            and linked_id not in final_ids
                            and len(final_ids) < self.top_k
                        ):
                            final_ids.append(linked_id)

        if final_ids:
            logger.debug(
                "[%s] 检索命中明细: query_tokens=%d, 候选匹配=%d, 最终返回=%s",
                self.BACKEND_TYPE,
                len(query_tokens),
                len(scored_candidates),
                final_ids,
            )
        return final_ids

    # ------------------------------------------------------------------
    # 生命周期治理与异步内容水合加载
    # ------------------------------------------------------------------
    def promote_artifact(
        self,
        artifact_id: str,
        layer: WikiArtifactLayer,
        from_stage: WikiMaturityStage,
        to_stage: WikiMaturityStage,
    ) -> Optional[str]:
        """将知识卡片在生命周期目录间安全迁移（如 debug -> release 或 release -> gold），并刷新内存索引"""
        src_rel = self.build_artifact_relpath(from_stage, layer, artifact_id)
        dst_rel = self.build_artifact_relpath(to_stage, layer, artifact_id)
        src_path = self.vault_root / src_rel
        dst_path = self.vault_root / dst_rel

        if not src_path.exists():
            logger.warning("[%s] 晋升跳过：源文件不存在 %s", self.BACKEND_TYPE, src_rel)
            return None

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        self._invalidate_path_cache(src_path)
        self._invalidate_path_cache(dst_path)
        logger.info("[%s] 知识晋升完成: %s -> %s", self.BACKEND_TYPE, src_rel, dst_rel)
        return dst_rel

    async def _fetch_contents_by_ids(self, artifact_ids: List[str]) -> str:
        """根据知识 ID 列表异步加载对应的 Markdown 卡片全文"""
        return await asyncio.to_thread(self._sync_load_contents, artifact_ids)

    def _sync_load_contents(self, artifact_ids: List[str]) -> str:
        sections: List[str] = []

        for aid in artifact_ids:
            found_text: Optional[str] = None
            for stage in self.allowed_retrieval_stages:
                for layer in WikiArtifactLayer:
                    try:
                        relpath = self.build_artifact_relpath(stage, layer, aid)
                    except ValueError:
                        continue
                    target_path = self.vault_root / relpath
                    if target_path.exists():
                        try:
                            found_text = target_path.read_text(encoding="utf-8").strip()
                        except OSError as exc:
                            logger.warning("[%s] 读取知识文件失败 %s: %s", self.BACKEND_TYPE, target_path, exc)
                        break
                if found_text is not None:
                    break

            if found_text:
                sections.append(f"=== 知识卡片 [{aid}] ===\n{found_text}")
            else:
                logger.debug("[%s] 未在允许的生命周期目录中找到知识 ID: %s", self.BACKEND_TYPE, aid)

        return "\n\n".join(sections)
