# /schemas/base.py
from pydantic import BaseModel, ConfigDict
from typing import Any, List, Set, Type, Union, get_args, get_origin
from enum import Enum

class SelfIntrospectable:
    """数据模型自省混入类（Mixin）：支持递归展开嵌套子模型的 Prompt 导出器"""

    @classmethod
    def _format_type_name(cls, annotation: Any) -> str:
        """将复杂的 typing 注解格式化为干净易读的类型名称"""
        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin is Union and type(None) in args:
            non_none_args = [cls._format_type_name(a) for a in args if a is not type(None)]
            return f"Optional[{', '.join(non_none_args)}]"

        if origin is not None:
            origin_name = getattr(origin, "__name__", str(origin))
            if args:
                args_str = ", ".join(cls._format_type_name(a) for a in args)
                return f"{origin_name}[{args_str}]"
            return origin_name

        return getattr(annotation, "__name__", str(annotation))

    @classmethod
    def _extract_sub_models(cls, annotation: Any) -> List[Type["SelfIntrospectable"]]:
        """递归提取字段类型中包含的 SelfIntrospectable 子模型类"""
        found: List[Type["SelfIntrospectable"]] = []
        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin is not None:
            for arg in args:
                found.extend(cls._extract_sub_models(arg))
        elif isinstance(annotation, type) and issubclass(annotation, SelfIntrospectable) and issubclass(annotation, BaseModel):
            found.append(annotation)

        return found

    @classmethod
    def to_prompt_guide(cls, _visited: Set[Type[Any]] | None = None) -> str:
        """一键导出当前数据模型及其引用子模型的完整字段说明"""
        if not hasattr(cls, "model_fields"):
            raise TypeError(f"{cls.__name__} 必须与 Pydantic BaseModel 配合使用")

        visited = _visited if _visited is not None else set()
        visited.add(cls)

        doc = (cls.__doc__ or "数据模型").strip().splitlines()
        lines = [f"### {cls.__name__} ({doc})"]
        sub_models_to_render: List[Type["SelfIntrospectable"]] = []

        for name, field_info in cls.model_fields.items():
            type_name = cls._format_type_name(field_info.annotation)
            req_tag = "必填" if field_info.is_required() else "可选"
            
            # 兼容读取可选的 category 标签（若有）
            extra = field_info.json_schema_extra if isinstance(field_info.json_schema_extra, dict) else {}
            cat_tag = f" [{extra['category']}]" if "category" in extra else ""
            
            desc = field_info.description or "无额外说明"
            lines.append(f"- `{name}` (`{type_name}`, {req_tag}){cat_tag}: {desc}")

            # 收集当前字段引用的子模型
            for sub_cls in cls._extract_sub_models(field_info.annotation):
                if sub_cls not in visited and sub_cls not in sub_models_to_render:
                    sub_models_to_render.append(sub_cls)

        # 依次在下方附加展开引用的子模型说明书
        sections = ["\n".join(lines)]
        for sub_cls in sub_models_to_render:
            sections.append(sub_cls.to_prompt_guide(_visited=visited))

        return "\n\n".join(sections)

class ImmutableSchema(BaseModel, SelfIntrospectable):
    """全局不可变数据模型基类：开启严格类型校验与只读保护"""
    model_config = ConfigDict(
        frozen=True,                 # 实例创建后不可修改（替代 dataclass(frozen=True)）
        extra="forbid",              # 禁止传入未定义的冗余字段，防止静默拼写错误
        populate_by_name=True,
        str_strip_whitespace=False    # 自动去除字符串首尾多余空白
    )

class LLMOutputSchema(BaseModel, SelfIntrospectable):
    """大模型输出解析专用基类：禁止修改、自动忽略冗余字段。"""
    model_config = ConfigDict(
        frozen=True,
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=False
    )

class BoundaryRequestSchema(BaseModel, SelfIntrospectable):
    """外部API边界请求基类：只读保护，但宽容处理上游新增的冗余字段"""
    model_config = ConfigDict(
        frozen=True,
        extra="ignore",              # 宽容原则：上游网关多传字段不报错，保证向后兼容
        populate_by_name=True,
        str_strip_whitespace=False   # 保留用户原始输入的首尾空格/缩进格式
    )

class DocumentedEnum(str, Enum):
    """支持分类与中文释义自省的枚举基类"""

    def __new__(cls, value: str, category: str, desc: str):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.category = category
        obj.desc = desc
        return obj

    @classmethod
    def to_prompt_guide(cls) -> str:
        """一键导出供LLM关系抽取使用的结构化说明"""
        return "\n".join(f"- `{e.value}` [{e.category}]: {e.desc}" for e in cls)
