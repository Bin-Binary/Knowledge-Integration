# /schemas/internal_knowledge/pipeline_envelope.py
from typing import List, Optional
from pydantic import Field

from schemas.base import ImmutableSchema
from schemas.internal_knowledge.resolve_problem import ResolveProblem
from schemas.internal_knowledge.source import SourceURI
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

    # 1. 【运用】环节：问题求解与缺口驱动
    problem_resolution: Optional[ResolveProblem] = Field(
        default=None, description="当前问题求解状态、已检索方案(resolutions)及知识缺口(remaining_gap)"
    )

    # 2. 【采集】环节：支持单个或由缺口路由出的多个目标SourceURI
    source_locators: List[SourceURI] = Field(
        default_factory=list,
        description=(
            "待采集的强类型数据源定位符列表."
            "由str升级为list以应对一个知识缺口可能需要去多个源"
            "静态任务直接传入；缺口驱动时由路由器填充"
            "避免下一轮问题依然未完全解决、产生新的remaining_gap时，采集器会误以为还有旧的source_locators而重复拉取上一轮的数据，必须清空source_locators"
        )
    )
    raw_infos: List[Information] = Field(
        default_factory=list, description=(
            "采集产出的原子信息片段集合"
            "进入第二轮循环时，raw_infos里可能还留着第一轮的切片"
            "为避免【组织】和【存储】重复处理第一轮已入库的数据，每轮【存储】完成后清空raw_infos[]"
        )
    )

    # 3. 【组织】环节：四阶知识加工产物
    labels: List[Labeling] = Field(
        default_factory=list,
        description=(
            "概念节点标注"
            "每轮【存储】完成后清空labels[]"
        )
    )
    relations: List[RelatingConcepts] = Field(
        default_factory=list, 
        description=(
            "语义关系网络;"
            "每轮【存储】完成后清空relations[]"
        )
    )
    complexes: List[Ontology] = Field(
        default_factory=list, 
        description=(
            "聚拢成型的知识闭环体"
            "每轮【存储】完成后清空complexes[]"
        )
    )

    # 4. 【存储】环节：多后端落盘状态
    storage_receipts: List[StorageReceipt] = Field(
        default_factory=list, description="各存储后端的落盘回执列表"
    )
