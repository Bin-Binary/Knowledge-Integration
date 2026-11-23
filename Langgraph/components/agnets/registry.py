# /components/agents/registry.py
import importlib
import logging
import pkgutil
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional, Type

from protocols.agent import AgentProtocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentPluginSpec:
    """单个 Agent 插件的元数据规格"""
    agent_id: str
    agent_cls: Type[AgentProtocol]
    description: str
    plannable: bool = True          # 是否允许被 LLMPlanner 拆解指派
    default_llm_role: str = "executor"


class AgentRegistry:
    """
    业务执行器（AgentProtocol）插件注册中心：
    - 类级别维护全局插件目录（_PLUGIN_CATALOG），支持装饰器自注册与包自动扫描；
    - 实例级别维护运行时已激活的 Agent 实例池，供 execution_graph 与 PlanAndSolveAgent 调度。
    """

    _PLUGIN_CATALOG: Dict[str, AgentPluginSpec] = {}
    _discovered: bool = False

    def __init__(self, agents: Optional[Iterable[AgentProtocol]] = None) -> None:
        self._instances: Dict[str, AgentProtocol] = {}
        if agents:
            for agent in agents:
                self.register_instance(agent)

    @classmethod
    def register_plugin(
        cls,
        agent_id: str,
        description: str,
        *,
        plannable: bool = True,
        default_llm_role: str = "executor",
    ) -> Callable[[Type[AgentProtocol]], Type[AgentProtocol]]:
        """
        类装饰器：将具体业务 Agent 注册为可插拔组件。

        示例：
            @AgentRegistry.register_plugin(
                agent_id="general_chat_agent",
                description="擅长常规问答、信息总结与逻辑推理",
            )
            class GeneralChatAgent(AgentProtocol):
                ...
        """
        def decorator(agent_cls: Type[AgentProtocol]) -> Type[AgentProtocol]:
            if agent_id in cls._PLUGIN_CATALOG:
                existing = cls._PLUGIN_CATALOG[agent_id].agent_cls
                if existing is not agent_cls:
                    logger.warning(
                        "[AgentRegistry] Overwriting plugin '%s': %s -> %s",
                        agent_id,
                        existing.__name__,
                        agent_cls.__name__,
                    )
            cls._PLUGIN_CATALOG[agent_id] = AgentPluginSpec(
                agent_id=agent_id,
                agent_cls=agent_cls,
                description=description,
                plannable=plannable,
                default_llm_role=default_llm_role,
            )
            return agent_cls

        return decorator

    @classmethod
    def discover_plugins(cls, package_name: str = "components.agents") -> None:
        """
        自动扫描指定包下的所有模块，触发 @register_plugin 装饰器执行。
        启动期调用一次即可，彻底消灭在 bootstrap 中手动逐个 import 新 Agent 的繁琐操作。
        """
        if cls._discovered:
            return
        try:
            package = importlib.import_module(package_name)
        except ModuleNotFoundError as exc:
            logger.error("[AgentRegistry] Plugin package '%s' not found: %s", package_name, exc)
            return

        pkg_path = getattr(package, "__path__", None)
        if pkg_path:
            for _, mod_name, is_pkg in pkgutil.iter_modules(pkg_path):
                if not is_pkg and not mod_name.startswith("_") and mod_name != "registry":
                    full_name = f"{package_name}.{mod_name}"
                    importlib.import_module(full_name)
                    logger.debug("[AgentRegistry] Discovered plugin module: %s", full_name)

        cls._discovered = True
        logger.info(
            "[AgentRegistry] Plugin discovery completed (%d plugins registered).",
            len(cls._PLUGIN_CATALOG),
        )

    @classmethod
    def get_plugin_catalog(cls) -> Dict[str, AgentPluginSpec]:
        """获取所有已发现的插件规格只读副本"""
        return dict(cls._PLUGIN_CATALOG)

    # ------------------------------------------------------------------
    # 运行时实例管理接口（供 execution_graph 与 PlanAndSolveAgent 调用）
    # ------------------------------------------------------------------

    def register_instance(self, agent: AgentProtocol) -> None:
        if agent.agent_id in self._instances:
            logger.warning("[AgentRegistry] Overwriting runtime instance '%s'", agent.agent_id)
        self._instances[agent.agent_id] = agent

    def get(self, agent_id: str) -> AgentProtocol:
        if agent_id not in self._instances:
            raise KeyError(
                f"Target agent '{agent_id}' is not registered in runtime AgentRegistry. "
                f"Available: {list(self._instances.keys())}"
            )
        return self._instances[agent_id]

    def list_active_ids(self) -> list[str]:
        return list(self._instances.keys())
