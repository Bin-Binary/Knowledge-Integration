# /schemas/internal_knowledge_base_building/information.py
"""Information数据模型。
知识的符号表示，是知识库最细粒度的原始符号载体。
对应FrameNet v17 Information的FE同构映射：
    Core FE:
        Information         -> `information`
        Cognizer            -> `cognizer_id`
        Topic               -> `topic`
    Peripheral FE:
        Source              -> `url`
        Means_of_gathering -> [设计忽略] 采集策略（如爬取/订阅/对话）属于流程行为而非静态数据，不在本模型中表示

"""
from typing import Optional
from pydantic import Field, ConfigDict
from schemas.base import ImmutableSchema

class InformationSchema(ImmutableSchema):
    """知识内容的符号描述
    开启 extra='forbid'，防止调用方误传`gather_strategies`参数
    """

    model_config = ConfigDict(extra='forbid')
    information: str = Field(..., min_length=1, description='知识的原始符号内容')
    cognizer_id: Optional[str] = Field(default=None, description='归属者标识')
    topic: Optional[str] = Field(default=None, min_length=1, description='关于的主题/领域')
    source: Optional[str] = Field(default=None, description='来源定位符')
