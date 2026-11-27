# /components/internal_knowledge/acquisition/handlers/generic_text_handler.py
import asyncio
from pathlib import Path
from typing import List, Tuple

from components.internal_knowledge.schemas.source_uri import SourceScheme, SourceURI
from components.internal_knowledge.schemas.information import Information
from components.internal_knowledge.schemas.pipeline_envelope import PipelineEnvelope
from components.internal_knowledge.acquisition.registry import AcquisitionPluginRegistry
from components.internal_knowledge.utils import (
    generate_info_id,
    resolve_local_uri_path,
)


@AcquisitionPluginRegistry.register(
    "generic_text_file",
    routes=[
        (SourceScheme.FILE, "*"),
        (SourceScheme.REPO, "*"),
    ],
)
class GenericTextFileHandler:
    """通用文本与代码文件采集处理器（实现 SourceHandlerProtocol，零继承）：
    作为 FILE / REPO 协议下的通配符 '*' 兜底处理器，支持 .md、.py、.txt、.json、.yaml 等文件。
    """

    def __init__(
        self,
        workspace_root: str | Path = ".",
        min_chunk_chars: int = 80,
        max_chars: int = 3500,
        overlap_chars: int = 350,
    ) -> None:
        self._workspace_root = Path(workspace_root).resolve()
        self._min_chunk_chars = min_chunk_chars
        self._max_chars = max_chars
        self._overlap_chars = overlap_chars

    async def fetch_and_slice(
        self, uri: SourceURI, envelope: PipelineEnvelope
    ) -> List[Information]:
        """实现 SourceHandlerProtocol：异步读取通用文本/代码文件并按完整行边界滑动切片"""
        _ = envelope
        file_path = resolve_local_uri_path(uri, workspace_root=self._workspace_root)
        if not file_path.exists():
            raise FileNotFoundError(f"目标文件不存在: {file_path}")

        try:
            content = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
        except UnicodeDecodeError:
            return []

        if not (len(content.strip()) >= self._min_chunk_chars):
            return []

        rel_path = uri.subpath or file_path.name
        line_chunks = self._slice_by_lines_with_overlap(content)

        results: List[Information] = []
        for idx, (start_line, end_line, chunk_text) in enumerate(line_chunks):
            if not (len(chunk_text.strip()) >= self._min_chunk_chars):
                continue

            line_anchor = f"L{start_line}-L{end_line}"
            source_uri = self._build_slice_source_uri(uri, line_anchor)
            slice_id = f"chunk:{idx}"
            info_id = generate_info_id(source_uri, slice_identity=slice_id)

            header = f"# File: {rel_path} ({line_anchor})\n\n"
            results.append(
                Information(
                    info_id=info_id,
                    information=header + chunk_text,
                    cognizer_id=self.__class__.__name__,
                    topic=file_path.suffix.lstrip(".").lower() or "document",
                    source=source_uri,
                )
            )

        return results

    def _slice_by_lines_with_overlap(
        self, content: str
    ) -> List[Tuple[int, int, str]]:
        """按完整行边界执行带重叠的滑动窗口切片，返回 [(start_line, end_line, text), ...]"""
        lines = content.splitlines()
        if not lines:
            return []

        chunks: List[Tuple[int, int, str]] = []
        total_lines = len(lines)
        start_idx = 0

        while total_lines > start_idx:
            current_chars = 0
            end_idx = start_idx

            while total_lines > end_idx:
                line_len = len(lines[end_idx]) + 1
                if end_idx > start_idx and current_chars + line_len > self._max_chars:
                    break
                current_chars += line_len
                end_idx += 1

            chunk_text = "\n".join(lines[start_idx:end_idx])
            chunks.append((start_idx + 1, end_idx, chunk_text))

            if end_idx >= total_lines:
                break

            overlap_accum = 0
            next_start = end_idx
            while next_start > start_idx + 1 and self._overlap_chars > overlap_accum:
                next_start -= 1
                overlap_accum += len(lines[next_start]) + 1

            start_idx = next_start

        return chunks

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
