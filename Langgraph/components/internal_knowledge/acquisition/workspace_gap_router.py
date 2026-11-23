# /components/internal_knowledge/acquisition/workspace_gap_router.py
import asyncio
import inspect
from pathlib import Path
from typing import List, Set
from pydantic import Field

from schemas import LLMOutputSchema
from schemas.internal_knowledge import SourceScheme, SourceURI
from protocols import StructuredLLMProtocol
from components.internal_knowledge.acquisition.base_gap_router import BaseGapRouter


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


class WorkspaceFileGapRouter(BaseGapRouter):
    """基于本地 Workspace 目录树的缺口路由算子（产出 SourceScheme.FILE 定位符）。

    核心安全与防幻觉机制：
        1. 目录白名单扫描：自动忽略 .git / __pycache__ / 知识库输出目录本身，构建真实文件目录树。
        2. 路径防穿越（Path Traversal Guard）：严格校验模型输出路径是否处于 workspace_root 内部且真实存在。
    """

    DEFAULT_IGNORE_DIRS: Set[str] = {
        ".git", ".venv", "venv", "__pycache__", "node_modules", ".idea", ".vscode", "data"
    }
    DEFAULT_ALLOWED_EXTS: Set[str] = {".md", ".txt", ".py", ".ts", ".go", ".java", ".json", ".yaml", ".yml"}

    def __init__(
        self,
        llm_client: StructuredLLMProtocol,
        workspace_root: str | Path = ".",
        max_candidates: int = 120,
        max_routed_files: int = 3,
    ):
        self.llm = llm_client
        self.workspace_root = Path(workspace_root).resolve()
        self.max_candidates = max_candidates
        self.max_routed_files = max_routed_files

    async def _infer_target_uris(
        self, gap_description: str, problem_context: str
    ) -> List[SourceURI]:
        # 1. 异步扫描 workspace 真实存在的文件清单
        candidate_files = await asyncio.to_thread(self._scan_workspace_files)
        if not candidate_files:
            return []

        file_tree_str = "\n".join(f"- {rel_path}" for rel_path in candidate_files)

        # 2. 让结构化大模型基于真实目录树路由最相关的文件
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个本地代码与文档库检索路由专家。请根据【知识缺口描述】与【原始问题】，"
                    f"从下方【Workspace 真实文件清单】中挑选最可能包含答案的文件（最多 {self.max_routed_files} 个）。\n"
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

        raw_call = self.llm.generate_structured(
            messages=messages,
            response_schema=_WorkspaceRoutingOutput,
        )
        result: _WorkspaceRoutingOutput = await raw_call if inspect.isawaitable(raw_call) else raw_call

        # 3. 路径防穿越与存在性二次校验，构造强类型 SourceURI
        routed_uris: List[SourceURI] = []
        valid_set = set(candidate_files)

        for target in result.targets[: self.max_routed_files]:
            clean_rel = target.relative_path.strip().lstrip("./")
            if clean_rel not in valid_set:
                continue

            # 物理边界校验，防止 ../ 越权访问系统敏感文件
            abs_target = (self.workspace_root / clean_rel).resolve()
            if not abs_target.is_relative_to(self.workspace_root) or not abs_target.is_file():
                continue

            routed_uris.append(
                SourceURI(
                    scheme=SourceScheme.FILE,
                    location=f"./{clean_rel}",
                    anchor=target.anchor.strip() if target.anchor else None,
                )
            )

        return routed_uris

    def _scan_workspace_files(self) -> List[str]:
        """扫描 workspace 目录，返回按字母序排列的相对 POSIX 路径列表"""
        if not self.workspace_root.exists():
            return []

        results: List[str] = []
        for path in self.workspace_root.rglob("*"):
            if any(part in self.DEFAULT_IGNORE_DIRS for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in self.DEFAULT_ALLOWED_EXTS:
                rel_posix = path.relative_to(self.workspace_root).as_posix()
                results.append(rel_posix)
                if len(results) >= self.max_candidates:
                    break

        results.sort()
        return results
