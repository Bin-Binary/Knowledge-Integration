# /config/system_config.py
import json
from pathlib import Path
from typing import Optional, Dict, List, Any, Literal
from pydantic import BaseModel, Field, SecretStr, ConfigDict, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

def detect_project_root(fallback_path: Optional[Path] = None) -> Path:
    """
    自动探测项目根目录：
    从当前文件向上查找特征标记文件；若未找到（如打包后的独立脚本），则回退到指定目录或文件祖父目录。
    """
    current = Path(__file__).resolve().parent
    markers = ("pyproject.toml", "requirements.txt", ".git", "main.py")
    for parent in [current, *current.parents]:
        if any((parent / marker).exists() for marker in markers):
            return parent
    return fallback_path.resolve() if fallback_path else current.parent

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
    enable_verbose_error_logs: bool = Field(
        default=False,
        description="是否开启详细错误堆栈及非密钥敏感载荷日志（生产环境保持 False）",
    )


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
    extra_body: Dict[str, Any] = Field(default_factory=dict)
    bypass_proxy: bool = Field(
        default=True,
        description="是否忽略系统 HTTP_PROXY/HTTPS_PROXY 环境变量直连大模型端点",
    )

    def get_plain_api_key(self) -> Optional[str]:
        return self.api_key.get_secret_value() if self.api_key else None


class IntentComponentConfig(BaseModel):
    """意图识别组件纯技术运行参数（业务意图清单已剥离至 IntentCatalog）"""
    model_config = ConfigDict(frozen=True, extra="forbid")

    context_window_turns: int = Field(default=4, ge=1, le=20)
    confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0)


class ServerEnvOverrides(BaseSettings):
    """允许通过环境变量覆盖 JSON 中的服务器参数（前缀 SERVER_）"""
    model_config = SettingsConfigDict(env_prefix="SERVER_", env_file=".env", extra="ignore")

    host: Optional[str] = None
    port: Optional[int] = None
    workers: Optional[int] = None
    reload: Optional[bool] = None
    log_level: Optional[str] = None
    enable_verbose_error_logs: Optional[bool] = None

class KnowledgeEnvOverrides(BaseSettings):
    """允许通过环境变量覆盖知识库路径与开关（前缀 KNOWLEDGE_）"""
    model_config = SettingsConfigDict(env_prefix="KNOWLEDGE_", env_file=".env", extra="ignore")

    enabled: Optional[bool] = None
    vault_root: Optional[str] = None
    workspace_root: Optional[str] = None

class EnvSecrets(BaseSettings):
    """专门从环境变量 / .env 读取敏感密钥与网关覆盖地址"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: Optional[SecretStr] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")

class InternalKnowledgeConfig(BaseModel):
    """领域知识库引擎基础设施与开关配置（不可变，所有路径在加载期归一化为绝对路径）"""
    model_config = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True, description="是否启用领域知识库子图")
    vault_root: str = Field(default="./data/llm_wiki", min_length=1, description="知识库 Markdown 仓库根目录（绝对路径）")
    workspace_root: str = Field(default=".", min_length=1, description="工作区根目录（绝对路径）")
    quality_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="知识检索/沉淀质量准入阈值")
    max_concurrency: int = Field(default=5, ge=1, le=32, description="知识引擎并发任务上限")

    @field_validator("vault_root", "workspace_root", mode="before")
    @classmethod
    def resolve_to_absolute_path(cls, v: Any, info: ValidationInfo) -> str:
        if not isinstance(v, (str, Path)) or not str(v).strip():
            raise ValueError("Path configuration must be a non-empty string or Path.")

        p = Path(v).expanduser()
        if p.is_absolute():
            return str(p.resolve())

        # 从校验上下文获取基准目录，若直接实例化未传 context 则自动探测项目根目录
        base_dir: Path = (info.context or {}).get("base_dir") or detect_project_root()
        return str((base_dir / p).resolve())

class AgentSystemConfig(BaseModel):
    """全系统根配置对象：仅管理基础设施、模型池与技术运行参数"""
    model_config = ConfigDict(frozen=True, extra="forbid")

    server: ServerConfig = Field(default_factory=ServerConfig)
    llm_profiles: Dict[str, LLMProfileConfig]
    intent_recognition: IntentComponentConfig = Field(default_factory=IntentComponentConfig)
    internal_knowledge: InternalKnowledgeConfig = Field(default_factory=InternalKnowledgeConfig)

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

        # 合并环境变量对 InternalKnowledge 参数的动态覆盖
        kn_section = raw_data.setdefault("internal_knowledge", {})
        kn_env = KnowledgeEnvOverrides()
        for field_name, val in kn_env.model_dump(exclude_none=True).items():
            # 若环境变量传入的是相对路径，基于当前进程 CWD 解析，符合运维直觉
            if field_name in ("vault_root", "workspace_root") and not Path(val).expanduser().is_absolute():
                val = str((Path.cwd() / Path(val).expanduser()).resolve())
            kn_section[field_name] = val

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
