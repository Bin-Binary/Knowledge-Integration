# /schemas/internal_knowledge/artifacts/base.py
import hashlib
import json
import re
from typing import Any, Dict, Generic, List, Literal, Optional, Sequence, TypeVar, Union
from pydantic import Field

from schemas.base import ImmutableSchema

CoreT = TypeVar("CoreT", bound=ImmutableSchema)

# 全局 ID 严格正则：^(info|lbl|rel|ont)_[a-z0-9_]{3,60}$
ARTIFACT_ID_PATTERN = re.compile(r"^(info|lbl|rel|ont)_[a-z0-9_]{3,60}$")

# 允许的 7 个标准 Callout 标识符白名单
AllowedCalloutType = Literal["abstract", "quote", "note", "bug", "caution", "important", "tip"]


def build_compliant_artifact_id(
    prefix: Literal["info", "lbl", "rel", "ont"],
    semantic_slug: str,
    fingerprint_seed: Optional[str] = None,
) -> str:
    """生成 100% 符合 `^(info|lbl|rel|ont)_[a-z0-9_]{3,60}$` 的闭合 ID。"""
    clean_slug = re.sub(r"[^a-z0-9_]+", "_", semantic_slug.strip().lower()).strip("_")
    if clean_slug.startswith(f"{prefix}_"):
        clean_slug = clean_slug[len(prefix) + 1 :]
    if len(clean_slug) < 3:
        clean_slug = f"{clean_slug}_node".strip("_")

    if fingerprint_seed:
        short_hash = hashlib.sha256(fingerprint_seed.strip().encode("utf-8")).hexdigest()[:4]
        clean_slug = clean_slug[:55].rstrip("_")
        candidate = f"{prefix}_{clean_slug}_{short_hash}"
    else:
        clean_slug = clean_slug[:60].rstrip("_")
        candidate = f"{prefix}_{clean_slug}"

    if not ARTIFACT_ID_PATTERN.match(candidate):
        raise ValueError(f"无法生成合法的规范 ID: {candidate}")
    return candidate


class BaseArtifactView(ImmutableSchema, Generic[CoreT]):
    """20-wiki 四层物化视图公共基类（自动继承 core 元数据 + 精简正交 YAML）"""

    core: CoreT = Field(..., exclude=True, description="底层不可变核心实体")
    domain: Optional[str] = Field(
        default=None,
        description="所属业务域或架构域（跨目录正交过滤字段）",
        json_schema_extra={"frontmatter": True},
    )

    @staticmethod
    def validate_wiki_id(value: str, expected_prefix: Literal["info", "lbl", "rel", "ont"]) -> str:
        """校验 ID 必须匹配 `^(info|lbl|rel|ont)_[a-z0-9_]{3,60}$` 且前缀一致"""
        if not value.startswith(f"{expected_prefix}_"):
            raise ValueError(f"ID `{value}` 必须以 `{expected_prefix}_` 开头")
        if not ARTIFACT_ID_PATTERN.match(value):
            raise ValueError(
                f"ID `{value}` 违反命名铁律：仅允许全小写字母、数字与下划线，后缀长度 3~60"
            )
        return value

    @staticmethod
    def render_single_line_callout(
        callout_type: AllowedCalloutType, title: str, single_line_text: str
    ) -> str:
        """渲染首节单行 Callout，强制压缩换行符以适配向量高密嵌入与 `line:` 算子"""
        clean_line = " ".join(single_line_text.strip().splitlines())
        return f"> [!{callout_type}] {title.strip()}\n> {clean_line}"

    @staticmethod
    def render_callout(
        callout_type: AllowedCalloutType,
        title: str,
        body: Union[str, Sequence[str]],
    ) -> str:
        """渲染正文明细 Callout（仅允许使用 7 个标准标识符）"""
        lines = [f"> [!{callout_type}] {title.strip()}"]
        if isinstance(body, str):
            for raw_line in body.strip().splitlines():
                lines.append(f"> {raw_line}".rstrip())
        else:
            for item in body:
                lines.append(f"> - {item.strip()}")
        return "\n".join(lines)

    @staticmethod
    def build_graph_footer(link_rows: List[str]) -> str:
        """仅当存在有效双链行时才渲染底部分割线与链接区，全空则彻底留空"""
        valid_rows = [row.strip() for row in link_rows if row and row.strip()]
        if not valid_rows:
            return ""
        return "\n".join(["---", *valid_rows])

    def get_frontmatter_data(self) -> Dict[str, Any]:
        """自动继承底层 core 模型声明的 frontmatter 元数据，并与包装层正交元数据合并"""
        core_fm = self.core.get_frontmatter_data()
        wrapper_fm = super().get_frontmatter_data()
        return {**core_fm, **wrapper_fm}

    def _render_frontmatter(self) -> str:
        """统一生成合法 YAML Frontmatter（确保字符串与列表输出为标准双引号格式）"""
        fm_data = self.get_frontmatter_data()
        if not fm_data:
            return ""
        fm_lines = ["---"]
        for key, val in fm_data.items():
            formatted_val = json.dumps(val, ensure_ascii=False) if isinstance(val, (str, list, dict)) else val
            fm_lines.append(f"{key}: {formatted_val}")
        fm_lines.append("---")
        return "\n".join(fm_lines)
