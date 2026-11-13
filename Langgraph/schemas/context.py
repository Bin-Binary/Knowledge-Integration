# schemas/context.py
from typing import Optional, List, Dict, Any, Literal
from pydantic import Field
from schemas.base import ImmutableSchema

class Message(ImmutableSchema):
    """标准单轮对话消息体"""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    token_count: Optional[int] = Field(default=None, ge=0, description="缓存单条消息的 Token 长度")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WindowMetrics(ImmutableSchema):
    """滑动窗口运行时度量指标"""
    total_input_tokens: int = Field(..., ge=0)
    w_input_safe: int = Field(..., gt=0)
    overflow_tokens: int = Field(default=0, ge=0)
    evicted_turns: int = Field(default=0, ge=0)
    is_rag_truncated: bool = Field(default=False, description="是否触发了 Level 2 强剪枝")

class RouteContext(ImmutableSchema):
    """路由与执行引擎接收的完整只读上下文"""
    session_id: str = Field(..., min_length=1)
    current_input: str
    safe_history: List[Message] = Field(default_factory=list)
    rag_context: Optional[str] = None
    window_metrics: Optional[WindowMetrics] = None
    session_state: Optional[str] = Field(default=None, description="当前会话状态机节点")
    user_profile: Dict[str, Any] = Field(default_factory=dict)
