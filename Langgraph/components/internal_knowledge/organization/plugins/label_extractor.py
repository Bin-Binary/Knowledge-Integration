# /components/internal_knowledge/organization/plugins/label_extractor.py
import asyncio
import inspect
import logging
import re
import time
from typing import Dict, List, Optional, Set
from pydantic import Field, create_model

from schemas.base import LLMOutputSchema
from components.internal_knowledge.schemas.artifacts import LabelMetaType, build_compliant_artifact_id
from components.internal_knowledge.schemas.information import Information
from components.internal_knowledge.schemas.labeling import Labeling, NodeCategory
from protocols.llm import StructuredLLMProtocol
from components.internal_knowledge.protocols import LabelExtractorProtocol
from components.internal_knowledge.organization.registry import OrganizationPluginRegistry, OrgStage

logger = logging.getLogger(__name__)

# 默认单切片概念基数上限（10切片最多 <= 30个，去重后约 12~18 个高内聚概念）
MAX_CONCEPTS_PER_INFO = 3

# 常见英文词尾复数排除白名单（避免 status -> statu、redis -> redi 等误伤）
_SINGULAR_EXCEPTIONS: Set[str] = frozenset({
    "status", "redis", "prometheus", "kubernetes", "k8s", "postgres",
    "process", "access", "address", "ingress", "egress", "bus", "os", "tls", "https", "dns",
})

_META_TYPE_TO_CATEGORY: Dict[LabelMetaType, NodeCategory] = {
    "component": NodeCategory.ENTITY,
    "mechanism": NodeCategory.CONCEPT,
    "principle": NodeCategory.RULE,
    "metric": NodeCategory.RULE,
    "failure_mode": NodeCategory.EVENT,
    "workflow": NodeCategory.EVENT,
}

_META_TYPE_CN_PREFIX: Dict[LabelMetaType, str] = {
    "mechanism": "机制",
    "component": "组件",
    "principle": "原则",
    "failure_mode": "故障模式",
    "metric": "指标",
    "workflow": "流程",
}


class _ExtractedConceptItem(LLMOutputSchema):
    """单个候选核心概念的结构化抽取结果"""

    label_type: LabelMetaType = Field(
        ...,
        description="受控元类型（必须严格从 mechanism / component / principle / failure_mode / metric / workflow 中 6 选 1）",
    )
    semantic_slug: str = Field(
        ...,
        description="全小写英文蛇形短标识（2~3个词，单数形式，如 artifact_repository / branch_fallback，严禁带 lbl_ 前缀）",
    )
    canonical_name: str = Field(
        ...,
        description="规范化概念名称（如 制品包仓 / 分支回退拉取机制）",
    )
    core_definition: str = Field(
        ...,
        description="结合当前业务上下文的一句话核心定义或判据（严禁空话，必须说明它是什么以及起什么作用）",
    )
    trigger_criteria: List[str] = Field(
        default_factory=list,
        max_length=2,
        description="1~2条具体的触发条件、适用时机或观测判据（结合业务参数或状态）",
    )
    boundaries_and_counterexamples: List[str] = Field(
        default_factory=list,
        max_length=2,
        description="1~2条适用边界、前置依赖或反例约束",
    )


@OrganizationPluginRegistry.register(OrgStage.EXTRACT, name="llm_label", is_default=True)
class LLMLabelExtractor(LabelExtractorProtocol):
    """3.2 基于结构化大模型的概念节点提取器（防概念分裂 + 真实业务语义抽取）"""

    def __init__(
        self,
        llm_client: StructuredLLMProtocol,
        max_concepts: int = MAX_CONCEPTS_PER_INFO,
        max_input_chars: int = 3500,
        timeout_seconds: Optional[float] = None,
    ):
        if max_concepts < 1:
            raise ValueError("max_concepts 必须 >= 1")
        self.llm = llm_client
        self.max_concepts = max_concepts
        self.max_input_chars = max_input_chars
        self.timeout_seconds = timeout_seconds

        # 动态生成唯一 Schema 类名，使自定义 max_concepts 真正生效且不冲突
        # 在 LLMLabelExtractor.__init__ 中修改动态 Schema 定义：
        schema_name = f"_LabelBatchOutput_Max{self.max_concepts}"
        self._output_schema = create_model(
            schema_name,
            __base__=LLMOutputSchema,
            slice_summary=(
                str,
                Field(
                    default="",
                    description="用一句话（30~60字）精准概括当前片段的核心业务逻辑、关键参数规则或函数职责（严禁废话或模板语）",
                ),
            ),
            concepts=(
                List[_ExtractedConceptItem],
                Field(
                    default_factory=list,
                    max_length=self.max_concepts,
                    description=f"提炼出的最高价值核心业务概念节点（严格最多 {self.max_concepts} 个，宁缺毋滥）",
                ),
            ),
        )


    @staticmethod
    def _singularize_token(token: str) -> str:
        """安全单数化英文单词，防止复数形式导致同义概念分裂"""
        if len(token) <= 3 or token in _SINGULAR_EXCEPTIONS:
            return token
        if token.endswith("ies") and len(token) > 4:
            return token[:-3] + "y"
        if token.endswith("s") and not token.endswith(("ss", "us", "is")):
            return token[:-1]
        return token

    @classmethod
    def _normalize_slug(cls, raw_slug: str) -> str:
        """规范化英文蛇形 slug（去冗余前后缀 + 词尾单数化 + 下划线折叠），防止同义词分裂"""
        slug = re.sub(r"[^a-z0-9_]+", "_", raw_slug.strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("_")

        for prefix in ("lbl_", "concept_", "node_"):
            if slug.startswith(prefix):
                slug = slug[len(prefix) :]
        for suffix in ("_concept", "_node", "_scripting", "_scripts"):
            if slug.endswith(suffix):
                slug = slug[: -len(suffix)]

        slug = re.sub(r"_+", "_", slug).strip("_")
        if not slug:
            return ""

        tokens = [cls._singularize_token(tok) for tok in slug.split("_") if tok]
        return "_".join(tokens)

    async def extract(self, info: Information) -> List[Labeling]:
        """从单条信息切片中抽取高内聚核心概念节点（基础设施异常向上抛出交由编排器统一隔离/熔断）"""
        content = (info.information or "").strip()
        if not content:
            logger.debug("跳过空切片概念提取 (info_id=%s)", info.info_id)
            return []

        start_ts = time.perf_counter()
        # System Prompt：
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个知识图谱概念抽取专家。请先概括切片的核心业务摘要，再提炼具备跨文档复用价值的核心业务概念。\n"
                    "### 严格抽取规则：\n"
                    f"1. **严格基数上限**：每条切片最多提取 {self.max_concepts} 个最核心概念，宁缺毋滥；若片段仅为通用样板代码或无业务规则，concepts 直接返回空列表 `[]`。\n"
                    "2. **严禁通用语法噪音**：绝对禁止提取编程语言或工具的通用语法特性（如 Bash 的 `set -ex`、`getopts` 参数解析、常规条件判断、标准库用法等），只提取与具体业务系统、专用组件、路径规范、状态流转和降级策略强绑定的领域知识。\n"
                    "3. **受控元类型（6 选 1）**：`mechanism`（机制/策略）、`component`（组件/仓库/模块）、"
                    "`principle`（原则/红线）、`failure_mode`（故障模式）、`metric`（指标/阈值）、`workflow`（流程/协议）。\n"
                    "4. **命名归一化**：`semantic_slug` 统一使用 2~3 个英文单数词的蛇形命名（如 `artifact_pull_fallback`）。"
                ),
            },
            {
                "role": "user",
                "content": f"主题: {info.topic or '通用'}\n片段内容:\n{content[: self.max_input_chars]}",
            },
        ]


        # 底层 LLM 调用超时或网络/鉴权报错直接向上抛出，由 KnowledgeOrganizer 的批量异常隔离与全灭熔断机制统一处理
        raw_call = self.llm.generate_structured(
            messages=messages,
            response_schema=self._output_schema,
        )
        coro = raw_call if inspect.isawaitable(raw_call) else asyncio.sleep(0, result=raw_call)
        if self.timeout_seconds is not None:
            result = await asyncio.wait_for(coro, timeout=self.timeout_seconds)
        else:
            result = await coro

        now_ts = time.time()
        labels: List[Labeling] = []
        seen_ids: Set[str] = set()
        dropped_count = 0

        for item in result.concepts:
            if len(labels) >= self.max_concepts:
                dropped_count += 1
                continue

            clean_name = item.canonical_name.strip()
            clean_slug = self._normalize_slug(item.semantic_slug)
            if not clean_name or not clean_slug:
                dropped_count += 1
                continue

            # 直接使用规范化 clean_slug 生成确定性语义 ID（同 slug 跨切片 100% 收敛为同一节点）
            lbl_id = build_compliant_artifact_id(prefix="lbl", semantic_slug=clean_slug)
            if lbl_id in seen_ids:
                dropped_count += 1
                continue
            seen_ids.add(lbl_id)

            cn_prefix = _META_TYPE_CN_PREFIX.get(item.label_type, "概念")
            formatted_tag = f"<{cn_prefix}：{clean_name}>"
            node_category = _META_TYPE_TO_CATEGORY.get(item.label_type, NodeCategory.CONCEPT)

            # 回写information的`核心摘要`
            clean_slice_summary = (getattr(result, "slice_summary", "") or "").strip()
            lbl = Labeling(
                label_id=lbl_id,
                info_id=info.info_id,
                category=node_category,
                label=formatted_tag,
                timestamp=now_ts,
                rich_semantics={
                    "label_type": item.label_type,
                    "core_definition": item.core_definition.strip(),
                    "trigger_criteria": [c.strip() for c in item.trigger_criteria if c.strip()],
                    "boundaries": [b.strip() for b in item.boundaries_and_counterexamples if b.strip()],
                    "slice_summary": clean_slice_summary,
                },
            )
            labels.append(lbl)

        elapsed = time.perf_counter() - start_ts
        logger.debug(
            "切片概念提取完成 (info_id=%s): 耗时=%.2fs, 原始返回=%d, 保留=%d, 过滤/去重丢弃=%d",
            info.info_id,
            elapsed,
            len(result.concepts),
            len(labels),
            dropped_count,
        )
        return labels
