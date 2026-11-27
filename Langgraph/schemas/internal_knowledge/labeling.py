# /schemas/internal_knowledge/labeling.py
from typing import Optional, Dict, Any
from pydantic import Field
from schemas.base import ImmutableSchema, DocumentedEnum

class NodeCategory(DocumentedEnum):
    """通用概念节点元类型（保持领域无关的抽象度）"""
    ENTITY = ("entity", "实体", "具体的技术组件、类名、工具或业务对象（如 Redis）")
    CONCEPT = ("concept", "抽象概念", "设计模式、架构原则或理论机制（如 依赖倒置）")
    EVENT = ("event", "事件/动作", "具体的业务流转、状态变更或异常现象")
    RULE = ("rule", "规则/约束", "业务红线、校验条件或前置假设")

class Labeling(ImmutableSchema):
    """Labeling（概念节点）数据模型：对 Information 抽取特征并赋予可检索的分类标签。

    FrameNet v17 (Labeling) FE 映射:
        - Label   -> `label`
        - Time    -> `timestamp`
        - Speaker / Entity / Medium / Place -> [忽略] 简化模型，不单独建模
    """
    label_id: str = Field(..., min_length=1, description="概念节点唯一标识", json_schema_extra={"frontmatter": True})
    info_id: str = Field(..., min_length=1, description="关联的原始 Information ID，用于从概念节点溯源回原文", json_schema_extra={"frontmatter": True})
    category: NodeCategory = Field(default=NodeCategory.CONCEPT, description="概念节点的元分类, 方便过滤检索", json_schema_extra={"frontmatter": True})
    label: str = Field(..., min_length=1, description="对该实体的分类化描述或语义判断（如 <实体：Redis>）")
    timestamp: Optional[float] = Field(default=None, description="标注发生的时间戳", json_schema_extra={"frontmatter": True})
    # 显式增加富语义，防止上游调用 envelope.model_copy()、model_dump() 或跨节点反序列化，这个私有属性会静默丢失，导致下游渲染不出核心定义与触发判据
    rich_semantics: Dict[str, Any] = Field(default_factory=dict, exclude=True)    
