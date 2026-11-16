# /schemas/api.py
from typing import Any, Dict, Optional
from pydantic import Field
from schemas.base import BoundaryRequestSchema, ImmutableSchema

class ChatTurnRequest(BoundaryRequestSchema):
    """外部调用方传入的标准请求体"""
    session_id: str = Field(..., min_length=1, max_length=128)
    user_message: str = Field(..., min_length=1, max_length=10000)
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatTurnResponse(ImmutableSchema):
    """返回给上游网关的标准化响应体"""
    trace_id: str
    session_id: str
    latency_ms: float
    intent: Optional[Dict[str, Any]] = None
    route_decision: Optional[Dict[str, Any]] = None
    reply: Optional[str] = None
