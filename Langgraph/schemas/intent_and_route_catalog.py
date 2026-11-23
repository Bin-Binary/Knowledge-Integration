# /schemas/intent_and_route_catalog.py
import re
from typing import Dict, List, Optional
from pydantic import Field, model_validator, field_validator
from schemas.base import ImmutableSchema, DocumentedEnum

class TargetDomain(DocumentedEnum):
    """系统顶层处理域定义"""
    KNOWLEDGE = ("knowledge", "domain", "知识领域子图（负责深度知识沉淀与向量/图谱检索）")
    EXECUTION = ("execution", "domain", "通用业务执行域（负责对话回复、规划编排与工具调用）")

class FastIntentRule(ImmutableSchema):
    """非 LLM 快速正则/关键词匹配规则"""
    intent: str = Field(..., min_length=1, description="命中的目标意图标签")
    patterns: List[str] = Field(..., min_length=1, description="正则表达式列表（忽略大小写）")
    confidence: float = Field(default=0.98, ge=0.0, le=1.0, description="规则命中时的默认置信度")

    @field_validator("patterns")
    @classmethod
    def validate_regex_syntax(cls, v: List[str]) -> List[str]:
        """启动期 Fail-Fast 校验正则表达式语法，防止运行期崩溃"""
        for pat in v:
            re.compile(pat)
        return v

class IntentCatalogItem(ImmutableSchema):
    """单个业务意图的语义定义（供意图识别器动态生成分类清单）"""
    intent: str = Field(..., min_length=1, description="意图唯一标识标签")
    description: str = Field(..., min_length=1, description="意图业务含义与适用边界说明")
    examples: List[str] = Field(default_factory=list, description="典型用户说法示例")

    def to_catalog_line(self) -> str:
        """格式化为单条意图候选说明"""
        ex_str = f"（示例: {' / '.join(self.examples)}）" if self.examples else ""
        return f"- `{self.intent}`: {self.description}{ex_str}"


class IntentCatalog(ImmutableSchema):
    """意图目录配置模型"""
    command_map: Dict[str, str] = Field(default_factory=dict, description="前缀静态指令直达映射")
    fast_rules: List[FastIntentRule] = Field(default_factory=list, description="非 LLM 快速正则/关键词匹配规则列表")
    intents: List[IntentCatalogItem] = Field(default_factory=list, description="语义意图候选列表")

    def format_catalog_block(self) -> str:
        """仅负责将意图列表渲染为结构化候选清单"""
        if not self.intents:
            return "- `chitchat`: 日常对话与通用问答"
        return "\n".join(item.to_catalog_line() for item in self.intents)


class RouteTargetSpec(ImmutableSchema):
    """单个意图的路由目标规格"""
    target_domain: TargetDomain = Field(
        default=TargetDomain.EXECUTION,
        description="所属处理域（knowledge=知识领域子图, execution=通用业务执行器）",
    )
    target_node: str = Field(..., min_length=1, description="目标节点或 Agent 唯一标识")
    fallback_node: Optional[str] = Field(default=None, description="该路由专属降级节点（可选）")
    skip_knowledge: bool = Field(
        default=False,
        description="是否跳过知识库检索直接执行（适用于纯闲聊 chitchat 等无需背景知识的场景）",
    )

    @model_validator(mode="after")
    def validate_domain_and_skip_consistency(self) -> "RouteTargetSpec":
        if self.target_domain == TargetDomain.KNOWLEDGE and self.skip_knowledge:
            raise ValueError(
                f"路由配置冲突：target_node='{self.target_node}' 属于 knowledge 域，不能设置 skip_knowledge=True"
            )
        return self

class RouteCatalog(ImmutableSchema):
    """路由调度目录配置模型"""
    default_fallback_node: str = Field(default="general_chat_agent", description="全局默认兜底执行节点")
    min_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="最低置信度准入阈值")
    routes: Dict[str, RouteTargetSpec] = Field(default_factory=dict, description="意图到目标节点的映射表")


class AgentBusinessConfig(ImmutableSchema):
    """全系统业务领域配置聚合根（含跨目录一致性快速失败校验）"""
    intent_catalog: IntentCatalog
    route_catalog: RouteCatalog

    @model_validator(mode="after")
    def validate_cross_catalog_consistency(self) -> "AgentBusinessConfig":
        defined_intents = {item.intent for item in self.intent_catalog.intents}
        defined_intents.update(self.intent_catalog.command_map.values())
        defined_intents.update(rule.intent for rule in self.intent_catalog.fast_rules)

        unrouted = defined_intents - set(self.route_catalog.routes.keys())
        if unrouted:
            raise ValueError(f"业务配置校验失败：以下意图缺少路由映射 -> {unrouted}")

        unknown = set(self.route_catalog.routes.keys()) - defined_intents
        if unknown:
            raise ValueError(f"业务配置校验失败：路由表引用了未定义的幽灵意图 -> {unknown}")

        return self

