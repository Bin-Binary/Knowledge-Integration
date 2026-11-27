# components/internal_knowledge/organization/heuristics/code_rules.py
import re
from typing import Optional
from components.internal_knowledge.schemas.information import Information

_CODE_STRUCTURE_RE = re.compile(
    r"\b(?:def|async\s+def|class|function|if|elif|case|for|while|try|except|return|export)\b"
    r"|^[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*\)\s*\{",
    re.MULTILINE,
)


def heuristic_code_and_file(info: Information) -> Optional[float]:
    """代码与配置文件双向快筛：负向拦截样板噪声，正向直通结构化业务逻辑切片"""
    raw_lines = [line.strip() for line in (info.information or "").splitlines() if line.strip()]
    lines = [line for line in raw_lines if not line.startswith("# File:")]
    if not lines:
        return 0.0

    # 1. 负向拦截：纯依赖导入块
    if all(line.startswith(("import ", "from ", "use ", "package ")) for line in lines):
        return 0.1

    joined = "\n".join(lines)
    meaningful_tokens = re.findall(r"[a-zA-Z0-9_\u4e00-\u9fa5]{2,}", joined)

    # 2. 负向拦截：极短无实质语义骨架
    if len(meaningful_tokens) < 4:
        return 0.1

    # 3. 正向快筛直通：已由结构化切片器切出的包含控制流/函数定义或领域注释的高密度切片（免 LLM 打分）
    has_code_logic = bool(_CODE_STRUCTURE_RE.search(joined))
    has_rich_docs = (
        any(line.startswith(("#", "//", "/*", '"""', "'''")) for line in lines)
        and len(meaningful_tokens) >= 15
    )

    if (has_code_logic and len(meaningful_tokens) >= 12) or has_rich_docs:
        return 0.85

    return None
