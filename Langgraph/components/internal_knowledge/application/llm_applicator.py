# /components/internal_knowledge/application/llm_applicator.py
import inspect
from typing import Callable, List, Optional
from pydantic import Field

from schemas.base import LLMOutputSchema
from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope
from schemas.internal_knowledge.resolve_problem import ResolutionOutcome, ResolveProblem
from protocols.llm import StructuredLLMProtocol
from components.internal_knowledge.application.base_application import BaseKnowledgeApplicator
from protocols.internal_knowledge import KnowledgeStorageProtocol

class _SolveEvaluationOutput(LLMOutputSchema):
    """大模型求解与缺口诊断结构化输出"""
    status: str = Field(..., description="评估结论枚举：只能输出 'success'、'partial' 或 'failure'")
    answer: Optional[str] = Field(
        default=None, description="基于检索知识生成的解答（status 为 success 或 partial 时填写）"
    )
    missing_gap: Optional[str] = Field(
        default=None, description="尚未解决的具体知识缺口描述（status 为 partial 或 failure 时必填，用于驱动采集）"
    )


class LLMKnowledgeApplicator(BaseKnowledgeApplicator):
    """基于结构化大模型的【运用】环节具体实现"""

    def __init__(
        self,
        llm_client: StructuredLLMProtocol,
        storage: KnowledgeStorageProtocol,
    ):
        """
        Args:
            llm_client: 结构化输出大模型客户端。
            knowledge_loader: 知识水合加载器，将 resolutions 中的知识 ID 列表转换为可读文本上下文。
        """
        self.llm = llm_client
        self.storage = storage

    async def _evaluate_and_solve(
        self, current: ResolveProblem, envelope: PipelineEnvelope
    ) -> ResolveProblem:
        # 1. 冷启动快速短路：若尚未检索到任何知识 ID，直接判定 FAILURE 并把原问题作为采集缺口（省一次 LLM 调用）
        if not current.resolutions:
            return current.model_copy(
                update={
                    "outcome": ResolutionOutcome.FAILURE,
                    "remaining_gap": current.problem,
                }
            )

        # 2. 直接通过协议接口加载知识全文
        knowledge_context = await self.storage.load_contents(current.resolutions)

        # 3. 调用大模型进行推理求解与缺口诊断
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
                "content": f"### 待解决问题：\n{current.problem}\n\n### 已检索知识上下文：\n{knowledge_context}",
            },
        ]

        raw_call = self.llm.generate_structured(
            messages=messages,
            response_schema=_SolveEvaluationOutput,
        )
        res: _SolveEvaluationOutput = await raw_call if inspect.isawaitable(raw_call) else raw_call

        # 4. 映射为不可变 ResolveProblem 新实例（返回后会自动触发基类的 model_validate 闭环校验）
        outcome_map = {
            "success": ResolutionOutcome.SUCCESS,
            "partial": ResolutionOutcome.PARTIAL,
            "failure": ResolutionOutcome.FAILURE,
        }
        outcome = outcome_map.get(res.status.strip().lower(), ResolutionOutcome.FAILURE)

        if outcome == ResolutionOutcome.SUCCESS:
            return current.model_copy(
                update={
                    "outcome": ResolutionOutcome.SUCCESS,
                    "resultant_situation": res.answer or "问题已解决",
                    "remaining_gap": None,
                }
            )

        return current.model_copy(
            update={
                "outcome": outcome,
                "resultant_situation": res.answer,
                "remaining_gap": res.missing_gap or current.problem,
            }
        )
