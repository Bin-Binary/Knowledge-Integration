# /components/internal_knowledge/factory.py
import components.internal_knowledge.acquisition.handlers  # noqa: F401
import components.internal_knowledge.organization.plugins  # noqa: F401

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from protocols.llm import StructuredLLMProtocol
from components.internal_knowledge.protocols import (
    GapRoutingProtocol,
    InternalKnowledgeEngineProtocol,
    KnowledgeAcquisitionProtocol,
    KnowledgeApplicationProtocol,
    KnowledgeStorageProtocol,
)

from components.internal_knowledge.acquisition.registry import AcquisitionPluginRegistry
from components.internal_knowledge.acquisition.workspace_gap_router import WorkspaceFileGapRouter
from components.internal_knowledge.application.guarded_applicator import GuardedKnowledgeApplicator
from components.internal_knowledge.application.llm_applicator import LLMKnowledgeApplicator
from components.internal_knowledge.organization.factory import build_knowledge_organizer
from components.internal_knowledge.storage.local_markdown_storage import LocalMarkdownStorage
from components.internal_knowledge.internal_knowledge_engine import InternalKnowledgeEngine

logger = logging.getLogger(__name__)


def create_default_knowledge_engine(
    llm_client: StructuredLLMProtocol,
    *,
    vault_root: str | Path = "./data/llm_wiki",
    workspace_root: str | Path = ".",
    storage: Optional[KnowledgeStorageProtocol] = None,
    application: Optional[KnowledgeApplicationProtocol] = None,
    acquisition: Optional[KnowledgeAcquisitionProtocol] = None,
    gap_router: Optional[GapRoutingProtocol] = None,
    quality_threshold: float = 0.5,
    max_concurrency: int = 5,
    organize_timeout_seconds: Optional[float] = 150.0,
    extra_shared_deps: Optional[Dict[str, Any]] = None,
) -> InternalKnowledgeEngineProtocol:
    """
    域内知识库总控引擎装配工厂（遵循 DIP 与 OCP）：
    - 【存储】：默认装配 LocalMarkdownStorage；
    - 【运用】：默认装配 LLMKnowledgeApplicator 并自动包裹 GuardedKnowledgeApplicator 守卫；
    - 【采集】：默认装配 CompositeKnowledgeAcquirer，自动从 AcquisitionPluginRegistry 挂载全部已注册处理器；
    - 【组织】：通过 shared_deps 自动按签名注入装配四阶算子流水线。
    """
    shared_deps: Dict[str, Any] = {
        "llm_client": llm_client,
        "workspace_root": workspace_root,
        **(extra_shared_deps or {}),
    }

    # 1. 【存储】支持外部注入覆盖，默认使用本地 Markdown 知识库
    effective_storage = storage or LocalMarkdownStorage(vault_root=vault_root)
    shared_deps["storage"] = effective_storage

    # 2. 【运用】支持外部注入覆盖，默认包一层 GuardedKnowledgeApplicator 统一收口校验与日志
    raw_application = application or LLMKnowledgeApplicator(
        llm_client=llm_client,
        storage=effective_storage,
    )
    effective_application = (
        raw_application
        if isinstance(raw_application, GuardedKnowledgeApplicator)
        else GuardedKnowledgeApplicator(raw_application)
    )

    # 3. 【采集】自动从 AcquisitionPluginRegistry 发现并装配组合调度器
    if acquisition is not None:
        effective_acquisition = acquisition
    else:
        effective_router = gap_router or WorkspaceFileGapRouter(
            llm_client=llm_client,
            workspace_root=workspace_root,
        )
        effective_acquisition = AcquisitionPluginRegistry.build_acquirer(
            gap_router=effective_router,
            shared_deps=shared_deps,
            max_concurrency=max_concurrency,
        )

    # 4. 【组织】使用共享依赖池自动按签名注入四阶算子
    organizer = build_knowledge_organizer(
        shared_deps=shared_deps,
        quality_threshold=quality_threshold,
        max_concurrency=max_concurrency,
    )

    # 5. 返回纯协议接口
    return InternalKnowledgeEngine(
        storage=effective_storage,
        application=effective_application,
        acquisition=effective_acquisition,
        organization=organizer,
        organize_timeout_seconds=organize_timeout_seconds,
    )
