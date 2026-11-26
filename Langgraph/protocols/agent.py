# /protocols/agent.py
from typing import Protocol, runtime_checkable, AsyncIterator, List, Any

from schemas import(
    RouteContext,
    RouteDecision,
    AgentResponse, 
    AgentStep,
    AgentToken,
) 

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

    async def run(self, context: RouteContext, decision: RouteDecision) -> AgentResponse:
        """异步执行完整推理循环并返回最终结果"""
        ...

    def stream(
        self, 
        context: RouteContext, 
        decision: RouteDecision
    ) -> AsyncIterator[AgentStep | AgentToken | AgentResponse]:
        """流式吐出每一步的 Thought/Action/Observation，最后吐出 AgentResponse"""
        ...
