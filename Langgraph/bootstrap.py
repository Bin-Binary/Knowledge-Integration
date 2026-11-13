import os
from pathlib import Path
import httpx
from typing import Optional, Dict, Any, Iterator
from contextlib import contextmanager

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from config.system_config import AgentSystemConfig, LLMProfileConfig

from infra.adapters import LangChainStructuredAdapter
from components.intent.hybrid_recognizer import HybridIntentRecognizer
from components.recovery.composite_recovery import CompositeRecoveryManager
from components.recovery.json_heal_recovery import JsonHealRecoveryManager
from graphs.master_graph import build_master_agent_graph

_PROXY_KEYS = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy", "OPENAI_PROXY")

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

class AgentApplication:
    """
    生产环境 Agent 应用容器：
    单例管理配置中心、多模型适配器池、持久化存储及编译后的 LangGraph 主控图。
    """
    def __init__(
        self,
        sys_cfg: AgentSystemConfig,
        checkpointer: Optional[Any] = None
    ) -> None:
        self.sys_cfg = sys_cfg
        self.checkpointer = checkpointer or MemorySaver()
        self.graph: CompiledStateGraph = self._initialize_graph()

    @classmethod
    def from_config_file(
        cls,
        config_path: str | Path = "config/agent_settings.json",
        checkpointer: Optional[Any] = None
    ) -> "AgentApplication":
        sys_cfg = AgentSystemConfig.load_from_json(config_path)
        return cls(sys_cfg=sys_cfg, checkpointer=checkpointer)

    def _build_llm_adapter(self, role: str) -> LangChainStructuredAdapter:
        """通用模型适配器工厂：按角色（'intent' / 'planner' / 'executor'）构建隔离客户端
        支持通过 bypass_proxy 配置项安全隔离公司代理，同时注入同步与异步 httpx 客户端; 内网模型走直连、公网模型走代理:
        只在服务启动加载配置时执行一次：
        1. 临时屏蔽环境变量，防止 ChatOpenAI/OpenAI SDK 在初始化阶段偷读代理；
        2. 注入 trust_env=False 的同步/异步 httpx 客户端，确保运行期永久直连内网；
        3. 退出 with 块后立刻恢复系统代理环境变量，对其他公网工具零影响。
        """
        profile: LLMProfileConfig = self.sys_cfg.get_llm_profile(role)

        # 根据配置决定是否绕过系统代理环境变量（trust_env=False）
        with temporary_no_proxy(enabled=profile.bypass_proxy):
            sync_client = httpx.Client(
                trust_env=not profile.bypass_proxy,
                timeout=profile.timeout_seconds
            )
            async_client = httpx.AsyncClient(
                trust_env=not profile.bypass_proxy,
                timeout=profile.timeout_seconds
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
            http_async_client=async_client              
        )
        return LangChainStructuredAdapter(chat_model=chat_model)

    def _initialize_graph(self) -> CompiledStateGraph:
        # 1. 构建意图识别组件
        intent_adapter = self._build_llm_adapter("intent")
        intent_cfg = self.sys_cfg.intent_recognition

        recognizer = HybridIntentRecognizer(
            command_map=intent_cfg.command_map,
            llm_client=intent_adapter,
            context_window_turns=intent_cfg.context_window_turns
        )
        # 2. 构建独立异常恢复组件（基类 + 子类扩展组合，后续新增异常类型只需向列表追加子类）
        try:
            recovery_adapter = self._build_llm_adapter("recovery")
        except Exception:
            recovery_adapter = intent_adapter

        recovery_manager = CompositeRecoveryManager(
            handlers=[
                JsonHealRecoveryManager(structured_llm=recovery_adapter),
            ]
        )

        # 2. [预留扩展位] 后续接入 Router / Planner / Executors 时在此组装

        # 3. 编译并返回主控状态图
        return build_master_agent_graph(
            intent_recognizer=recognizer,
            recovery_manager=recovery_manager,
            checkpointer=self.checkpointer
        )

    def invoke_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> dict:
        """同步单轮调用接口"""
        config = {"configurable": {"thread_id": session_id}}
        input_payload = {
            "session_id": session_id,
            "messages": [HumanMessage(content=user_message)],
            "user_profile": user_profile or {}
        }
        return self.graph.invoke(input_payload, config=config)

    async def ainvoke_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> dict:
        """异步高并发单轮调用接口"""
        config = {"configurable": {"thread_id": session_id}}
        input_payload = {
            "session_id": session_id,
            "messages": [HumanMessage(content=user_message)],
            "user_profile": user_profile or {}
        }
        return await self.graph.ainvoke(input_payload, config=config)
