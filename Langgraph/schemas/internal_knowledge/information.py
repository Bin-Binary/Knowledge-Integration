# /schemas/internal_knowledge/information.py
from typing import Optional
from pydantic import Field, field_serializer

from schemas.base import ImmutableSchema
from schemas.internal_knowledge.source_uri import SourceScheme, SourceURI

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

    info_id: str = Field(
        ..., 
        min_length=1, 
        description="全局唯一主键，供下游 Labeling 溯源（缺失将导致节点孤立）", 
        json_schema_extra={"frontmatter": True}
    )
    information: str = Field(
        ..., 
        min_length=1, 
        description="知识的原始符号内容"
    )
    cognizer_id: Optional[str] = Field(
        default=None, 
        description="归属者或采集主体标识", 
        json_schema_extra={"frontmatter": True}
    )
    topic: Optional[str] = Field(
        default=None, 
        min_length=1, 
        description="所属主题或领域", 
        json_schema_extra={"frontmatter": True}
    )
    source: Optional[SourceURI] = Field(
        default=None,
        description="强类型结构化数据源定位符",
        json_schema_extra={"frontmatter": True}
    )

    @field_serializer("source")
    def serialize_source_uri(self, uri: Optional[SourceURI]) -> Optional[str]:
        """导出 Frontmatter 或 JSON 时自动序列化为标准紧凑 URI 字符串"""
        if uri is None:
            return None
        anchor = f"#{uri.anchor}" if uri.anchor else ""
        if uri.scheme == SourceScheme.REPO:
            rev = f"#{uri.revision}" if uri.revision else ""
            sub = f":{uri.subpath}" if uri.subpath else ""
            return f"repo:{uri.location}{rev}{sub}{anchor}"
        if uri.scheme == SourceScheme.FILE and uri.location.startswith("."):
            return f"file:{uri.location}{anchor}"
        return f"{uri.scheme.value}://{uri.location}{anchor}"

    def _render_body(self) -> str:
        """渲染正文：固定使用一级标题 # Information 并以代码块高保真包裹原始符号内容"""
        # 动态计算安全的围栏长度，防止 self.information 内部本身包含 ``` 时破坏 Markdown 结构
        fence = "```"
        while fence in self.information:
            fence += "`"

        return f"# Information\n\n{fence}\n{self.information}\n{fence}"
