# /protocols/governance.py
from typing import Protocol, Dict, Any, runtime_checkable
from schemas.decision import RouteDecision


@runtime_checkable
class HumanApprovalGateProtocol(Protocol):
    """安全风控与人工审批门禁协议（Human-in-the-Loop）"""

    def requires_approval(self, decision: RouteDecision, state: Dict[str, Any]) -> bool:
        """
        判断当前路由决策与参数是否触及高危边界，需要触发 LangGraph interrupt 挂起等待人工确认。
        """
        ...

    async def verify_approval(self, state: Dict[str, Any]) -> bool:
        """
        校验人工唤醒（Command(resume=...)）后回传的审批载荷是否合法且允许放行。
        """
        ...
