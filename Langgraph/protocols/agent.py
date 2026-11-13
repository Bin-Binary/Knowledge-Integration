# /protocols/agent.py
from typing import Protocol, runtime_checkable, AsyncIterator, List, Any

from schemas.context import RouteContext
from schemas.decision import RouteDecision
from schemas.execution import AgentResponse, AgentStep

@runtime_checkable
class AgentProtocol(Protocol):
    """
    通用 Agent 执行器协议：屏蔽底层架构差异（ReAct / Plan-Solve / Reflexion / Workflow）。
    所有被路由调度的目标节点（target_node）都必须实现此协议。
    """
    @property
    def agent_id(self) -> str:
        """节点唯一标识，与 RouteDecision.target_node 严格对应"""
        ...

    def run(self, context: RouteContext, decision: RouteDecision) -> AgentResponse:
        """同步执行完整推理循环并返回最终结果"""
        ...

    async def stream(
        self, 
        context: RouteContext, 
        decision: RouteDecision
    ) -> AsyncIterator[AgentStep | AgentResponse]:
        """流式吐出每一步的 Thought/Action/Observation，最后吐出 AgentResponse"""
        ...


@runtime_checkable
class ToolCapableAgentProtocol(AgentProtocol, Protocol):
    """
    支持动态工具挂载的 Agent 协议（适用于 ReAct 等自主规划架构）。
    允许在运行时根据用户权限或路由决策动态注入可用的工具集。
    """
    def bind_tools(self, tools: List[Any]) -> None:
        ...
