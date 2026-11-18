# /schemas/internal_knowledge/set_of_interrelated_entities.py
"""Set_of_interrelated_entities(子图/本体)数据模型
知识组织环节产物，将多个相关 Labeling 及 RelatingConcepts 聚拢为一个高内聚的知识闭环体
对应FrameNet v17 Set_of_interrelated_entities的FE同构映射：
    Core FE:
        Component_entities    -> `label_ids` + `relation_ids` (共同构成完整子图拓扑)
        Complex               -> `complex_id`
    Extra-Thematic FE:
        Descriptor            -> `description` (宏观子图摘要，区别于微观节点标签) 这个感觉和labeling是一个意思，为了检索？但怎么才能和labeling不冲突呢？ 同构异形体？
        Possessor             -> [设计忽略] 不在本模型中表示

"""
from typing import List, Optional
from pydantic import Field, field_validator
from schemas.base import ImmutableSchema

class SetOfInterrelatedEntities(ImmutableSchema):
    """内聚的知识形态：由若干概念节点及其相互关系边构成的完整子图"""

    complex_id: str = Field(..., min_length=1, description="知识闭环体ID")
    label_ids: List[str] = Field(default_factory=list, description="组成该知识形态的概念节点ID集合")
    """缺失'relation_ids'会导致知识闭环体就退化成了一个无序集合，丢失了边的关系"""
    relation_ids: List[str] = Field(default_factory=list, description="连接上述概念节点的语义边ID集合")
    """这个参数和`Labeling.label`一样，为了检索。但是并不冲突，属于不同粒度的[功能同构]
    `Labeling.label`（微观节点标签）：对单个原始片段（Information）的特征提取,例如从一句话中抽出的 <事件：数据库宕机>、<实体：Redis>
    `descriptor`（宏观子图摘要）：对一整个关系网络（Complex）的整体定性或摘要。例如:
    “Redis内存满 -> 触发淘汰 -> 缓存穿透 -> 数据库宕机”这 4 个节点和 3 条边打包后，赋予整个子图一个宏观描述：“一次典型的缓存雪崩生产事故复盘”
    """
    descriptor: Optional[str] = Field(default=None, description="对该复杂整体的宏观概括/摘要（用于子图级检索）")
    

    @field_validator("label_ids", "relation_ids", mode="before")
    @classmethod
    def coerce_none_components_to_list(cls, v: Optional[List[str]]) -> List[str]:
        """容错：null 转为空列表。"""
        return v if v is not None else []
