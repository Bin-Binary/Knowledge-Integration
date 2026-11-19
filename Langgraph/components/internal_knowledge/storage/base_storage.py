# /components/internal_knowledge/storage/base_storage.py
import logging
from abc import ABC, abstractmethod
from pathlib import PurePosixPath
from typing import ClassVar, List, Dict

from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope, StorageReceipt
from schemas.internal_knowledge.wiki_governance import WikiArtifactLayer, WikiMaturityStage
from protocols.internal_knowledge import KnowledgeStorageProtocol

logger = logging.getLogger(__name__)

class BaseKnowledgeStorage(ABC, KnowledgeStorageProtocol):
    """4. 【存储】环节通用抽象基类（实现 KnowledgeStorageProtocol）。

    LLM-WIKI 存储治理与落盘规范（3层生命周期 × 4层抽象粒度）：
        物理目录矩阵：`<vault_root>/<stage>/<layer>/<artifact_id>.md`
        - 三层生命周期 (`WikiMaturityStage`)：
            1. `debug/`   : AI 自动生成的未审核知识缓冲区（高风险，允许试错）。
            2. `release/` : 经人工审核通过的 AI 产物，或人工直接编写的准生产知识。
            3. `gold/`    : 经真实生产问题求解闭环验证有效（outcome=SUCCESS）的黄金标准知识。
        - 四层知识形态 (`WikiArtifactLayer`，信息密度由低到高)：
            1. `information/` : L1 原始符号切片（采集即生成）。
            2. `labeling/`    : L2 概念节点（采集后生成 N >= 0 条）。
            3. `relating/`    : L3 有向语义边（labeling >= 2 且存在明确关联时生成）。
            4. `ontology/`    : L4 知识闭环体（多轮积累后低频聚拢生成）。

    三大核心落地与治理设计：
        1. 【写入隔离设计 (`save`)】：
           自动化流水线产出的所有新知识默认且仅允许落盘至 `debug/` 目录下，严禁直接覆盖或污染 `release/` 与 `gold/`。
        2. 【检索加权与跨层防断链 (`retrieve`)】：
           - 检索时应按成熟度赋予可信度权重（`gold` > `release` > `debug`），生产模式可配置仅检索 `release` 与 `gold`。
           - 跨文件引用必须严格使用全局唯一逻辑 ID（如 `[[lbl_101]]`、`info_id: "info_001"`），严禁硬编码物理相对路径，确保文件在 `debug -> release -> gold` 之间迁移时零断链。
        3. 【验证晋升与双向追溯 (`promote` / Traceability)】：
           - 自动晋升：当求解闭环达成 `outcome == SUCCESS` 时，触发晋升算子将本次命中的 `release/` 知识迁移归档至 `gold/`。
           - 双向追溯：自顶向下支持 `Ontology -> Relating/Labeling -> Information -> SourceURI` 推理展开；自底向上支持源文件变更时通过 `info_id` 反查上游节点实现局部图谱增量刷新。
    """

    # 子类必须声明的存储后端唯一标识（如 "local_markdown", "neo4j", "milvus"）
    BACKEND_TYPE: ClassVar[str] = "unknown"

    # 跨介质通用知识成熟度可信度权重（适用于文件系统目录分级、向量库 Payload 加权及图库节点过滤）
    DEFAULT_STAGE_WEIGHTS: ClassVar[Dict[WikiMaturityStage, float]] = {
        WikiMaturityStage.GOLD: 1.0,     # 黄金区：最高可信度（生产闭环已验证）
        WikiMaturityStage.RELEASE: 0.8,  # 准生产区：高可信度（人工审核/编写）
        WikiMaturityStage.DEBUG: 0.4,    # 缓冲区：低可信度（AI 初始生成，生产环境可配置过滤）
    }

    # ------------------------------------------------------------------
    # 标准路径与命名契约工具（消除硬编码，统一所有文件系统/对象存储子类）
    # ------------------------------------------------------------------

    @staticmethod
    def build_artifact_relpath(
        stage: WikiMaturityStage,
        layer: WikiArtifactLayer,
        artifact_id: str,
        ext: str = ".md",
    ) -> str:
        """生成标准化的知识产物相对路径（如 'debug/ontology/ont_cache_avalanche.md'）"""
        clean_id = artifact_id.strip()
        if not clean_id:
            raise ValueError("artifact_id 不能为空")
        filename = clean_id if clean_id.endswith(ext) else f"{clean_id}{ext}"
        return str(PurePosixPath(stage.value) / layer.value / filename)

    # ------------------------------------------------------------------
    # 核心模板方法（实现 KnowledgeStorageProtocol 契约）
    # ------------------------------------------------------------------

    async def save(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """统一异步持久化入口：检查有效负载 -> 隔离写入 debug 区 -> 追加 StorageReceipt"""
        has_payload = any([
            envelope.raw_infos,
            envelope.labels,
            envelope.relations,
            envelope.complexes,
        ])
        if not has_payload:
            return envelope

        try:
            saved_locations = await self._persist_artifacts(envelope)
            receipt = StorageReceipt(
                backend_type=self.BACKEND_TYPE,
                saved_locations=saved_locations,
                success=True,
            )
        except Exception as exc:
            logger.error(
                "[%s] 知识落盘失败 (trace_id=%s): %s",
                self.BACKEND_TYPE,
                envelope.trace_id,
                exc,
            )
            raise

        return envelope.model_copy(
            update={"storage_receipts": [*envelope.storage_receipts, receipt]}
        )

    async def retrieve(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """统一异步记忆召回入口：提取 problem -> 按生命周期权重检索 -> 去重回填 resolutions"""
        resolution = envelope.problem_resolution
        if not resolution:
            raise ValueError("检索环节失败：PipelineEnvelope中缺失 problem_resolution 上下文")

        recalled_ids = await self._query_knowledge_ids(resolution.problem, envelope)
        if not recalled_ids:
            return envelope

        # 保持顺序去重合并已有 resolutions 与新召回的知识 ID
        merged_resolutions = list(dict.fromkeys([*resolution.resolutions, *recalled_ids]))
        updated_resolution = resolution.model_copy(
            update={"resolutions": merged_resolutions}
        )

        return envelope.model_copy(
            update={"problem_resolution": updated_resolution}
        )

    @abstractmethod
    async def _persist_artifacts(self, envelope: PipelineEnvelope) -> List[str]:
        """子类必须实现的异步持久化核心逻辑：
        遵循【写入隔离设计】，默认将 raw_infos / labels / relations / complexes
        写入 `WikiMaturityStage.DEBUG` 对应的四层子目录中，返回落盘相对路径或记录 ID 列表。
        """
        ...

    @abstractmethod
    async def _query_knowledge_ids(self, problem: str, envelope: PipelineEnvelope) -> List[str]:
        """子类必须实现的异步检索核心逻辑：
        遵循【检索加权设计】，按 `gold > release > debug` 优先级召回关联的知识 ID 列表。
        """
        ...
