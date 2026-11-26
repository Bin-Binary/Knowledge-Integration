# /schemas/internal_knowledge/pipeline_envelope.py
from typing import Any, List, Optional
from pydantic import Field, field_validator

from schemas.base import ImmutableSchema
from schemas.internal_knowledge.resolve_problem import ResolveProblem
from schemas.internal_knowledge.source_uri import SourceURI
from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.labeling import Labeling
from schemas.internal_knowledge.relating_concepts import RelatingConcepts
from schemas.internal_knowledge.ontology import Ontology


class StorageReceipt(ImmutableSchema):
    """存储后端落盘回执（内聚辅助结构，支持多异构存储同时写入的状态追踪）"""
    backend_type: str = Field(..., description="存储后端标识（如 neo4j, milvus, local_fs）")
    saved_locations: List[str] = Field(default_factory=list, description="落盘物理路径或记录ID")
    success: bool = Field(default=True, description="是否写入成功")


class PipelineEnvelope(ImmutableSchema):
    """全链路统一传输载体（贯穿 运用 <-> 采集 -> 组织 -> 存储）"""
    trace_id: str = Field(..., min_length=1, description="全链路闭环追踪ID")
    iteration: int = Field(default=0, ge=0, description="当前闭环迭代轮次（防止产生新缺口无法收敛时死循环）")
    max_iterations: int = Field(default=3, ge=1, description="允许的最大闭环迭代上限")

    # 1. 【运用】环节：问题求解与缺口驱动
    problem_resolution: Optional[ResolveProblem] = Field(
        default=None, description="当前问题求解状态、已检索方案(resolutions)及知识缺口(remaining_gap)"
    )

    # 2. 【采集】环节：支持单个或由缺口路由出的多个目标SourceURI
    source_locators: List[SourceURI] = Field(
        default_factory=list,
        description="待采集的强类型数据源定位符列表（每轮存储后清空，防止下一轮重复拉取旧源）",
    )
    raw_infos: List[Information] = Field(
        default_factory=list,
        description="采集产出的原子信息片段集合（每轮存储后清空，防止重复组织与入库）",
    )

    # 3. 【组织】环节：四阶知识加工产物
    labels: List[Labeling] = Field(
        default_factory=list, description="概念节点标注（每轮存储后清空）"
    )
    relations: List[RelatingConcepts] = Field(
        default_factory=list, description="语义关系网络（每轮存储后清空）"
    )
    complexes: List[Ontology] = Field(
        default_factory=list, description="聚拢成型的知识闭环体（每轮存储后清空）"
    )

    # 4. 【存储】环节：多后端落盘状态（跨轮次累加保留）
    storage_receipts: List[StorageReceipt] = Field(
        default_factory=list, description="各存储后端的落盘回执列表"
    )

    @field_validator(
        "source_locators", "raw_infos", "labels", "relations", "complexes", "storage_receipts",
        mode="before",
    )
    @classmethod
    def coerce_none_lists(cls, v: Optional[List[Any]]) -> List[Any]:
        """容错：防止外部显式传入 null 导致类型校验失败"""
        return v if v is not None else []

    @property
    def can_continue_loop(self) -> bool:
        """纯只读状态判定：是否仍允许进入下一轮缺口采集闭环"""
        return self.iteration < self.max_iterations

    def advance_to_next_iteration(self) -> "PipelineEnvelope":
        """纯函数状态跃迁：单轮【存储】落盘完成后调用。
        清空本轮暂存工作区（locators/raw_infos/labels/relations/complexes），
        保留 problem_resolution 与历史 storage_receipts，并将轮次 +1。
        """
        return self.model_copy(
            update={
                "iteration": self.iteration + 1,
                "source_locators": [],
                "raw_infos": [],
                "labels": [],
                "relations": [],
                "complexes": [],
            }
        )
