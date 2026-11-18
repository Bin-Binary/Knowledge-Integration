# /schemas/internal_knowledge/pipelin_envenlope.py
from typing import List
from pydantic import BaseModel, Field

from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.labeling import Labeling
from schemas.internal_knowledge.relating_concepts import RelatingConcepts
from schemas.internal_knowledge.ontology import Ontology

class PipelineEnvelope(BaseModel):
    """知识构建数据流转封装（仅用于从采集->组织->存储的知识形态传递）
    四层模型通过ID引用，进行追溯的链路：
    Information (info_id) ⬅️ Labeling (label_id, info_id) ⬅️ RelatingConcepts (relation_id, label_1_id, label_2_id) ⬅️ Ontology (complex_id, label_ids[], relation_ids[])
    """
    trace_id: str = Field(..., description="单次知识构建任务的追踪ID")
    
    # 阶段1：原始输入（1条）
    raw_info: Information
    
    # 阶段2：概念节点标注（多条，通过info_id关联[阶段1]的raw_info）
    labels: List[Labeling] = Field(default_factory=list)
    
    # 阶段3：语义关系网络（多条，通过label_1_id/label_2_id关联[阶段2]labels）
    relations: List[RelatingConcepts] = Field(default_factory=list)
    
    # 阶段4：聚拢成型的知识闭环体（按需生成，通过label_ids + relation_ids锁定子图）
    complexes: List[Ontology] = Field(default_factory=list)
