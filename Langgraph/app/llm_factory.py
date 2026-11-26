# app/llm_factory.py
import os
import logging
from contextlib import contextmanager
from typing import Any, Dict, Iterator

import httpx
from langchain_openai import ChatOpenAI

from config import AgentSystemConfig, LLMProfileConfig
from infra import HybridLangChainAdapter
from infra.middlewares.local_json_healer import LocalJsonHealerMiddleware
from infra.middlewares.model_failover import ModelFailoverMiddleware

logger = logging.getLogger(__name__)

_PROXY_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "http_proxy",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
    "OPENAI_PROXY",
)


@contextmanager
def temporary_no_proxy(enabled: bool = True) -> Iterator[None]:
    """仅在客户端实例化期间临时屏蔽代理环境变量，退出立刻无损恢复"""
    if not enabled:
        yield
        return
    saved_env = {k: os.environ.pop(k) for k in _PROXY_KEYS if k in os.environ}
    try:
        yield
    finally:
        os.environ.update(saved_env)


def build_llm_adapter(
    sys_cfg: AgentSystemConfig, role: str
) -> Any:  # 满足 StructuredLLMProtocol & StreamingLLMProtocol
    profile: LLMProfileConfig = sys_cfg.get_llm_profile(role)

    with temporary_no_proxy(enabled=profile.bypass_proxy):
        sync_client = httpx.Client(
            trust_env=not profile.bypass_proxy,
            timeout=profile.timeout_seconds,
        )
        async_client = httpx.AsyncClient(
            trust_env=not profile.bypass_proxy,
            timeout=profile.timeout_seconds,
        )

    chat_model = ChatOpenAI(
        model=profile.model_name,
        temperature=profile.temperature,
        max_tokens=profile.max_tokens,
        timeout=profile.timeout_seconds,
        max_retries=profile.max_retries,
        api_key=profile.get_plain_api_key(),
        base_url=profile.base_url,
        http_client=sync_client,
        http_async_client=async_client,
        extra_body=profile.extra_body,
    )
    raw_adapter = HybridLangChainAdapter(chat_model=chat_model)
    # 统一挂载 L1 零成本格式自愈切面
    return LocalJsonHealerMiddleware(raw_adapter)

def _get_or_fallback_adapter(
    sys_cfg: AgentSystemConfig, role: str, fallback: HybridLangChainAdapter
) -> HybridLangChainAdapter:
    """按角色获取模型适配器，若配置中未单独声明该角色则显式打印告警并平滑回退"""
    try:
        adapter = build_llm_adapter(sys_cfg, role)
        logger.info("[LLMFactory] Initialized isolated adapter for role '%s' (model=%s)", role, sys_cfg.get_llm_profile(role).model_name)
        return adapter
    except KeyError:
        logger.warning("[LLMFactory] Profile for role '%s' not found in config; falling back to default adapter!", role)
        return fallback

def build_adapter_pool(sys_cfg: AgentSystemConfig) -> Dict[str, Any]:
    """
    构建全系统多角色高可用模型适配器池：
    洋葱切面结构：ModelFailoverMiddleware(外层灾备) -> LocalJsonHealerMiddleware(内层L1清洗) -> HybridLangChainAdapter
    """
    intent_raw = build_llm_adapter(sys_cfg, "intent")
    recovery_adapter = _get_or_fallback_adapter(sys_cfg, "recovery", intent_raw)
    knowledge_raw = _get_or_fallback_adapter(sys_cfg, "knowledge", intent_raw)
    executor_raw = _get_or_fallback_adapter(sys_cfg, "executor", intent_raw)
    planner_raw = _get_or_fallback_adapter(sys_cfg, "planner", executor_raw)

    def _with_failover(primary: Any) -> Any:
        # 若主模型与灾备模型是同一个实例，跳过多余包裹
        if primary is recovery_adapter:
            return primary
        return ModelFailoverMiddleware(primary=primary, backup=recovery_adapter)

    return {
        "intent": _with_failover(intent_raw),
        "knowledge": _with_failover(knowledge_raw),
        "executor": _with_failover(executor_raw),
        "planner": _with_failover(planner_raw),
        "recovery": recovery_adapter,  # 供 L2 恢复插件直接使用，不再套一层自身灾备
    }
