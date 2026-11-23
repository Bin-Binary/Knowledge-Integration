# protocols/__init__.py
"""
系统核心协议（Contracts / Interfaces）统一出口。

设计原则：
1. 依赖倒置（DIP）：所有跨模块依赖均应直接从本包导入 Protocol，严禁直接依赖具体实现类。
2. 门面收敛：屏蔽内部按领域拆分的子模块路径细节，提供扁平化的导入体验。
3. 显式契约：严格通过 `__all__` 控制对外暴露的公共符号，隐藏内部泛型变量与辅助类型。
"""

# 1. 执行器、工具挂载与实例注册解析协议
from .agent import (
    AgentProtocol,
    ToolCapableAgentProtocol,
)
from .registry import (
    AgentRegistrarProtocol,
    AgentResolverProtocol,
)

# 2. 核心调度流水线组件协议（已按子域拆分）
from .routing import (
    IntentRecognizerProtocol,
    RouterProtocol,
)
from .planning import (
    PlannerProtocol,
)
from .recovery import (
    ExceptionMapperProtocol,
    ExceptionRecoveryProtocol,
)

# 3. 通用评估与过滤协议
from .evaluation import (
    QualityEvaluatorProtocol,
)

# 4. 域内知识库全链路闭环协议
from .internal_knowledge import (
    GapRoutingProtocol,
    InternalKnowledgeEngineProtocol,
    KnowledgeAcquisitionProtocol,
    KnowledgeApplicationProtocol,
    KnowledgeOrganizationProtocol,
    KnowledgeStorageProtocol,
)

# 5. 底层模型与基础设施协议
from .llm import (
    StructuredLLMProtocol,
)

# 6.数据清洗协议
from .sanitization import (
    InputSanitizerProtocol,
    RawPayloadRepairerProtocol
)
__all__ = [
    # Agent & Registry
    "AgentProtocol",
    "ToolCapableAgentProtocol",
    "AgentResolverProtocol",
    "AgentRegistrarProtocol",
    # Routing, Planning & Recovery
    "IntentRecognizerProtocol",
    "RouterProtocol",
    "PlannerProtocol",
    "ExceptionMapperProtocol",
    "ExceptionRecoveryProtocol",
    # Evaluation
    "QualityEvaluatorProtocol",
    # Internal Knowledge
    "KnowledgeApplicationProtocol",
    "GapRoutingProtocol",
    "KnowledgeAcquisitionProtocol",
    "KnowledgeOrganizationProtocol",
    "KnowledgeStorageProtocol",
    "InternalKnowledgeEngineProtocol",
    # LLM
    "StructuredLLMProtocol",
    # Sanitization
    "InputSanitizerProtocol",
    "RawPayloadRepairerProtocol"
]
