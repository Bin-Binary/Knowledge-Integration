# /componnets/internal_knowledge/__init__.py
"""域内知识库构建与检索组件（对外统一门面）

调用契约说明：
    1. 并发安全约束：通过 `create_default_knowledge_engine(llm_client=...)` 传入的客户端必须支持异步非阻塞并发调用。
    2. 双轨异常处理：
       - 底层模型/网络异常（如 `ModelServiceUnavailableError`、`StructuredOutputError`、`RateLimitError`、`APITimeoutError`）
         直接向上透传，交由外层全局恢复节点处理；
       - 知识库业务阻断（如工作区路径越界、缺失上下文、全源采集失败）抛出 `KnowledgePipelineError`（继承自 `AgentBusinessError`）。
"""
from components.internal_knowledge.factory import create_default_knowledge_engine
from components.internal_knowledge.protocols import InternalKnowledgeEngineProtocol
from components.internal_knowledge.schemas.pipeline_envelope import PipelineEnvelope
from components.internal_knowledge.schemas.resolve_problem import ResolutionOutcome, ResolveProblem
from components.internal_knowledge.schemas.source_uri import SourceScheme, SourceURI

__all__ = [
    "create_default_knowledge_engine",
    "InternalKnowledgeEngineProtocol",
    "PipelineEnvelope",
    "ResolveProblem",
    "ResolutionOutcome",
    "SourceURI",
    "SourceScheme",

]
