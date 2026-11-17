# /schemas/internal_knowledge/information.py
"""Information(信息片段)数据模型。
知识的符号表示，是知识库最细粒度的原始符号载体。
对应FrameNet v17 Information的FE同构映射：
    Core FE:
        Information         -> `information`
        Cognizer            -> `cognizer_id`
        Topic               -> `topic`
    Peripheral FE:
        Source              -> `source`
        Means_of_gathering  -> [设计忽略] 采集策略属于流程行为而非静态数据，不在本模型中表示
"""
from typing import Optional
from pydantic import Field, ConfigDict
from schemas.base import ImmutableSchema

class Information(ImmutableSchema):
    """知识内容的符号描述"""
    model_config = ConfigDict(extra='forbid')

    """缺失`info_id`,会导致Labeling变成了孤立的字典词条，全局唯一的主键供下游节点溯源"""
    info_id: str = Field(..., min_length=1, description='信息片段唯一标识（供下游节点溯源）')
    information: str = Field(..., min_length=1, description='知识的原始符号内容')
    cognizer_id: Optional[str] = Field(default=None, description='归属者标识')
    topic: Optional[str] = Field(default=None, min_length=1, description='关于的主题/领域')
    source: Optional[str] = Field(default=None, description='来源定位符')
