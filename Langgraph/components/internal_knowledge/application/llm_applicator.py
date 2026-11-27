# /components/internal_knowledge/application/llm_applicator.py
import asyncio
import inspect
import logging
from typing import Optional
from pydantic import Field

from schemas.base import LLMOutputSchema
from components.internal_knowledge.schemas.pipeline_envelope import PipelineEnvelope
from components.internal_knowledge.schemas.resolve_problem import ResolutionOutcome, ResolveProblem
from protocols.llm import StructuredLLMProtocol
from components.internal_knowledge.protocols import KnowledgeApplicationProtocol, KnowledgeStorageProtocol

logger = logging.getLogger(__name__)


class _SolveEvaluationOutput(LLMOutputSchema):
    """大模型求解与缺口诊断结构化输出"""

    status: str = Field(..., description="评估结论枚举：只能输出 'success'、'partial' 或 'failure'")
    answer: Optional[str] = Field(
        default=None, description="基于检索知识生成的解答（status 为 success 或 partial 时填写）"
    )
    missing_gap: Optional[str] = Field(
        default=None, description="尚未解决的具体知识缺口描述（status 为 partial 或 failure 时必填，用于驱动采集）"
    )


class LLMKnowledgeApplicator(KnowledgeApplicationProtocol):
    """基于结构化大模型的【运用】环节独立实现（零基类继承）"""

    def __init__(
        self,
        llm_client: StructuredLLMProtocol,
        storage: KnowledgeStorageProtocol,
        max_context_chars: int = 12000,
        timeout_seconds: Optional[float] = None,
    ):
        if max_context_chars < 500:
            raise ValueError("max_context_chars 必须 >= 500")
        self.llm = llm_client
        self.storage = storage
        self.max_context_chars = max_context_chars
        self.timeout_seconds = timeout_seconds

    async def resolve(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        current = envelope.problem_resolution
        if not current:
            return envelope

        # 1. 冷启动快速短路：无已召回知识 ID 时直接判定 FAILURE（省一次 LLM 调用）
        if not current.resolutions:
            logger.debug("[LLMKnowledgeApplicator] 无已召回知识 ID，触发冷启动短路 (trace_id=%s)", envelope.trace_id)
            updated = current.model_copy(
                update={"outcome": ResolutionOutcome.FAILURE, "remaining_gap": current.problem}
            )
            return envelope.model_copy(update={"problem_resolution": updated})

        # 2. 水合知识正文，若结果为空同样短路
        knowledge_context = (await self.storage.load_contents(current.resolutions)).strip()
        if not knowledge_context:
            logger.warning(
                "[LLMKnowledgeApplicator] 召回的 %d 条知识 ID 水合正文为空，触发短路 (trace_id=%s)",
                len(current.resolutions),
                envelope.trace_id,
            )
            updated = current.model_copy(
                update={"outcome": ResolutionOutcome.FAILURE, "remaining_gap": current.problem}
            )
            return envelope.model_copy(update={"problem_resolution": updated})

        # 3. 调用大模型进行推理求解与缺口诊断（原生异常直接向上透传给恢复节点）
        bounded_context = knowledge_context[: self.max_context_chars]
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个严谨的知识库求解与缺口诊断专家。请严格基于提供的【已检索知识上下文】回答用户问题。\n"
                    "判断规则：\n"
                    "1. 若上下文足以完整、准确回答问题：status 输出 'success'，在 answer 中给出完整解答。\n"
                    "2. 若上下文只能回答部分问题：status 输出 'partial'，在 answer 中给出已知部分，并在 missing_gap 中明确指出还缺什么具体知识。\n"
                    "3. 若上下文与问题完全无关：status 输出 'failure'，在 missing_gap 中描述需要补充检索的方向。"
                ),
            },
            {
                "role": "user",
                "content": f"### 待解决问题：\n{current.problem}\n\n### 已检索知识上下文：\n{bounded_context}",
            },
        ]

        raw_call = self.llm.generate_structured(
            messages=messages,
            response_schema=_SolveEvaluationOutput,
        )
        coro = raw_call if inspect.isawaitable(raw_call) else asyncio.sleep(0, result=raw_call)
        if self.timeout_seconds is not None:
            res: _SolveEvaluationOutput = await asyncio.wait_for(coro, timeout=self.timeout_seconds)
        else:
            res = await coro

        outcome_map = {
            "success": ResolutionOutcome.SUCCESS,
            "partial": ResolutionOutcome.PARTIAL,
            "failure": ResolutionOutcome.FAILURE,
        }
        outcome = outcome_map.get(res.status.strip().lower(), ResolutionOutcome.FAILURE)

        if outcome == ResolutionOutcome.SUCCESS:
            updated = current.model_copy(
                update={
                    "outcome": ResolutionOutcome.SUCCESS,
                    "resultant_situation": res.answer or "问题已解决",
                    "remaining_gap": None,
                }
            )
        else:
            updated = current.model_copy(
                update={
                    "outcome": outcome,
                    "resultant_situation": res.answer,
                    "remaining_gap": res.missing_gap or current.problem,
                }
            )

        return envelope.model_copy(update={"problem_resolution": updated})
