# app/llm_factory.py
import os
from contextlib import contextmanager
from typing import Dict, Iterator

import httpx
from langchain_openai import ChatOpenAI

from config.system_config import AgentSystemConfig, LLMProfileConfig
from infra.adapters import LangChainStructuredAdapter

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
) -> LangChainStructuredAdapter:
    """通用模型适配器工厂：按角色（'intent' / 'planner' / 'executor'）构建隔离客户端"""
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
    return LangChainStructuredAdapter(chat_model=chat_model)


def _get_or_fallback_adapter(
    sys_cfg: AgentSystemConfig, role: str, fallback: LangChainStructuredAdapter
) -> LangChainStructuredAdapter:
    """按角色获取模型适配器，若配置中未单独声明该角色则平滑回退至默认适配器"""
    try:
        return build_llm_adapter(sys_cfg, role)
    except KeyError:
        return fallback


def build_adapter_pool(
    sys_cfg: AgentSystemConfig,
) -> Dict[str, LangChainStructuredAdapter]:
    """构建全系统多角色隔离模型适配器池"""
    intent_adapter = build_llm_adapter(sys_cfg, "intent")
    executor_adapter = _get_or_fallback_adapter(sys_cfg, "executor", intent_adapter)
    return {
        "intent": intent_adapter,
        "recovery": _get_or_fallback_adapter(sys_cfg, "recovery", intent_adapter),
        "knowledge": _get_or_fallback_adapter(sys_cfg, "knowledge", intent_adapter),
        "executor": executor_adapter,
        "planner": _get_or_fallback_adapter(sys_cfg, "planner", executor_adapter),
    }
