# /schemas/internal_knowledge/relating_concepts.py
"""Relating_concepts（语义边）数据模型。
知识组织环节产物，通过 LLM 语义关系抽取、规则共现或图推理，将离散的 Labeling 连接为有向网络边。

对应 FrameNet v17 Relating_concepts 的 FE 同构映射：
    Core FE:
        Concept_1           -> `label_1_id`
        Concept_2           -> `label_2_id`
        Evidence            -> [设计忽略] 当前不额外引入复杂度，不在本模型中表示
        Concepts            -> [设计忽略] 当前不额外引入复杂度，不在本模型中表示
    Peripheral FE:
        Point_of_view       -> [设计忽略] 当前不额外引入复杂度，不在本模型中表示
        Degree              -> `degree`
        Specification       -> `relationship_type`（边的语义类型规约）
"""
from typing import Optional, Union
from pydantic import Field

from schemas.base import ImmutableSchema, DocumentedEnum
from schemas.internal_knowledge.domain.code_relation_type import CodeRelationType

class GeneralRelationType(DocumentedEnum):
    """通用语义关系"""
    CAUSAL = ("causal", "通用语义", "因果关系（A 导致 B）")
    IS_A = ("is_a", "通用语义", "继承/分类关系（A 是一种 B）")
    PART_OF = ("part_of", "通用语义", "组成/包含关系（A 是 B 的一部分）")
    PRECEDES = ("precedes", "通用语义", "时序/前置关系（A 发生在 B 之前）")
    ASSOCIATED_WITH = ("associated", "通用语义", "通用弱关联")

# 声明全局合法关系联合类型（支持通用语义与领域专属关系扩展）
AnyRelationType = Union[GeneralRelationType, CodeRelationType]

class RelatingConcepts(ImmutableSchema):
    """基于标签（Labeling）构建概念间网络结构，形成可推理的有向关系边"""

    relation_id: str = Field(..., min_length=1, description="语义边全局唯一标识（缺失将导致边无法被检索或聚合）")
    label_1_id: str = Field(..., min_length=1, description="有向边的起点概念节点 ID（Concept_1）")
    label_2_id: str = Field(..., min_length=1, description="有向边的终点概念节点 ID（Concept_2）")
    relationship_type: AnyRelationType = Field(..., description="有向边的关系类型（通用语义或代码仓专属关系）")
    degree: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="关联强度或置信度 [0.0, 1.0]")
