# /components/internal_knowledge/storage/base_storage.py
import logging
import time
from abc import ABC, abstractmethod
from pathlib import PurePosixPath
from typing import ClassVar, Dict, List, Tuple

from components.internal_knowledge.schemas.pipeline_envelope import PipelineEnvelope, StorageReceipt
from components.internal_knowledge.schemas.wiki_governance import WikiArtifactLayer, WikiMaturityStage
from components.internal_knowledge.protocols import KnowledgeStorageProtocol
from infra import emit_component_status, KnowledgePipelineError

logger = logging.getLogger(__name__)


class BaseKnowledgeStorage(ABC, KnowledgeStorageProtocol):
    """4. 【存储】环节通用抽象基类（实现 KnowledgeStorageProtocol）。

    存储治理规范（3层生命周期 × 4层抽象粒度）：
        物理矩阵：`<vault_root>/<stage>/<layer>/<artifact_id>.md`
        - 生命周期：`debug/`（AI 缓冲区） -> `release/`（人工审核/准生产） -> `gold/`（求解闭环验证）
        - 抽象粒度：`information/`（L1 切片） -> `labeling/`（L2 概念） -> `relating/`（L3 关系） -> `ontology/`（L4 本体）
        - 治理原则：自动化产物默认仅写 `debug/`；跨层引用仅用逻辑 ID 防断链；检索按 `gold > release > debug` 加权。
    """

    BACKEND_TYPE: ClassVar[str] = "unknown"

    DEFAULT_STAGE_WEIGHTS: ClassVar[Dict[WikiMaturityStage, float]] = {
        WikiMaturityStage.GOLD: 1.0,     # 黄金区：生产闭环已验证
        WikiMaturityStage.RELEASE: 0.8,  # 准生产区：人工审核/编写
        WikiMaturityStage.DEBUG: 0.4,    # 缓冲区：AI 初始生成
    }

    DEFAULT_RETRIEVABLE_STAGES: ClassVar[Tuple[WikiMaturityStage, ...]] = (
        WikiMaturityStage.GOLD,
        WikiMaturityStage.RELEASE,
        WikiMaturityStage.DEBUG,
    )

    @staticmethod
    def build_artifact_relpath(
        stage: WikiMaturityStage,
        layer: WikiArtifactLayer,
        artifact_id: str,
        ext: str = ".md",
    ) -> str:
        """生成标准化知识产物相对路径并校验防路径穿越（如 'debug/ontology/ont_xxx.md'）"""
        clean_id = artifact_id.strip()
        if (
            not clean_id
            or "/" in clean_id
            or "\\" in clean_id
            or ".." in clean_id
            or PurePosixPath(clean_id).name != clean_id
        ):
            raise ValueError(f"非法的 artifact_id: {artifact_id!r}")
        filename = clean_id if clean_id.endswith(ext) else f"{clean_id}{ext}"
        return str(PurePosixPath(stage.value) / layer.value / filename)

    async def save(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """统一异步持久化入口：检查负载 -> 隔离写入 debug 区 -> 追加 StorageReceipt"""
        has_payload = any([
            envelope.raw_infos,
            envelope.labels,
            envelope.relations,
            envelope.complexes,
        ])
        if not has_payload:
            logger.info("[%s] 无有效知识产物需要落盘，跳过存储 (trace_id=%s)", self.BACKEND_TYPE, envelope.trace_id)
            return envelope

        total_items = (
            len(envelope.raw_infos)
            + len(envelope.labels)
            + len(envelope.relations)
            + len(envelope.complexes)
        )
        start_ts = time.perf_counter()
        logger.info(
            "[%s] 开始知识落盘 (trace_id=%s, total=%d: infos=%d, labels=%d, relations=%d, complexes=%d)",
            self.BACKEND_TYPE,
            envelope.trace_id,
            total_items,
            len(envelope.raw_infos),
            len(envelope.labels),
            len(envelope.relations),
            len(envelope.complexes),
        )
        emit_component_status(
            f"【存储】：正在将 {total_items} 项多形态知识产物写入隔离区（{self.BACKEND_TYPE}）...\n",
        )

        try:
            saved_locations = await self._persist_artifacts(envelope)
            receipt = StorageReceipt(
                backend_type=self.BACKEND_TYPE,
                saved_locations=saved_locations,
                success=True,
            )
        except KnowledgePipelineError:
            raise
        except Exception as exc:
            logger.exception("[%s] 知识落盘失败 (trace_id=%s)", self.BACKEND_TYPE, envelope.trace_id)
            raise KnowledgePipelineError(
                message=f"知识产物持久化失败 ({self.BACKEND_TYPE}): {exc}",
                stage="storage",
                user_friendly_hint="知识库写入存储介质时发生异常，请检查磁盘权限或存储服务状态。",
                metadata={
                    "trace_id": envelope.trace_id,
                    "backend_type": self.BACKEND_TYPE,
                    "error_type": type(exc).__name__,
                },
            ) from exc

        logger.info(
            "[%s] 知识落盘完成 (trace_id=%s): 耗时=%.2fs, 生成凭证数=%d",
            self.BACKEND_TYPE,
            envelope.trace_id,
            time.perf_counter() - start_ts,
            len(saved_locations),
        )
        emit_component_status(
            f"【存储】：持久化落盘完成，共生成 {len(saved_locations)} 条存储凭证。\n",
        )

        return envelope.model_copy(
            update={"storage_receipts": [*envelope.storage_receipts, receipt]}
        )

    async def retrieve(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """统一异步记忆召回入口：提取 problem -> 按生命周期权重检索 -> 去重回填 resolutions"""
        resolution = envelope.problem_resolution
        if not resolution:
            msg = "检索环节失败：PipelineEnvelope 中缺失 problem_resolution 上下文"
            logger.warning("[%s] %s (trace_id=%s)", self.BACKEND_TYPE, msg, envelope.trace_id)
            raise KnowledgePipelineError(
                message=msg,
                stage="retrieval",
                metadata={"trace_id": envelope.trace_id},
            )

        start_ts = time.perf_counter()
        emit_component_status(
            "【检索】：正在按成熟度权重（gold > release > debug）检索关联知识...\n",
        )

        # 底层模型/网络异常直接向上透传给 DEFAULT_EXCEPTION_SPECS 恢复节点
        recalled_ids = await self._query_knowledge_ids(resolution.problem, envelope)
        elapsed = time.perf_counter() - start_ts

        if not recalled_ids:
            logger.info("[%s] 知识检索完成：未命中条目 (trace_id=%s, 耗时=%.2fs)", self.BACKEND_TYPE, envelope.trace_id, elapsed)
            emit_component_status("【检索】：暂未命中匹配的已有知识条目。\n")
            return envelope

        merged_resolutions = list(dict.fromkeys([*resolution.resolutions, *recalled_ids]))
        updated_resolution = resolution.model_copy(
            update={"resolutions": merged_resolutions}
        )

        logger.info(
            "[%s] 知识检索完成 (trace_id=%s): 耗时=%.2fs, 本次召回=%d, 累计去重=%d",
            self.BACKEND_TYPE,
            envelope.trace_id,
            elapsed,
            len(recalled_ids),
            len(merged_resolutions),
        )
        emit_component_status(
            f"【检索】：成功召回 {len(recalled_ids)} 条相关知识 ID。\n",
        )

        return envelope.model_copy(
            update={"problem_resolution": updated_resolution}
        )

    async def load_contents(self, artifact_ids: List[str]) -> str:
        """统一异步内容加载入口：空列表拦截 -> 保序去重 -> 委托子类水合正文"""
        if not artifact_ids:
            return ""

        deduped_ids = list(dict.fromkeys(aid.strip() for aid in artifact_ids if aid and aid.strip()))
        if not deduped_ids:
            return ""

        start_ts = time.perf_counter()
        content = await self._fetch_contents_by_ids(deduped_ids)
        logger.debug(
            "[%s] 内容水合完成: 请求ID数=%d, 返回字符数=%d, 耗时=%.3fs",
            self.BACKEND_TYPE,
            len(deduped_ids),
            len(content),
            time.perf_counter() - start_ts,
        )
        return content

    @abstractmethod
    async def _persist_artifacts(self, envelope: PipelineEnvelope) -> List[str]:
        """子类实现：遵循写入隔离设计将四层产物落盘至 debug/，返回相对路径或记录 ID 列表"""
        ...

    @abstractmethod
    async def _query_knowledge_ids(self, problem: str, envelope: PipelineEnvelope) -> List[str]:
        """子类实现：遵循检索加权设计，按 gold > release > debug 优先级召回关联知识 ID"""
        ...

    @abstractmethod
    async def _fetch_contents_by_ids(self, artifact_ids: List[str]) -> str:
        """子类实现：根据去重后的知识 ID 列表读取并水合为可读上下文文本"""
        ...
