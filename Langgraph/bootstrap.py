# /bootstrap.py
import os
import uuid
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
from infra.observability import (
    setup_global_observability_logging,
    bind_observability_context,
    reset_observability_context,
)
from components.intent.hybrid_recognizer import HybridIntentRecognizer
from components.recovery.composite_recovery import CompositeRecoveryManager
from components.recovery.json_heal_recovery import JsonHealRecoveryManager
from components.internal_knowledge.factory import create_default_knowledge_engine
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
        # 应用启动时，根据 ServerConfig 初始化全局日志级别与脱敏过滤器
        setup_global_observability_logging(
            log_level=self.sys_cfg.server.log_level,
            enable_verbose=self.sys_cfg.server.enable_verbose_error_logs,
        )
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
            http_async_client=async_client,
            extra_body=profile.extra_body,              
        )
        return LangChainStructuredAdapter(chat_model=chat_model)

    def _initialize_graph(self) -> CompiledStateGraph:
        # 构建意图识别组件
        intent_adapter = self._build_llm_adapter("intent")
        intent_cfg = self.sys_cfg.intent_recognition

        recognizer = HybridIntentRecognizer(
            command_map=intent_cfg.command_map,
            llm_client=intent_adapter,
            context_window_turns=intent_cfg.context_window_turns
        )
        # 构建独立异常恢复组件（基类 + 子类扩展组合，后续新增异常类型只需向列表追加子类）        
        try:
            recovery_adapter = self._build_llm_adapter("recovery")
        except Exception:
            recovery_adapter = intent_adapter

        recovery_manager = CompositeRecoveryManager(
            handlers=[
                JsonHealRecoveryManager(structured_llm=recovery_adapter),
            ]
        )

        # [预留扩展位起点] 后续接入新组件时在此组装 --------
        try:
            knowledge_adapter = self._build_llm_adapter("knowledge")
        except Exception:
            knowledge_adapter = intent_adapter

        knowledge_cfg = getattr(self.sys_cfg, "internal_knowledge", None)
        knowledge_engine = create_default_knowledge_engine(
            llm_client=knowledge_adapter,
            vault_root=getattr(knowledge_cfg, "vault_root", "./data/llm_wiki"),
            workspace_root=getattr(knowledge_cfg, "workspace_root", "."),
            quality_threshold=getattr(knowledge_cfg, "quality_threshold", 0.5),
            max_concurrency=getattr(knowledge_cfg, "max_concurrency", 5),
        )
        # [预留扩展位终点] 

        # 编译并返回主控状态图
        return build_master_agent_graph(
            intent_recognizer=recognizer,
            recovery_manager=recovery_manager,
            knowledge_engine=knowledge_engine,
            checkpointer=self.checkpointer
        )

    def _build_initial_turn_state(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        构建单轮对话的初始状态载荷：
        显式重置所有单轮临时状态，彻底隔离 Checkpointer 中的历史快照污染。
        """
        return {
            # 1. 身份与链路追踪（每轮刷新 trace_id）
            "session_id": session_id,
            "trace_id": trace_id or f"tr_{uuid.uuid4().hex[:16]}",
            "user_profile": user_profile or {},

            # 2. 增量对话流（由 LangGraph add_messages 自动追加到历史消息列表）
            "messages": [HumanMessage(content=user_message)],

            # 3. 显式清零单轮决策产物（防止上一轮结果污染本轮）
            "intent_result": None,
            "route_decision": None,
            "final_response": None,
            "rag_context": None,
            "window_metrics": None,

            # 4. 显式清零异常与自愈状态（兜底防线）
            "failure_context": None,
            "recovery_outcome": None,
            "is_terminal": False,
        }

    def invoke_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        is_verbose: Optional[bool] = None,
    ) -> dict:
        """同步单轮调用接口"""
        trace_id = trace_id or f"tr_{uuid.uuid4().hex[:16]}"
        config = {"configurable": {"thread_id": session_id}}
        input_payload = self._build_initial_turn_state(
            session_id=session_id,
            user_message=user_message,
            user_profile=user_profile,
            trace_id=trace_id,
        )
        # 绑定当前线程的日志上下文，并在结束时安全重置
        reset = bind_observability_context(
            trace_id=trace_id,
            session_id=session_id,
            is_verbose=is_verbose,
        )
        try:
            return self.graph.invoke(input_payload, config=config)
        finally:
            reset_observability_context(reset)

    async def ainvoke_turn(
        self,
        session_id: str,
        user_message: str,
        user_profile: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        is_verbose: Optional[bool] = None,
    ) -> dict:
        """异步高并发单轮调用接口"""
        trace_id = trace_id or f"tr_{uuid.uuid4().hex[:16]}"
        config = {"configurable": {"thread_id": session_id}}
        input_payload = self._build_initial_turn_state(
            session_id=session_id,
            user_message=user_message,
            user_profile=user_profile,
            trace_id=trace_id,
        )
        # 绑定当前协程的日志上下文（高并发下各请求严格隔离）
        reset = bind_observability_context(
            trace_id=trace_id,
            session_id=session_id,
            is_verbose=is_verbose,
        )
        try:
            return await self.graph.ainvoke(input_payload, config=config)
        finally:
            reset_observability_context(reset)
