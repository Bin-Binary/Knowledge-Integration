# protocols/registry.py
from typing import Protocol, runtime_checkable
from protocols.agent import AgentProtocol


@runtime_checkable
class AgentResolverProtocol(Protocol):
    """
    运行时 Agent 解析协议（只读视图）。
    供 execution_graph、PlanAndSolveAgent 等编排调度层使用，彻底隔离注册与扫描细节。
    """

    def get(self, agent_id: str) -> AgentProtocol:
        """根据 agent_id 获取已激活的 Agent 实例，不存在时抛出 KeyError"""
        ...

    def list_active_ids(self) -> list[str]:
        """返回当前所有可用的 agent_id 列表"""
        ...


@runtime_checkable
class AgentRegistrarProtocol(Protocol):
    """
    运行时 Agent 实例注册协议（写入视图）。
    供应用启动期（Bootstrap / DI 容器）装配 Agent 实例时使用。
    """

    def register_instance(self, agent: AgentProtocol) -> None:
        """向运行时池注册一个具体的 Agent 实例"""
        ...
