"""LLM client.

Creates a ChatOpenAI instance configured for one of the supported
providers. Provider selection is driven by the LLM_PROVIDER env var.

Supported providers:
  - deepseek : uses OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL
  - qwen     : uses DASHSCOPE_API_KEY / DASHSCOPE_BASE_URL / DASHSCOPE_MODEL

Environment variables (loaded from .env at project root):
  - LLM_PROVIDER        : "deepseek" or "qwen"; default "qwen"
  - OPENAI_API_KEY      : required when provider=deepseek
  - OPENAI_BASE_URL     : optional, default https://api.deepseek.com
  - OPENAI_MODEL        : optional, default deepseek-chat
  - DASHSCOPE_API_KEY   : required when provider=qwen
  - DASHSCOPE_BASE_URL  : required when provider=qwen
  - DASHSCOPE_MODEL     : required when provider=qwen

Design notes:
  - Do not hardcode secrets.
  - Provider-specific configs are kept separate to allow side-by-side keys.
  - The cached constructor key includes provider so switching does not
    reuse a stale instance.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


# ---------------------------------------------------------------------------
# .env loading
# ---------------------------------------------------------------------------

def _load_env_once() -> None:
    """Load .env from project root once."""
    here = Path(__file__).resolve()
    project_root = here.parent.parent.parent
    env_path = project_root / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)


# ---------------------------------------------------------------------------
# Provider config
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProviderConfig:
    name: str
    api_key: str
    base_url: str
    model: str


def _resolve_provider() -> ProviderConfig:
    """Resolve the active provider config from environment variables.

    Raises RuntimeError if required variables are missing.
    """
    provider = os.getenv("LLM_PROVIDER", "qwen").strip().lower()

    if provider == "deepseek":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "LLM_PROVIDER=deepseek but OPENAI_API_KEY is not set."
            )
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
        model = os.getenv("OPENAI_MODEL", "deepseek-chat")
        return ProviderConfig("deepseek", api_key, base_url, model)

    if provider == "qwen":
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "LLM_PROVIDER=qwen but DASHSCOPE_API_KEY is not set."
            )
        base_url = os.getenv("DASHSCOPE_BASE_URL", "")
        if not base_url:
            raise RuntimeError(
                "LLM_PROVIDER=qwen but DASHSCOPE_BASE_URL is not set."
            )
        model = os.getenv("DASHSCOPE_MODEL", "")
        if not model:
            raise RuntimeError(
                "LLM_PROVIDER=qwen but DASHSCOPE_MODEL is not set."
            )
        return ProviderConfig("qwen", api_key, base_url, model)

    raise RuntimeError(
        f"Unsupported LLM_PROVIDER: {provider!r}. "
        f"Expected 'deepseek' or 'qwen'."
    )


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

@lru_cache(maxsize=4)
def _cached_llm(
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    temperature: float,
    timeout: float,
) -> ChatOpenAI:
    """Internal cached constructor. Key includes provider to avoid cross-talk."""
    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        timeout=timeout,
    )


def get_llm(
    temperature: float = 0.0,
    timeout: float = 60.0,
) -> ChatOpenAI:
    """Return a ChatOpenAI instance for the active provider.

    Parameters
    ----------
    temperature : float
        Default 0.0 for deterministic selection tasks.
    timeout : float
        Request timeout in seconds.

    Raises
    ------
    RuntimeError
        If the provider config is incomplete.
    """
    _load_env_once()
    cfg = _resolve_provider()
    return _cached_llm(
        provider=cfg.name,
        api_key=cfg.api_key,
        base_url=cfg.base_url,
        model=cfg.model,
        temperature=temperature,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Debug helpers
# ---------------------------------------------------------------------------

def describe_active_provider() -> dict[str, str]:
    """Return active provider info for logging."""
    _load_env_once()
    cfg = _resolve_provider()
    return {
        "provider": cfg.name,
        "base_url": cfg.base_url,
        "model": cfg.model,
    }


def get_model_name() -> str:
    """Return the active model name."""
    return describe_active_provider()["model"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    info = describe_active_provider()
    llm = get_llm()

    print(f"Provider: {info['provider']}")
    print(f"Model   : {info['model']}")
    print(f"Base    : {info['base_url']}")
    print(f"Timeout : {llm.request_timeout}")
    print(f"Class   : {type(llm).__name__}")


if __name__ == "__main__":
    _main()