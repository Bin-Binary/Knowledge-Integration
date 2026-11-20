# /components/internal_knowledge/storage/local_markdown_storage.py
import asyncio
import logging
import re
import shutil
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Sequence, Set, Tuple

from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope
from schemas.internal_knowledge.wiki_governance import WikiArtifactLayer, WikiMaturityStage
from components.internal_knowledge.storage.base_storage import BaseKnowledgeStorage

logger = logging.getLogger(__name__)

class LocalMarkdownStorage(BaseKnowledgeStorage):
    """基于本地文件系统（Obsidian 风格 Markdown + YAML Frontmatter）的知识存储适配器。

    核心特性：
        1. 严格遵循写入隔离铁律：流水线自动化落盘默认且仅写入 `debug/` 目录。
        2. 跨层加权检索：按 `gold (1.0) > release (0.8) > debug (0.4)` 置信度权重匹配并返回 Top-K 知识 ID。
        3. 生命周期晋升：提供 `promote_artifact()` 支持人工审核（debug -> release）与闭环验证（release -> gold）无损迁移。
    """

    BACKEND_TYPE: ClassVar[str] = "local_markdown"

    def __init__(
        self,
        vault_root: str | Path,  
        allowed_retrieval_stages: Optional[Sequence[WikiMaturityStage]] = None,
        top_k: int = 8,
    ):
        """
        Args:
            vault_root: LLM-WIKI 知识库本地根目录（如 "./data/llm_wiki"）。
            allowed_retrieval_stages: 允许参与检索的生命周期阶段（生产环境可设为 [GOLD, RELEASE] 屏蔽未审核 debug）。
            top_k: 单次检索返回的最大关联知识 ID 数量。
        """
        self.vault_root = Path(vault_root)
        self.allowed_retrieval_stages = tuple(
            allowed_retrieval_stages
            if allowed_retrieval_stages is not None
            else (WikiMaturityStage.GOLD, WikiMaturityStage.RELEASE, WikiMaturityStage.DEBUG)
        )
        self.top_k = top_k
        self._init_vault_directories()

    def _init_vault_directories(self) -> None:
        """初始化 3层生命周期 × 4层抽象粒度 的 12 个标准正交目录"""
        for stage in WikiMaturityStage:
            for layer in WikiArtifactLayer:
                (self.vault_root / stage.value / layer.value).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. 异步持久化落盘（实现 BaseKnowledgeStorage._persist_artifacts）
    # ------------------------------------------------------------------

    async def _persist_artifacts(self, envelope: PipelineEnvelope) -> List[str]:
        """将四类知识产物渲染为 Markdown 并隔离写入 `debug/` 对应子目录"""
        return await asyncio.to_thread(self._sync_write_to_debug, envelope)

    def _sync_write_to_debug(self, envelope: PipelineEnvelope) -> List[str]:
        saved_relpaths: List[str] = []
        stage = WikiMaturityStage.DEBUG  # 写入隔离铁律：自动化产物仅允许进入 debug/

        # 按信息密度由低到高依次落盘
        artifact_groups = [
            (WikiArtifactLayer.INFORMATION, envelope.raw_infos, "info_id"),
            (WikiArtifactLayer.LABELING, envelope.labels, "label_id"),
            (WikiArtifactLayer.RELATING, envelope.relations, "relation_id"),
            (WikiArtifactLayer.ONTOLOGY, envelope.complexes, "complex_id"),
        ]

        for layer, items, id_attr in artifact_groups:
            for item in items:
                artifact_id = getattr(item, id_attr)
                relpath = self.build_artifact_relpath(stage, layer, artifact_id)
                abs_path = self.vault_root / relpath

                markdown_content = item.to_markdown()
                abs_path.write_text(markdown_content, encoding="utf-8")
                saved_relpaths.append(relpath)

        logger.info(
            "[%s] 成功落盘 %d 个知识文件至 debug/ (trace_id=%s)",
            self.BACKEND_TYPE,
            len(saved_relpaths),
            envelope.trace_id,
        )
        return saved_relpaths

    # ------------------------------------------------------------------
    # 2. 异步加权记忆召回（实现 BaseKnowledgeStorage._query_knowledge_ids）
    # ------------------------------------------------------------------

    async def _query_knowledge_ids(self, problem: str, envelope: PipelineEnvelope) -> List[str]:
        """跨允许的生命周期目录检索关联知识 ID，按【置信度权重 × 词元重合度】排序"""
        return await asyncio.to_thread(self._sync_search_vault, problem)

    def _sync_search_vault(self, problem: str) -> List[str]:
        query_tokens = self._tokenize(problem)
        if not query_tokens:
            return []

        # 优先检索高层抽象知识（Ontology > Labeling > Information），提供高密度上下文
        layer_priority_boost: Dict[WikiArtifactLayer, float] = {
            WikiArtifactLayer.ONTOLOGY: 1.5,
            WikiArtifactLayer.LABELING: 1.2,
            WikiArtifactLayer.RELATING: 1.0,
            WikiArtifactLayer.INFORMATION: 0.9,
        }

        scored_candidates: List[Tuple[float, str]] = []
        seen_ids: Set[str] = set()

        # 按 gold -> release -> debug 顺序扫描（高成熟度版本覆盖低成熟度同 ID 文件）
        for stage in self.allowed_retrieval_stages:
            stage_weight = self.DEFAULT_STAGE_WEIGHTS.get(stage, 0.5)

            for layer, layer_boost in layer_priority_boost.items():
                layer_dir = self.vault_root / stage.value / layer.value
                if not layer_dir.exists():
                    continue

                for md_file in layer_dir.glob("*.md"):
                    artifact_id = md_file.stem
                    if artifact_id in seen_ids:
                        continue  # 已被更高成熟度（如 gold）的同名知识覆盖，跳过低层级副本

                    try:
                        content = md_file.read_text(encoding="utf-8")
                    except OSError:
                        continue

                    doc_tokens = self._tokenize(content)
                    if not doc_tokens:
                        continue

                    overlap = len(query_tokens & doc_tokens)
                    if overlap == 0:
                        continue

                    # 综合得分 = 词元召回率 * 生命周期可信度权重 * 抽象层密度加权
                    recall_ratio = overlap / len(query_tokens)
                    final_score = recall_ratio * stage_weight * layer_boost

                    seen_ids.add(artifact_id)
                    scored_candidates.append((final_score, artifact_id))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return [aid for _, aid in scored_candidates[: self.top_k]]

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """轻量级中英文混合分词器（兼容中文双字滑窗与英文/代码标识符提取）"""
        lowered = text.lower()
        # 提取英文单词、数字与下划线标识符（如 pipeline_envelope, redis）
        en_tokens = set(re.findall(r"[a-z0-9_]{2,}", lowered))
        # 提取连续中文片段并生成 2-gram 词元（零第三方分词库依赖）
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
    # 3. 生命周期治理工具（支持人工审核与闭环验证晋升）
    # ------------------------------------------------------------------

    def promote_artifact(
        self,
        artifact_id: str,
        layer: WikiArtifactLayer,
        from_stage: WikiMaturityStage,
        to_stage: WikiMaturityStage,
    ) -> Optional[str]:
        """将知识卡片在生命周期目录间安全迁移（如 debug -> release 或 release -> gold）。
        得益于逻辑 ID 双链机制，物理文件迁移后全库引用零断链。
        """
        src_rel = self.build_artifact_relpath(from_stage, layer, artifact_id)
        dst_rel = self.build_artifact_relpath(to_stage, layer, artifact_id)
        src_path = self.vault_root / src_rel
        dst_path = self.vault_root / dst_rel

        if not src_path.exists():
            logger.warning("[%s] 晋升跳过：源文件不存在 %s", self.BACKEND_TYPE, src_rel)
            return None

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        logger.info("[%s] 知识晋升完成: %s -> %s", self.BACKEND_TYPE, src_rel, dst_rel)
        return dst_rel

    # ------------------------------------------------------------------
    # 异步内容水合加载（实现 BaseKnowledgeStorage._fetch_contents_by_ids）
    # ------------------------------------------------------------------

    async def _fetch_contents_by_ids(self, artifact_ids: List[str]) -> str:
        """根据知识 ID 列表异步加载对应的 Markdown 卡片全文"""
        return await asyncio.to_thread(self._sync_load_contents, artifact_ids)

    def _sync_load_contents(self, artifact_ids: List[str]) -> str:
        sections: List[str] = []

        for aid in artifact_ids:
            found_text: Optional[str] = None
            # 按可信度权重优先级（gold > release > debug）查找最新有效版本
            for stage in self.allowed_retrieval_stages:
                for layer in WikiArtifactLayer:
                    target_path = self.vault_root / self.build_artifact_relpath(stage, layer, aid)
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

