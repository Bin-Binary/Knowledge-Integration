# /schemas/internal_knowledge/information.py
from typing import Optional
from pydantic import Field, ConfigDict
from schemas.base import ImmutableSchema

class Information(ImmutableSchema):
    """Information（信息片段）数据模型：知识库最细粒度的不可变原始符号载体。

    FrameNet v17 (Information) FE 映射:
        - Information        -> `information`
        - Cognizer           -> `cognizer_id`
        - Topic              -> `topic`
        - Source             -> `source`
        - Means_of_gathering -> [忽略] 采集策略属于流程行为，不在静态模型中表示

    工程备注:
        1. 保持高保真原始符号切片，不在本层提前做语义总结。
        2. 代码仓场景下由 Git Diff 驱动增量更新，仅重建变更文件/函数对应的切片。
    """
    model_config = ConfigDict(extra="forbid")

    info_id: str = Field(..., min_length=1, description="全局唯一主键，供下游 Labeling 溯源（缺失将导致节点孤立）")
    information: str = Field(..., min_length=1, description="知识的原始符号内容")
    cognizer_id: Optional[str] = Field(default=None, description="归属者或采集主体标识")
    topic: Optional[str] = Field(default=None, min_length=1, description="所属主题或领域")
    source: Optional[str] = Field(default=None, description="数据源定位符（如文件路径、URL）")
