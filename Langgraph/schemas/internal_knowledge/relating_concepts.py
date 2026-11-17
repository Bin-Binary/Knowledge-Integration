# /schemas/internal_knowledge/relating_concepts.py
"""Relating_concepts(语义边)数据模型。
知识组织环节产物，通过LLM语义关系抽取、规则共现或图推理，将离散的Labeling连接为网络边。

一个Concept_1通过某种Evidence与Concept_2相关联，把两个标签/概念结成网络边（edge）。
对应FrameNet v17 Relating_concepts的FE同构映射：
    Core FE:
        Concept_1           -> `label_1_id`
        Concept_2           -> `label_2_id`
        Evidence            -> [设计忽略] 当前不额外引入复杂度,不在本模型中表示
        Concepts            -> [设计忽略] 当前不额外引入复杂度,不在本模型中表示
    Peripheral FE:
        Point_of_view       -> `point_of_view`
        Degree              -> `degree`
        Specification       -> `relationship_type`        # 边的类型/进一步规约（如"因果链接"）

"""
from enum import Enum
from typing import List, Optional
from pydantic import Field, field_validator
from schemas.base import ImmutableSchema

class RelationshipType(str, Enum):
    """复用知识图谱的关系枚举，完备性和后续扩展同步增加"""
    CAUSAL = "causal"               # 因果关系（A 导致 B）
    IS_A = "is_a"                   # 继承/分类关系（A 是一种 B）
    PART_OF = "part_of"             # 组成/包含关系（A 是 B 的一部分）
    PRECEDES = "precedes"           # 时序/前置关系（A 发生在 B 之前）
    ASSOCIATED_WITH = "associated"  # 通用弱关联

class RelatingConcepts(ImmutableSchema):
    """基于标签（Labeling）构建概念间网络结构，形成可推理的关系边"""

    """缺失'relation_id'会导致这个边不能被找到"""
    relation_id: str = Field(..., min_length=1, description="语义边唯一标识")
    label_1_id: Optional[str] = Field(..., min_length=1, description='被关联的label_1')
    label_2_id: Optional[str] = Field(..., min_length=1, description='被关联的label_2')
    specification: Optional[RelationshipType] = Field(..., description="关系")
    degree: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="关联强度 [0,1]")

    @field_validator("concepts")
    @classmethod
    def coerce_none_concepts_to_list(cls, v: Optional[List[str]]) -> List[str]:
        """容错：null 转为空列表。"""
        return v if v is not None else []
