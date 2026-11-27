# /components/internal_knowledge/utils.py
"""域内知识库通用无状态工具集（纯确定性函数，零 I/O、零类状态、零继承耦合）。"""

import hashlib
from pathlib import Path
from typing import List, Optional, Tuple

from components.internal_knowledge.schemas.source_uri import SourceScheme, SourceURI
from infra.exceptions import KnowledgePipelineError


def generate_info_id(
    uri: SourceURI,
    slice_identity: Optional[str] = None,
    fallback_content: str = "",
) -> str:
    """基于【稳定逻辑位置 + 切片局部身份指纹】生成确定性且全局唯一的 info_id（格式：info_<16位hex>）。"""
    if uri.scheme == SourceScheme.REPO:
        stable_base = f"repo:{uri.location}#{uri.subpath or ''}"
    else:
        stable_base = f"{uri.scheme.value}:{uri.location}"

    if uri.anchor and not uri.anchor.startswith("L"):
        stable_base = f"{stable_base}#{uri.anchor}"

    if slice_identity:
        stable_base = f"{stable_base}@{slice_identity.strip()}"
    elif fallback_content:
        stable_base = f"{stable_base}@fallback:{fallback_content[:128]}"

    digest = hashlib.sha256(stable_base.encode("utf-8")).hexdigest()[:16]
    return f"info_{digest}"


def parse_line_range(anchor: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """通用行号锚点解析器：将 'L42-L68'、'L42-68' 或 'L42' 解析为 (start_line, end_line)。"""
    if not anchor or not anchor.startswith("L"):
        return None, None
    range_part = anchor.split(":", 1)[0][1:]
    parts = range_part.split("-", 1)
    try:
        start = int(parts[0])
        end = int(parts[1].lstrip("L")) if len(parts) > 1 else start
        return start, end
    except ValueError:
        return None, None


def apply_window_bounds(
    text: str,
    max_chars: int = 4000,
    overlap_chars: int = 400,
) -> List[str]:
    """重叠滑动窗口文本切片器：防止单条切片过长超出提取/评估模型上下文上限。"""
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    step = max(1, max_chars - overlap_chars)
    for start in range(0, len(text), step):
        chunks.append(text[start : start + max_chars])
        if start + max_chars >= len(text):
            break
    return chunks


def resolve_local_uri_path(
    uri: SourceURI,
    workspace_root: str | Path = ".",
    enforce_workspace_jail: bool = True,
) -> Path:
    """将 FILE 或 REPO 类型的 SourceURI 安全解析为本地文件系统绝对路径，并防目录穿越越界。"""
    root = Path(workspace_root).resolve()

    if uri.scheme == SourceScheme.FILE:
        loc = uri.location
        if loc.startswith("///"):
            loc = loc[2:]
        candidate = Path(loc)
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    elif uri.scheme == SourceScheme.REPO and uri.subpath:
        resolved = (root / uri.subpath).resolve()
    else:
        resolved = root

    if enforce_workspace_jail and not resolved.is_relative_to(root):
        raise KnowledgePipelineError(
            message=f"安全拦截：禁止访问工作区 ({root}) 之外的路径 ({resolved})",
            stage="acquisition",
            user_friendly_hint="目标文件路径超出允许的工作区范围，已被安全策略拦截。",
            metadata={"uri": str(uri), "resolved_path": str(resolved)},
        )

    return resolved
