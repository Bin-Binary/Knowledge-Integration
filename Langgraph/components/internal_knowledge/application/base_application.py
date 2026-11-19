# /components/internal_knowledge/application/base_application.py
from abc import ABC, abstractmethod

from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope
from schemas.internal_knowledge.resolve_problem import ResolveProblem
from protocols.internal_knowledge import KnowledgeApplicationProtocol

class BaseKnowledgeApplicator(ABC, KnowledgeApplicationProtocol):
    """1. 【运用】环节抽象基类（实现 KnowledgeApplicationProtocol）。

    核心职能：
        1. 校验输入信封的求解上下文（problem_resolution）完整性。
        2. 委托子类执行基于检索知识（resolutions）的异步推理求解与缺口诊断。
        3. 强制触发 Pydantic 闭环约束校验，不可变地回写更新后的 ResolveProblem 状态。
    """

    async def resolve(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """统一异步求解入口：前置状态校验 -> 执行推理求解 -> 契约校验 -> 不可变更新信封"""
        if not envelope.problem_resolution:
            raise ValueError("运用环节失败：信封中缺失 problem_resolution 上下文")

        updated_resolution = await self._evaluate_and_solve(
            envelope.problem_resolution, envelope
        )

        # 显式重校验：防止子类使用 model_copy(update=...) 时绕过 validate_closed_loop 校验
        validated_resolution = ResolveProblem.model_validate(
            updated_resolution.model_dump()
        )

        return envelope.model_copy(
            update={"problem_resolution": validated_resolution}
        )

    @abstractmethod
    async def _evaluate_and_solve(
        self, current: ResolveProblem, envelope: PipelineEnvelope
    ) -> ResolveProblem:
        """子类必须实现的核心异步求解逻辑：
        根据 current.problem 与已召回的 current.resolutions 进行评估：
        - 彻底解决：返回 outcome=SUCCESS 且包含 resultant_situation 的新实例。
        - 未完全解决：返回 outcome=PARTIAL/FAILURE 且包含 remaining_gap 的新实例。
        """
        ...
