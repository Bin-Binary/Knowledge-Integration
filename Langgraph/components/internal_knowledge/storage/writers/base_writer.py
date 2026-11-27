# /components/internal_knowledge/storage/writers/base_writer.py
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Callable, Dict, Generic, List, Optional, Sequence, TypeVar

from components.internal_knowledge.schemas.wiki_governance import WikiArtifactLayer, WikiMaturityStage

logger = logging.getLogger(__name__)

ItemT = TypeVar("ItemT")


@dataclass(frozen=True)
class GraphBatchContext:
    """单批次跨层图谱反向索引上下文（供各层 Writer 按需读取关联双链）"""

    trace_id: str
    info_to_labels: Dict[str, List[str]] = field(default_factory=dict)
    label_to_infos: Dict[str, List[str]] = field(default_factory=dict)
    label_to_out_rels: Dict[str, List[str]] = field(default_factory=dict)
    label_to_onts: Dict[str, List[str]] = field(default_factory=dict)
    rel_to_onts: Dict[str, List[str]] = field(default_factory=dict)
    info_summaries: Dict[str, str] = field(default_factory=dict)


class BaseMarkdownArtifactWriter(ABC, Generic[ItemT]):
    """四层知识产物落盘基类（模板方法 + 钩子模式）

    公共能力（基类统一收口）：
        1. 跨生命周期目录存在性检查（gold -> release -> debug）。
        2. 只读高水位拦截：目标已位于 release/ 或 gold/ 时严禁覆写，自动写入 .patch_queue.jsonl。
        3. 底部双链锚点区正则提取与集合并集幂等合并。
    """

    LAYER: WikiArtifactLayer  # 子类必须声明所属抽象层

    def __init__(
        self,
        vault_root: Path,
        on_file_written: Optional[Callable[[Path], None]] = None,
    ):
        self.vault_root = vault_root
        self._on_file_written = on_file_written

    @staticmethod
    def _validate_artifact_id(artifact_id: str) -> str:
        """校验 artifact_id 合法性，严防路径穿越"""
        clean_id = artifact_id.strip()
        if (
            not clean_id
            or "/" in clean_id
            or "\\" in clean_id
            or ".." in clean_id
            or PurePosixPath(clean_id).name != clean_id
        ):
            raise ValueError(f"非法的 artifact_id（禁止为空或包含路径穿越字符）: {artifact_id!r}")
        return clean_id

    # ------------------------------------------------------------------
    # 模板方法（Template Method）：固定落盘治理主流程
    # ------------------------------------------------------------------
    def write_batch(
        self, items: Sequence[ItemT], ctx: Optional[GraphBatchContext] = None
    ) -> List[str]:
        """批量落盘当前层产物，返回成功写入/更新的 debug/ 相对路径列表"""
        if not items:
            return []

        start_ts = time.perf_counter()
        batch_ctx = ctx or GraphBatchContext(trace_id="standalone")
        prepared_items = self._prepare_items(items)
        saved_relpaths: List[str] = []
        created_count = 0
        updated_count = 0
        queued_count = 0

        for item in prepared_items:
            artifact_id = self._validate_artifact_id(self._get_artifact_id(item))
            link_updates = self._extract_link_updates(item, batch_ctx)
            existing_stage = self._find_existing_stage(artifact_id)

            # 1. 只读高水位拦截（release / gold 严禁覆写，进待审队列）
            if existing_stage in (WikiMaturityStage.RELEASE, WikiMaturityStage.GOLD):
                if any(link_updates.values()):
                    self._enqueue_patch_for_review(
                        target_stage=existing_stage,
                        artifact_id=artifact_id,
                        new_links=link_updates,
                        trace_id=batch_ctx.trace_id,
                    )
                    queued_count += 1
                continue

            relpath = str(PurePosixPath(WikiMaturityStage.DEBUG.value) / self.LAYER.value / f"{artifact_id}.md")
            abs_path = self.vault_root / relpath
            abs_path.parent.mkdir(parents=True, exist_ok=True)

            # 2. debug/ 已存在时的更新策略（委托子类钩子决定保留正文还是刷新正文）
            if abs_path.exists():
                existing_md = abs_path.read_text(encoding="utf-8")
                final_md = self._on_debug_file_exists(item, existing_md, link_updates, batch_ctx)
                updated_count += 1
            else:
                final_md = self._render_new_markdown(item, batch_ctx)
                created_count += 1

            abs_path.write_text(final_md, encoding="utf-8")
            if self._on_file_written is not None:
                self._on_file_written(abs_path)
            saved_relpaths.append(relpath)

        logger.debug(
            "[Writer:%s] 批量落盘完成 (trace_id=%s): 耗时=%.3fs, 新增=%d, 合并更新=%d, 高水位入队=%d",
            self.LAYER.value,
            batch_ctx.trace_id,
            time.perf_counter() - start_ts,
            created_count,
            updated_count,
            queued_count,
        )
        return saved_relpaths

    # ------------------------------------------------------------------
    # 子类钩子（Hooks）：由 L1 / L2 / L3 / L4 各自实现差异化细节
    # ------------------------------------------------------------------
    def _prepare_items(self, items: Sequence[ItemT]) -> List[ItemT]:
        """钩子 1（可选）：入库前预处理（如 L2 按 label_id 去重合并多切片语义）"""
        return list(items)

    @abstractmethod
    def _get_artifact_id(self, item: ItemT) -> str:
        """钩子 2（必填）：提取当前实体的全局唯一主键 ID"""
        ...

    @abstractmethod
    def _extract_link_updates(self, item: ItemT, ctx: GraphBatchContext) -> Dict[str, List[str]]:
        """钩子 3（必填）：提取本轮需要追加/合并的底部双链分组（如 {'发出关系': ['rel_xxx']}）"""
        ...

    @abstractmethod
    def _render_new_markdown(self, item: ItemT, ctx: GraphBatchContext) -> str:
        """钩子 4（必填）：首次落盘时包装为对应 Artifact 视图并渲染完整 Markdown"""
        ...

    def _on_debug_file_exists(
        self,
        item: ItemT,
        existing_md: str,
        link_updates: Dict[str, List[str]],
        ctx: GraphBatchContext,
    ) -> str:
        """钩子 5（默认只读正文）：默认严格保留已有正文，仅对底部双链做幂等集合合并"""
        return self.merge_bottom_links(existing_md, link_updates)

    # ------------------------------------------------------------------
    # 基类通用底层治理工具
    # ------------------------------------------------------------------
    def _find_existing_stage(self, artifact_id: str) -> Optional[WikiMaturityStage]:
        for stage in (WikiMaturityStage.GOLD, WikiMaturityStage.RELEASE, WikiMaturityStage.DEBUG):
            target = self.vault_root / stage.value / self.LAYER.value / f"{artifact_id}.md"
            if target.exists():
                return stage
        return None

    def _enqueue_patch_for_review(
        self,
        target_stage: WikiMaturityStage,
        artifact_id: str,
        new_links: Dict[str, List[str]],
        trace_id: str,
    ) -> None:
        queue_file = self.vault_root / ".patch_queue.jsonl"
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "target_stage": target_stage.value,
            "layer": self.LAYER.value,
            "artifact_id": artifact_id,
            "append_links": {k: v for k, v in new_links.items() if v},
        }
        with queue_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info(
            "[Writer:%s] 目标处于高水位只读区 (%s)，双链变更已写入待审队列: %s",
            self.LAYER.value,
            target_stage.value,
            artifact_id,
        )

    @staticmethod
    def extract_bottom_links(md_text: str) -> Dict[str, List[str]]:
        """从已有 Markdown 文本底部解析双链分组"""
        footer_pattern = re.compile(r"\n---\n((?:\*\*[^*]+\*\*：.+\n?)+)\s*$")
        match = footer_pattern.search(md_text)
        groups: Dict[str, List[str]] = defaultdict(list)
        if not match:
            return groups

        for line in match.group(1).strip().splitlines():
            m_line = re.match(r"^\*\*([^*]+)\*\*：(.+)$", line.strip())
            if m_line:
                key = m_line.group(1).strip()
                for item in re.findall(r"\[\[([^\]]+)\]\]", m_line.group(2)):
                    if item not in groups[key]:
                        groups[key].append(item)
        return groups

    @classmethod
    def merge_bottom_links(cls, existing_md: str, new_link_groups: Dict[str, List[str]]) -> str:
        """只读正文原则：保留 # 标题至 --- 之间的正文，仅对底部双链做集合并集重绘"""
        footer_pattern = re.compile(r"\n---\n((?:\*\*[^*]+\*\*：.+\n?)+)\s*$")
        match = footer_pattern.search(existing_md)
        body_part = existing_md[: match.start()].rstrip() if match else existing_md.rstrip()

        merged = cls.extract_bottom_links(existing_md)
        for key, items in new_link_groups.items():
            for item in items:
                if item and item not in merged[key]:
                    merged[key].append(item)

        if not merged:
            return f"{body_part}\n"

        footer_lines = ["---"]
        for key, items in merged.items():
            if key in ("归属架构", "支撑总纲"):
                ref_val = next((x for x in reversed(items) if x != "Unclassified_Architecture"), items[-1])
                footer_lines.append(f"**{key}**：[[{ref_val}]]")
            else:
                links_str = " | ".join(f"[[{x}]]" for x in items)
                footer_lines.append(f"**{key}**：{links_str}")

        return f"{body_part}\n\n" + "\n".join(footer_lines) + "\n"
