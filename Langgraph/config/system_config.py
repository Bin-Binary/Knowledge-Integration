import json
from pathlib import Path
from typing import Optional, Dict, List, Literal
from pydantic import BaseModel, Field, SecretStr, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseModel):
    """HTTP 网关与 ASGI 服务器运行配置（不可变）"""
    model_config = ConfigDict(frozen=True, extra="forbid")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1, le=64)
    reload: bool = Field(default=False)
    log_level: Literal["debug", "info", "warning", "error", "critical"] = Field(default="info")
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    request_timeout_seconds: float = Field(default=60.0, gt=0.0)


class LLMProfileConfig(BaseModel):
    """单个大模型节点的纯静态运行参数（不可变）"""
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: Literal["openai", "anthropic", "deepseek", "vllm", "azure"] = "openai"
    model_name: str = Field(..., min_length=1)
    api_key: Optional[SecretStr] = None
    base_url: Optional[str] = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1024, gt=0)
    timeout_seconds: float = Field(default=15.0, gt=0.0)
    max_retries: int = Field(default=2, ge=0, le=5)
    bypass_proxy: bool = Field(
        default=True,
        description="是否忽略系统 HTTP_PROXY/HTTPS_PROXY 环境变量直连大模型端点"
    )
    def get_plain_api_key(self) -> Optional[str]:
        return self.api_key.get_secret_value() if self.api_key else None


class IntentComponentConfig(BaseModel):
    """意图识别组件配置块"""
    model_config = ConfigDict(frozen=True, extra="forbid")

    context_window_turns: int = Field(default=4, ge=1, le=20)
    confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    command_map: Dict[str, str] = Field(default_factory=dict)


class RoutingComponentConfig(BaseModel):
    """路由调度组件配置块"""
    model_config = ConfigDict(frozen=True, extra="forbid")

    default_fallback_node: str = Field(default="clarification_agent")
    intent_to_node: Dict[str, str] = Field(default_factory=dict)


class ServerEnvOverrides(BaseSettings):
    """允许通过环境变量覆盖 JSON 中的服务器参数（前缀 SERVER_）"""
    model_config = SettingsConfigDict(env_prefix="SERVER_", env_file=".env", extra="ignore")

    host: Optional[str] = None
    port: Optional[int] = None
    workers: Optional[int] = None
    reload: Optional[bool] = None
    log_level: Optional[str] = None


class EnvSecrets(BaseSettings):
    """专门从环境变量 / .env 读取敏感密钥与网关覆盖地址"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: Optional[SecretStr] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")


class AgentSystemConfig(BaseModel):
    """全系统根配置对象：由 JSON 文件加载并自动注入环境变量覆盖"""
    model_config = ConfigDict(frozen=True, extra="forbid")

    server: ServerConfig = Field(default_factory=ServerConfig)
    llm_profiles: Dict[str, LLMProfileConfig]
    intent_recognition: IntentComponentConfig = Field(default_factory=IntentComponentConfig)
    routing: RoutingComponentConfig = Field(default_factory=RoutingComponentConfig)

    @classmethod
    def load_from_json(cls, json_path: str | Path) -> "AgentSystemConfig":
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path.resolve()}")

        raw_data = json.loads(path.read_text(encoding="utf-8"))

        # 1. 合并环境变量对 Server 参数的动态覆盖
        srv_section = raw_data.setdefault("server", {})
        srv_env = ServerEnvOverrides()
        for field_name, val in srv_env.model_dump(exclude_none=True).items():
            srv_section[field_name] = val

        # 2. 合并环境变量对 LLM 密钥与地址的注入
        secrets = EnvSecrets()
        for _, prof in raw_data.get("llm_profiles", {}).items():
            if not prof.get("api_key") and secrets.openai_api_key:
                prof["api_key"] = secrets.openai_api_key.get_secret_value()
            if not prof.get("base_url") and secrets.openai_base_url:
                prof["base_url"] = secrets.openai_base_url

        return cls.model_validate(raw_data)

    def get_llm_profile(self, role: str) -> LLMProfileConfig:
        if role not in self.llm_profiles:
            raise KeyError(f"LLM profile '{role}' is not defined in configuration.")
        return self.llm_profiles[role]
