# /components/internal_knowledge/factory.py
from pathlib import Path
from typing import Optional

from protocols.llm import StructuredLLMProtocol
from protocols.internal_knowledge import (
    GapRoutingProtocol,
    InternalKnowledgeEngineProtocol,
)

# 显式导入触发 @BaseKnowledgeAcquirer.register 装饰器注册
from components.internal_knowledge.acquisition.shell_repo_acquirer import ShellRepoAcquirer
from components.internal_knowledge.application.llm_applicator import LLMKnowledgeApplicator
from components.internal_knowledge.organization.factory import build_knowledge_organizer
from components.internal_knowledge.storage.local_markdown_storage import LocalMarkdownStorage
from components.internal_knowledge.internal_knowledge_engine import InternalKnowledgeEngine


def create_default_knowledge_engine(
    llm_client: StructuredLLMProtocol,
    *,
    vault_root: str | Path = "./data/llm_wiki",
    workspace_root: str | Path = ".",
    gap_router: Optional[GapRoutingProtocol] = None,
    quality_threshold: float = 0.5,
    max_concurrency: int = 5,
) -> InternalKnowledgeEngineProtocol:
    """域内知识库总控引擎一键装配工厂。

    严格遵循依赖倒置（DIP）：对外仅返回高度泛化的 InternalKnowledgeEngineProtocol 接口，
    完全隐藏内部 Storage / Application / Acquisition / Organization 四大环节装配细节。
    """
    # 1. 实例化【存储】环节（遵循 LLM-WIKI 三层生命周期 × 四层抽象粒度治理）
    storage = LocalMarkdownStorage(vault_root=vault_root)

    # 2. 实例化【运用】环节（注入结构化 LLM 与存储内容水合契约）
    applicator = LLMKnowledgeApplicator(
        llm_client=llm_client,
        storage=storage,
    )

    # 3. 实例化【采集】环节（内置策略路由表，支持静态定位符与缺口动态路由双模式）
    # acquirer = ShellRepoAcquirer(  # 原因: ShellRepoAcquirer.__init__ 不接受 workspace_root 参数，传入会导致 TypeError
    #     gap_router=gap_router,
    #     workspace_root=workspace_root,
    # )
    acquirer = ShellRepoAcquirer(
        gap_router=gap_router,
    )

    # 4. 自动发现并装配【组织】环节（3.1 评估 -> 3.2 提特征 -> 3.3 建边 -> 3.4 图聚类）
    organizer = build_knowledge_organizer(
        plugin_kwargs={
            "llm_hybrid": {"llm_client": llm_client},
            "llm_label": {"llm_client": llm_client},
            "llm_relation": {"llm_client": llm_client},
        },
        quality_threshold=quality_threshold,
        max_concurrency=max_concurrency,
    )

    # 5. 组装并返回总控闭环引擎
    return InternalKnowledgeEngine(
        storage=storage,
        application=applicator,
        acquisition=acquirer,
        organization=organizer,
    )
