# /components/internal_knowledge/acquisition/workspace_gap_router.py
import re
import asyncio
import inspect
import logging
from pathlib import Path
from typing import Iterable, List, Optional, Set
from pydantic import Field

from schemas.base import LLMOutputSchema
from components.internal_knowledge.schemas.source_uri import SourceScheme, SourceURI
from protocols.llm import StructuredLLMProtocol
from components.internal_knowledge.protocols import GapRoutingProtocol
from infra import emit_component_status

logger = logging.getLogger(__name__)

DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", ".idea", ".vscode", "data"
}
DEFAULT_ALLOWED_EXTS: Set[str] = {
    ".md", ".txt", ".py", ".ts", ".go", ".java", ".json", ".yaml", ".yml", ".sh", ".bash", ".zsh"
}
# 匹配 Windows/POSIX 显式文件路径（如 D:/foo/bar.sh 或 ./docs/a.md）
_EXPLICIT_PATH_RE = re.compile(
    r"(?:[a-zA-Z]:[\\/]|[./\\]{1,2})?[\w\-./\\]+\.(?:md|txt|py|ts|go|java|json|yaml|yml|sh|bash|zsh)\b",
    re.IGNORECASE,
)

class _SelectedFileTarget(LLMOutputSchema):
    relative_path: str = Field(..., description="命中的文件相对路径（必须严格来自候选文件清单）")
    anchor: str | None = Field(
        default=None,
        description="可选细粒度锚点（如 Markdown 章节 'sec:架构设计' 或函数名 'func:login'，不确定则留空）",
    )


class _WorkspaceRoutingOutput(LLMOutputSchema):
    targets: List[_SelectedFileTarget] = Field(
        default_factory=list,
        description="与当前知识缺口最相关的本地目标文件列表（按相关性降序，最多 3 个）",
    )


class WorkspaceFileGapRouter(GapRoutingProtocol):
    """
    基于本地 Workspace 目录树的缺口路由算子（直接实现 GapRoutingProtocol，零基类继承）。

    核心安全与防幻觉机制：
        1. 可配置目录白名单扫描：忽略无关目录，构建真实文件目录树；
        2. 路径防穿越（Path Traversal Guard）：严格校验模型输出路径是否处于 workspace_root 内部且真实存在。
    """

    def __init__(
        self,
        llm_client: StructuredLLMProtocol,
        workspace_root: str | Path = ".",
        max_candidates: int = 120,
        max_routed_files: int = 3,
        ignore_dirs: Optional[Iterable[str]] = None,
        allowed_exts: Optional[Iterable[str]] = None,
    ) -> None:
        self._llm = llm_client
        self._workspace_root = Path(workspace_root).resolve()
        self._max_candidates = max_candidates
        self._max_routed_files = max_routed_files
        self._ignore_dirs = set(ignore_dirs) if ignore_dirs is not None else DEFAULT_IGNORE_DIRS
        self._allowed_exts = (
            {ext.lower() for ext in allowed_exts}
            if allowed_exts is not None
            else DEFAULT_ALLOWED_EXTS
        )

    async def route(self, gap_description: str, problem_context: str) -> List[SourceURI]:
        """实现 GapRoutingProtocol：前置空值拦截 -> 显式路径快筛 / LLM 推理定位 -> 规范化 URI 去重保序"""
        clean_gap = (gap_description or "").strip()
        if not clean_gap:
            return []

        clean_context = (problem_context or "").strip()
        emit_component_status(
            f"[缺口路由]：正在针对知识缺口定位目标数据源：{clean_gap[:30]}...\n"
        )

        # 1. 快筛：若文本中已明确给出本地真实存在的文件路径，0ms 直通（免除全盘扫描与 LLM 路由）
        raw_uris = self._extract_explicit_local_uris(f"{clean_gap}\n{clean_context}")
        if not raw_uris:
            raw_uris = await self._infer_target_uris(
                gap_description=clean_gap,
                problem_context=clean_context,
            )

        deduped_uris: List[SourceURI] = []
        seen: Set[str] = set()
        for uri in raw_uris:
            key = uri.model_dump_json()
            if key not in seen:
                seen.add(key)
                deduped_uris.append(uri)

        emit_component_status(
            f"[缺口路由]：已锁定 {len(deduped_uris)} 个待采集数据源。\n"
        )
        return deduped_uris


    async def _infer_target_uris(
        self, gap_description: str, problem_context: str
    ) -> List[SourceURI]:
        candidate_files = await asyncio.to_thread(self._scan_workspace_files)
        if not candidate_files:
            logger.warning(
                "[WorkspaceGapRouter] 工作区目录 '%s' 下未扫描到任何符合白名单的候选文件！",
                self._workspace_root,
            )
            return []

        logger.info(
            "[WorkspaceGapRouter] 在 '%s' 下扫描到 %d 个候选文件，开始请求 LLM 路由...",
            self._workspace_root,
            len(candidate_files),
        )
        file_tree_str = "\n".join(f"- {rel_path}" for rel_path in candidate_files)

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个本地代码与文档库检索路由专家。请根据【知识缺口描述】与【原始问题】，"
                    f"从下方【Workspace 真实文件清单】中挑选最可能包含答案的文件（最多 {self._max_routed_files} 个）。\n"
                    "铁律：relative_path 必须一字不差地来自给定清单，严禁捏造不存在的路径。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"### 原始问题：\n{problem_context}\n\n"
                    f"### 知识缺口描述：\n{gap_description}\n\n"
                    f"### Workspace 真实文件清单：\n{file_tree_str}"
                ),
            },
        ]

        raw_call = self._llm.generate_structured(
            messages=messages,
            response_schema=_WorkspaceRoutingOutput,
        )
        result: _WorkspaceRoutingOutput = await raw_call if inspect.isawaitable(raw_call) else raw_call

        routed_uris: List[SourceURI] = []
        valid_set = set(candidate_files)

        for target in result.targets[: self._max_routed_files]:
            clean_rel = target.relative_path.strip().lstrip("./")
            if clean_rel not in valid_set:
                logger.debug("[WorkspaceGapRouter] 过滤模型幻觉路径: %s", clean_rel)
                continue

            abs_target = (self._workspace_root / clean_rel).resolve()
            if not abs_target.is_relative_to(self._workspace_root) or not abs_target.is_file():
                continue

            routed_uris.append(
                SourceURI(
                    scheme=SourceScheme.FILE,
                    location=abs_target.as_posix(),
                    anchor=target.anchor.strip() if target.anchor else None,
                )
            )

        return routed_uris

    def _scan_workspace_files(self) -> List[str]:
        """扫描 workspace 目录，返回按字母序排列的相对 POSIX 路径列表"""
        if not self._workspace_root.exists():
            return []

        results: List[str] = []
        for path in self._workspace_root.rglob("*"):
            if any(part in self._ignore_dirs for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in self._allowed_exts:
                rel_posix = path.relative_to(self._workspace_root).as_posix()
                results.append(rel_posix)
                if len(results) >= self._max_candidates:
                    break

        results.sort()
        return results

    def _extract_explicit_local_uris(self, text: str) -> List[SourceURI]:
        """快筛：若文本中已明确给出本地真实存在的文件路径，直接构造 SourceURI，免除全盘扫描与 LLM 路由"""
        found: List[SourceURI] = []
        for match in _EXPLICIT_PATH_RE.findall(text):
            raw_p = Path(match.strip())
            candidates = [raw_p] if raw_p.is_absolute() else [self._workspace_root / raw_p, raw_p]
            for cand in candidates:
                try:
                    resolved = cand.resolve()
                except OSError:
                    continue
                if resolved.is_file() and (not self._strict_workspace_jail or resolved.is_relative_to(self._workspace_root)):
                    found.append(SourceURI(scheme=SourceScheme.FILE, location=resolved.as_posix()))
                    break
        return found
