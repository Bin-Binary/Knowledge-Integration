# /components/agents/general_chat_agent.py
import logging
from pydantic import Field
from typing import AsyncIterator, List, Dict

from protocols import AgentProtocol, StructuredLLMProtocol
from schemas import (
    LLMOutputSchema,
    RouteContext,
    RouteDecision,
    AgentResponse,
    AgentStatus,
    AgentStep,
)
from infra import log_execution
# 推荐写法（包内部直接导入，防止日后有人误改 components/agents/__init__.py 引发循环导入）
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
    消费前置节点检索出的 context.rag_context 与对话历史，生成自然语言最终答复。
    """

    def __init__(self, llm_client: StructuredLLMProtocol) -> None:
        self._llm = llm_client

    @property
    def agent_id(self) -> str:
        return "general_chat_agent"

    def _build_messages(self, context: RouteContext, decision: RouteDecision) -> List[Dict[str, str]]:
        sys_parts = [
            "你是一个专业、严谨的智能助手。请直接、清晰地回答用户的问题。",
            f"【输出格式要求】\n{_DirectReplySchema.to_prompt_guide()}",
        ]
        # 如果前置知识库快速检索到了背景资料，自动注入上下文
        if context.rag_context:
            sys_parts.append(
                f"【内部知识库参考资料】\n{context.rag_context}\n"
                "请优先基于上述参考资料回答；若资料未覆盖，可结合通用知识补充，但切勿编造。"
            )

        messages: List[Dict[str, str]] = [{"role": "system", "content": "\n\n".join(sys_parts)}]
        for msg in context.safe_history:
            if msg.role in ("user", "assistant"):
                messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": context.current_input})
        return messages

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
    ) -> AsyncIterator[AgentStep | AgentResponse]:
        yield AgentStep(step_index=1, thought="正在整理思路并检索参考资料...")
        response = await self.run(context, decision)
        yield response
