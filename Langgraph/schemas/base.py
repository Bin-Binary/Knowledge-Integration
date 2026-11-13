# /schemas/base.py
from pydantic import BaseModel, ConfigDict

class ImmutableSchema(BaseModel):
    """全局不可变数据模型基类：开启严格类型校验与只读保护"""
    model_config = ConfigDict(
        frozen=True,                 # 实例创建后不可修改（替代 dataclass(frozen=True)）
        extra="forbid",              # 禁止传入未定义的冗余字段，防止静默拼写错误
        populate_by_name=True,
        str_strip_whitespace=True    # 自动去除字符串首尾多余空白
    )

class LLMOutputSchema(BaseModel):
    """大模型输出解析专用基类：禁止修改、自动忽略冗余字段。"""
    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True
    )
