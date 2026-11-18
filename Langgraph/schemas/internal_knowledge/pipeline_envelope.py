# /schemas/internal_knowledge/pipeline_envelope.py
from typing import List, Optional
from pydantic import Field

from schemas.base import ImmutableSchema
from schemas.internal_knowledge.resolve_problem import ResolveProblem
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

    # 1. 【运用】环节：问题求解与缺口驱动
    problem_resolution: Optional[ResolveProblem] = Field(
        default=None, description="当前问题求解状态、已检索方案(means)及知识缺口(remaining_gap)"
    )

    # 2. 【采集】环节：数据源定位符
    source_locator: Optional[str] = Field(
        default=None, description="数据源定位符（静态采集时必填；缺口驱动时可由调度器路由填入）"
    )
    raw_infos: List[Information] = Field(
        default_factory=list, description="采集产出的原子信息片段集合"
    )

    # 3. 【组织】环节：四阶知识加工产物
    labels: List[Labeling] = Field(default_factory=list, description="概念节点标注")
    relations: List[RelatingConcepts] = Field(default_factory=list, description="语义关系网络")
    complexes: List[Ontology] = Field(default_factory=list, description="聚拢成型的知识闭环体")

    # 4. 【存储】环节：多后端落盘状态
    storage_receipts: List[StorageReceipt] = Field(
        default_factory=list, description="各存储后端的落盘回执列表"
    )
