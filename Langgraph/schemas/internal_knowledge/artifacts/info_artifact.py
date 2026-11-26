# /schemas/internal_knowledge/artifacts/info_artifact.py
from pathlib import Path
from typing import List, Optional
from pydantic import Field, model_validator

from schemas.internal_knowledge.artifacts.base import BaseArtifactView
from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.source_uri import SourceScheme


class InformationArtifact(BaseArtifactView[Information]):
    """模板 A：L1 原始符号切片物化视图（基于 SourceScheme 自适应代码与通用文本排版，零语言特化）"""

    trace_id: Optional[str] = Field(
        default=None,
        description="全链路运行追踪 ID",
        json_schema_extra={"frontmatter": True},
    )

    # 底部双链收口字段
    derived_labels: List[str] = Field(default_factory=list, description="提炼出的概念节点 ID 列表")
    architecture_ref: str = Field(
        default="Unclassified_Architecture",
        min_length=1,
        description="归属架构节点名称",
    )

    # 可选摘要插槽（缺省时由模型基于 self.core 自动推导）
    title: Optional[str] = Field(default=None, description="文档一级标题")
    one_line_summary: Optional[str] = Field(default=None, description="首节核心摘要单行文本")
    unresolved_issues: List[str] = Field(default_factory=list, description="遗留问题列表")

    @model_validator(mode="after")
    def _validate_l1_invariants(self) -> "InformationArtifact":
        self.validate_wiki_id(self.core.info_id, "info")
        for lid in self.derived_labels:
            self.validate_wiki_id(lid, "lbl")
        return self

    def _resolve_repo_fence_lang(self) -> Optional[str]:
        """纯结构化协议判断：仅当数据源为 REPO 时，直接提取文件后缀作为围栏语言标识"""
        uri = self.core.source
        if not uri or uri.scheme != SourceScheme.REPO:
            return None
        target = uri.subpath or uri.location
        suffix = Path(target).suffix.lstrip(".").lower()
        return suffix if suffix.isalnum() else ""

    def _build_default_summary(self) -> str:
        """基于 core 元数据自动生成高密单行摘要"""
        src_desc = self.core.serialize_source_uri(self.core.source) or self.core.info_id
        topic_desc = f"[{self.core.topic}] " if self.core.topic else ""
        return f"{topic_desc}来自 `{src_desc}` 的原始符号切片。"

    def _render_body(self) -> str:
        raw_text = self.core.information.strip()

        # 1. 若输入本身已是结构化三段式 Markdown 笔记，直接保持原结构
        if "## 核心摘要" in raw_text and "## 原始切片明细" in raw_text:
            body_parts = [raw_text]
        else:
            # 2. 自动套用标准 L1 三段式骨架
            uri = self.core.source
            if self.title:
                heading = self.title
            elif uri:
                name = Path(uri.subpath or uri.location).name
                heading = f"{name} ({uri.anchor})" if uri.anchor else name
            else:
                heading = self.core.topic or self.core.info_id

            summary = self.one_line_summary or self._build_default_summary()
            sec1 = "\n\n".join([
                "## 核心摘要",
                self.render_single_line_callout("abstract", "一句话摘要", summary),
            ])

            # 仅 REPO 协议源自动加动态安全代码围栏，其余源（WEB/DOC/CHAT/FILE笔记等）原样作为 Markdown 正文
            fence_lang = self._resolve_repo_fence_lang()
            if fence_lang is not None:
                fence = "```"
                while fence in raw_text:
                    fence += "`"
                detail_content = f"{fence}{fence_lang}\n{raw_text}\n{fence}"
            else:
                detail_content = raw_text

            sec2 = f"## 原始切片明细\n\n{detail_content}"
            issues = self.unresolved_issues or ["待 3.2 阶段提炼概念节点与跨切片关联"]
            sec3 = "\n".join(["## 遗留问题", *(f"- {item}" for item in issues)])
            body_parts = [f"# {heading}", sec1, sec2, sec3]

        # 3. 底部双链收口
        link_rows: List[str] = []
        if self.derived_labels:
            links = " | ".join(f"[[{lid}]]" for lid in self.derived_labels)
            link_rows.append(f"**提炼概念**：{links}")
        if self.architecture_ref:
            link_rows.append(f"**归属架构**：[[{self.architecture_ref}]]")

        footer = self.build_graph_footer(link_rows)
        if footer:
            body_parts.append(footer)
        return "\n\n".join(body_parts)
