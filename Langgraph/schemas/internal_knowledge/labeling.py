# /schemas/internal_knowledge/labeling.py
"""Labeling(概念节点)数据模型
特征抽取后的产物，对Information(信息片段)打上分类标签，赋予其可检索的语义.

说话者用一个非约定俗成的Label（标签）指称一个Entity，该标签不是固定名，
而是对该实体进行分类化描述并借此表达判断。
对应FrameNet v17 Labeling的FE同构映射：
    Core FE:
        Speaker             -> [设计忽略] 不在本模型中表示
        Entity              -> [设计忽略] 不在本模型中表示
        Label               -> `label`
        Medium              -> [设计忽略] 不在本模型中表示
    Peripheral FE:
        Time                -> `timestamp`
        Place               -> [设计忽略] 不在本模型中表示

知识组织环节产出,例如：
<事件：数据库宕机>、<实体：Redis>、<过程>、<活动>.....
"""
from typing import Optional
from pydantic import Field

from schemas.base import ImmutableSchema
from schemas.internal_knowledge.information import Information

class Labeling(ImmutableSchema):
    """对采集获得的`Information`抽取特征并分类，产出可检索的标签描述"""
    label_id: str = Field(..., min_length=1, description="唯一标识")
    """需要这个唯一info_id, 才能从`概念节点`溯源回`原始文本`"""
    info_id: str = Field(..., min_length=1, description="Information(原始信息片段)ID")
    label: str = Field(..., min_length=1, description="对该实体的分类描述/判断")
    timestamp: Optional[float] = Field(default=None, description="标注发生时间戳")
