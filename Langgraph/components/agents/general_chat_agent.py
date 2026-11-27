# /components/agents/general_chat_agent.py
import logging
from pydantic import Field
from typing import AsyncIterator, List, Dict

from protocols import (
    AgentProtocol,
    StructuredLLMProtocol,
    StreamingLLMProtocol,
)
from schemas import (
    LLMOutputSchema,
    RouteContext,
    RouteDecision,
    AgentResponse,
    AgentStatus,
    AgentStep,
    AgentToken,
)
from infra import log_execution
from components.agents.registry import AgentPluginCatalog

logger = logging.getLogger(__name__)


class _DirectReplySchema(LLMOutputSchema):
    """通用对话结构化回复载体"""
    reply: str = Field(..., description="面向用户的最终自然语言回复内容")


@AgentPluginCatalog.register_plugin(
    agent_id="general_chat_agent",
    description="擅长常规问答、信息总结、文本改写、概念解释与逻辑推理",
    plannable=True,
    default_llm_role="executor",
)
class GeneralChatAgent(AgentProtocol):
    """
    通用问答与知识融合 Agent：
    - 非流式模式（run）：强制 JSON 结构化输出，保障接口强类型契约；
    - 流式模式（stream）：直出自然语言 Token 流，实现打字机效果。
    """

    def __init__(self, llm_client: StructuredLLMProtocol) -> None:
        self._llm = llm_client

    @property
    def agent_id(self) -> str:
        return "general_chat_agent"

    def _assemble_chat_messages(
        self, sys_parts: List[str], context: RouteContext
    ) -> List[Dict[str, str]]:
        """公共消息组装：拼接系统提示词、历史对话与当前输入"""
        if context.rag_context:
            sys_parts.append(
                f"【内部知识库参考资料】\n{context.rag_context}\n"
                "请优先基于上述参考资料回答；若资料未覆盖，可结合通用知识补充，但切勿编造。"
            )

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": "\n\n".join(sys_parts)}
        ]
        for msg in context.safe_history:
            if msg.role in ("user", "assistant"):
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": context.current_input})
        return messages

    def _build_messages(
        self, context: RouteContext, decision: RouteDecision
    ) -> List[Dict[str, str]]:
        """非流式专用：附带 JSON Schema 格式要求"""
        _ = decision
        sys_parts = [
            "你是一个专业、严谨的智能助手。请直接、清晰地回答用户的问题。",
            f"【输出格式要求】\n{_DirectReplySchema.to_prompt_guide()}",
        ]
        return self._assemble_chat_messages(sys_parts, context)

    def _build_stream_messages(self, context: RouteContext) -> List[Dict[str, str]]:
        """流式专用：去除 JSON 格式约束，避免把 JSON 外壳暴露给用户"""
        sys_parts = ["你是一个专业、严谨的智能助手。请直接、清晰地回答用户的问题。"]
        return self._assemble_chat_messages(sys_parts, context)

    @log_execution("GeneralChatAgent.run")
    async def run(self, context: RouteContext, decision: RouteDecision) -> AgentResponse:
        messages = self._build_messages(context, decision)
        structured_res = await self._llm.generate_structured(messages, _DirectReplySchema)

        return AgentResponse(
            status=AgentStatus.COMPLETED,
            final_answer=structured_res.reply,
            steps=[
                AgentStep(
                    step_index=1,
                    thought="已融合上下文与知识库检索结果生成最终回复",
                    action="llm_direct_reply",
                )
            ],
            metadata={"used_rag": bool(context.rag_context)},
        )

    async def stream(
        self, context: RouteContext, decision: RouteDecision
    ) -> AsyncIterator[AgentStep | AgentToken | AgentResponse]:
        # 降级兜底：若注入的客户端未实现 StreamingLLMProtocol（如测试 Mock），平滑回退到 run()
        if not isinstance(self._llm, StreamingLLMProtocol):
            resp = await self.run(context, decision)
            yield AgentToken(content=resp.final_answer)
            yield resp
            return

        yield AgentStep(
            step_index=1,
            thought="正在组织语言生成回复...",
            action="llm_stream_reply",
        )
        messages = self._build_stream_messages(context)
        chunks: List[str] = []

        async for token in self._llm.astream_text(messages):
            chunks.append(token)
            yield AgentToken(content=token)

        full_text = "".join(chunks)
        if not full_text.strip():
            raise RuntimeError("Streaming LLM returned empty response.")

        yield AgentResponse(
            status=AgentStatus.COMPLETED,
            final_answer=full_text,
            steps=[
                AgentStep(
                    step_index=1,
                    thought="流式生成完成",
                    action="llm_stream_reply",
                )
            ],
            metadata={"used_rag": bool(context.rag_context), "streamed": True},
        )

