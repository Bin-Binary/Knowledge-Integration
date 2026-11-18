# /schemas/internal_knowledge/labeling.py
from typing import Optional
from pydantic import Field
from schemas.base import ImmutableSchema

class Labeling(ImmutableSchema):
    """Labeling（概念节点）数据模型：对 Information 抽取特征并赋予可检索的分类标签。

    FrameNet v17 (Labeling) FE 映射:
        - Label   -> `label`
        - Time    -> `timestamp`
        - Speaker / Entity / Medium / Place -> [忽略] 简化模型，不单独建模
    """
    label_id: str = Field(..., min_length=1, description="概念节点唯一标识")
    info_id: str = Field(..., min_length=1, description="关联的原始 Information ID，用于从概念节点溯源回原文")
    label: str = Field(..., min_length=1, description="对该实体的分类化描述或语义判断（如 <实体：Redis>）")
    timestamp: Optional[float] = Field(default=None, description="标注发生的时间戳")
