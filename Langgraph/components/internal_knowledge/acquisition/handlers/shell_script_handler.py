# /components/internal_knowledge/acquisition/handlers/shell_script_handler.py
import asyncio
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from components.internal_knowledge.schemas.source_uri import SourceScheme, SourceURI
from components.internal_knowledge.schemas.information import Information
from components.internal_knowledge.schemas.pipeline_envelope import PipelineEnvelope
from components.internal_knowledge.acquisition.registry import AcquisitionPluginRegistry
from components.internal_knowledge.utils import (
    apply_window_bounds,
    generate_info_id,
    resolve_local_uri_path,
)


@AcquisitionPluginRegistry.register(
    "shell_script",
    routes=[
        (SourceScheme.FILE, ".sh"),
        (SourceScheme.FILE, ".bash"),
        (SourceScheme.FILE, ".zsh"),
        (SourceScheme.REPO, ".sh"),
        (SourceScheme.REPO, ".bash"),
        (SourceScheme.REPO, ".zsh"),
    ],
)
class ShellScriptHandler:
    """Shell 脚本专用采集处理器（实现 SourceHandlerProtocol，零继承）：
    按全局头声明 + 函数体 + 控制流代码块进行语法感知切片，并产出带行号锚点的 Information。
    """

    _SHELL_KEYWORDS = frozenset({
        "do", "done", "if", "then", "else", "elif", "fi", "for", "while",
        "until", "case", "esac", "in", "select", "time", "coproc",
    })

    _FUNC_START_RE = re.compile(
        r"^\s*(?:function\s+)?([a-zA-Z_][a-zA-Z0-9_-]*)\s*(?:\(\s*\))?\s*\{?\s*$"
    )
    _GLOBAL_DECL_RE = re.compile(
        r"^\s*(?:source\s+|\.\s+|export\s+)?[a-zA-Z_][a-zA-Z0-9_]*="
    )
    _CONTROL_FLOW_RE = re.compile(
        r"^\s*(?:while|for|until|if|elif|else|case|select)\b"
    )
    _FLOW_CLOSE_MAP = {
        "if": "fi", "elif": "fi", "else": "fi",
        "for": "done", "while": "done", "until": "done", "select": "done",
        "case": "esac",
    }

    def __init__(
        self,
        workspace_root: str | Path = ".",
        min_chunk_chars: int = 100,
        max_chars: int = 4000,
        overlap_chars: int = 400,
    ) -> None:
        self._workspace_root = Path(workspace_root).resolve()
        self._min_chunk_chars = min_chunk_chars
        self._max_chars = max_chars
        self._overlap_chars = overlap_chars

    @classmethod
    def _is_func_decl(cls, line: str, next_line: Optional[str]) -> bool:
        m = cls._FUNC_START_RE.match(line)
        if not m:
            return False
        name = m.group(1)
        if name in cls._SHELL_KEYWORDS:
            return False
        if "{" in line:
            return True
        if next_line and next_line.strip().startswith("{"):
            return True
        return False

    async def fetch_and_slice(
        self, uri: SourceURI, envelope: PipelineEnvelope
    ) -> List[Information]:
        """实现 SourceHandlerProtocol：异步读取本地 Shell 文件并执行语法块切片"""
        _ = envelope
        file_path = resolve_local_uri_path(uri, workspace_root=self._workspace_root)
        if not file_path.exists():
            raise FileNotFoundError(f"Shell 脚本路径不存在: {file_path}")

        try:
            source_code = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
        except UnicodeDecodeError:
            return []

        rel_path = uri.subpath or file_path.name
        raw_chunks = self._extract_raw_chunks(source_code, rel_path)

        results: List[Information] = []
        name_counter: Dict[str, int] = {}

        for anchor, start_line, end_line, text in raw_chunks:
            if len(text) < self._min_chunk_chars:
                continue

            name_counter[anchor] = name_counter.get(anchor, 0) + 1
            anchor_seq = name_counter[anchor]

            windows = apply_window_bounds(
                text,
                max_chars=self._max_chars,
                overlap_chars=self._overlap_chars,
            )
            for idx, window_text in enumerate(windows):
                line_anchor = (
                    f"L{start_line}-L{end_line}"
                    if idx == 0
                    else f"L{start_line}-L{end_line}:part{idx}"
                )
                source_uri = self._build_slice_source_uri(uri, line_anchor)

                parts = [anchor, str(anchor_seq)]
                if idx > 0:
                    parts.append(f"part{idx}")
                slice_id = ":".join(parts)

                info_id = generate_info_id(source_uri, slice_identity=slice_id)
                results.append(
                    Information(
                        info_id=info_id,
                        information=window_text,
                        cognizer_id=self.__class__.__name__,
                        topic="shell_script",
                        source=source_uri,
                    )
                )

        return results

    @staticmethod
    def _build_slice_source_uri(base_uri: SourceURI, anchor: str) -> SourceURI:
        if base_uri.scheme == SourceScheme.REPO:
            return SourceURI(
                scheme=base_uri.scheme,
                location=base_uri.location,
                revision=base_uri.revision,
                subpath=base_uri.subpath,
                anchor=anchor,
            )
        return SourceURI(
            scheme=base_uri.scheme,
            location=base_uri.location,
            anchor=anchor,
        )

    def _extract_raw_chunks(
        self, source_code: str, rel_path: str
    ) -> List[Tuple[str, int, int, str]]:
        lines = source_code.splitlines()
        global_headers: List[str] = []
        func_blocks: List[Tuple[str, int, int, str]] = []
        block_spans: List[Tuple[str, int, int, str]] = []
        orphan_spans: List[Tuple[int, str]] = []
        header_done = False

        i, n = 0, len(lines)
        while i < n:
            line = lines[i]
            stripped = line.strip()

            if not header_done:
                if (
                    stripped.startswith("#")
                    or stripped.startswith("set -")
                    or self._GLOBAL_DECL_RE.match(line)
                ):
                    global_headers.append(line)
                    i += 1
                    continue
                header_done = True

            next_line = lines[i + 1].strip() if i + 1 < n else None
            if self._is_func_decl(line, next_line):
                match = self._FUNC_START_RE.match(line)
                func_name = match.group(1) if match else "anonymous_func"
                comment_start = self._find_comment_start(lines, i)
                _, next_idx = self._extract_brace_block(lines, i)
                start_line = comment_start + 1
                end_line = next_idx
                block_text = "\n".join(lines[comment_start:next_idx])
                func_blocks.append((func_name, start_line, end_line, block_text))
                i = next_idx
                continue

            if self._CONTROL_FLOW_RE.match(line):
                block_body, next_idx = self._extract_control_block(lines, i)
                block_type = self._CONTROL_FLOW_RE.match(line).group(0).strip().split()[0]  # type: ignore[union-attr]
                block_label = f"block:{block_type}"
                start_line = i + 1
                end_line = next_idx
                block_text = "\n".join(block_body)
                block_spans.append((block_label, start_line, end_line, block_text))
                i = next_idx
                continue

            if stripped:
                orphan_spans.append((i, line))
            i += 1

        header_str = (f"# File: {rel_path}\n" + "\n".join(global_headers)).strip()

        chunks: List[Tuple[str, int, int, str]] = [
            (func_name, s, e, f"{header_str}\n\n{func_code}")
            for func_name, s, e, func_code in func_blocks
        ]

        for block_label, s, e, block_code in block_spans:
            chunks.append((block_label, s, e, f"{header_str}\n\n{block_code}"))

        if orphan_spans:
            main_start = orphan_spans[0][0] + 1
            main_end = orphan_spans[-1][0] + 1
            main_code = "\n".join(line for _, line in orphan_spans)
            chunks.append(
                (
                    "orphan",
                    main_start,
                    main_end,
                    f"{header_str}\n\n# --- Orphan Statements ---\n{main_code}",
                )
            )

        return chunks

    @staticmethod
    def _find_comment_start(lines: List[str], func_start_idx: int) -> int:
        idx = func_start_idx - 1
        while idx >= 0 and lines[idx].strip().startswith("#"):
            idx -= 1
        return idx + 1

    @staticmethod
    def _extract_brace_block(
        lines: List[str], start_idx: int
    ) -> Tuple[List[str], int]:
        block: List[str] = []
        brace_depth, opened, idx = 0, False, start_idx
        while idx < len(lines):
            line = lines[idx]
            block.append(line)
            code_part = line.split("#", 1)[0]
            open_c, close_c = code_part.count("{"), code_part.count("}")
            if open_c > 0:
                opened = True
            brace_depth += open_c - close_c
            idx += 1
            if opened and brace_depth <= 0:
                break
        return block, idx

    _OPEN_KEYWORDS = frozenset({"if", "for", "while", "until", "select", "case"})

    def _extract_control_block(
        self, lines: List[str], start_idx: int
    ) -> Tuple[List[str], int]:
        block: List[str] = []
        first_word = lines[start_idx].strip().split()[0]
        close_kw = self._FLOW_CLOSE_MAP.get(first_word)
        if not close_kw:
            return [lines[start_idx]], start_idx + 1

        depth = 0
        idx = start_idx
        while idx < len(lines):
            line = lines[idx]
            stripped = line.strip()
            block.append(line)

            if stripped and not stripped.startswith("#"):
                code_part = stripped.split("#", 1)[0].strip()
                tokens = re.split(r"[\s;]+", code_part)
                first_tok = tokens[0] if tokens else ""
                last_tok = tokens[-1] if tokens else ""

                if idx == start_idx:
                    depth = 1
                elif first_tok in self._OPEN_KEYWORDS and self._FLOW_CLOSE_MAP.get(first_tok) == close_kw:
                    depth += 1

                # 兼容单行写法 (如 if ...; then ...; fi) 及常规独立结束行
                if (idx > start_idx and first_tok == close_kw) or (last_tok == close_kw):
                    depth -= 1

            idx += 1
            if depth <= 0:
                break

        return block, idx
