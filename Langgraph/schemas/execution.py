# schemas/execution.py
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import Field
from schemas.base import ImmutableSchema

class AgentStatus(str, Enum):
    """Agent 单次运行的终态或中间状态"""
    COMPLETED = "completed"
    NEEDS_INPUT = "needs_input"
    MAX_STEPS_REACHED = "max_steps"
    FAILED = "failed"

class AgentStep(ImmutableSchema):
    """记录 ReAct / Plan-Solve 架构中的单步推理轨迹"""
    step_index: int = Field(..., ge=1)
    thought: Optional[str] = None
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None

class AgentResponse(ImmutableSchema):
    """所有 Agent 架构必须返回的标准化输出契约"""
    status: AgentStatus
    final_answer: str
    steps: List[AgentStep] = Field(default_factory=list)
    updated_state: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
