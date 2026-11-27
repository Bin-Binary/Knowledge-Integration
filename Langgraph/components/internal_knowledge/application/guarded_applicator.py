# /components/internal_knowledge/application/guarded_applicator.py

import logging
import time

from components.internal_knowledge.schemas.pipeline_envelope import PipelineEnvelope
from components.internal_knowledge.schemas.resolve_problem import ResolveProblem, ResolutionOutcome
from components.internal_knowledge.protocols import KnowledgeApplicationProtocol
from infra import emit_component_status, KnowledgePipelineError

logger = logging.getLogger(__name__)


class GuardedKnowledgeApplicator(KnowledgeApplicationProtocol):
    """【运用】环节组合守卫装饰器（零继承）：
    统一收口前置上下文校验、ResolveProblem 闭环重校验、耗时日志与状态播报。
    支持包裹任意单一求解器或链式组合求解器（避免多层继承导致的重复播报）。
    """

    def __init__(self, inner: KnowledgeApplicationProtocol) -> None:
        self._inner = inner

    async def resolve(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        if not envelope.problem_resolution:
            msg = "运用环节失败：信封中缺失 problem_resolution 上下文"
            logger.warning("[GuardedApplicator] %s (trace_id=%s)", msg, envelope.trace_id)
            raise KnowledgePipelineError(
                message=msg,
                stage="application",
                metadata={"trace_id": envelope.trace_id},
            )

        start_ts = time.perf_counter()
        recalled_count = len(envelope.problem_resolution.resolutions or [])
        logger.info(
            "[GuardedApplicator] 开始问题求解与缺口诊断 (trace_id=%s, recalled_ids=%d)",
            envelope.trace_id,
            recalled_count,
        )
        emit_component_status(
            f"【运用】正结合 {recalled_count} 条参考知识进行推理与缺口诊断...\n",
        )

        # 委托内部求解器执行推理（原生模型/网络异常直接向上透传给恢复节点）
        result_envelope = await self._inner.resolve(envelope)
        if not result_envelope.problem_resolution:
            raise KnowledgePipelineError(
                message="运用环节内部求解器返回了空的 problem_resolution",
                stage="application",
                metadata={"trace_id": envelope.trace_id},
            )

        # 显式重校验：防止内部使用 model_copy(update=...) 时绕过闭环契约校验
        validated_resolution = ResolveProblem.model_validate(
            result_envelope.problem_resolution.model_dump()
        )

        elapsed = time.perf_counter() - start_ts
        if validated_resolution.outcome == ResolutionOutcome.SUCCESS:
            logger.info(
                "[GuardedApplicator] 求解达成闭环 SUCCESS (trace_id=%s, 耗时=%.2fs)",
                envelope.trace_id,
                elapsed,
            )
            emit_component_status(" 【运用】 知识已充分覆盖目标问题，闭环求解达成！\n")
        else:
            gap_preview = (validated_resolution.remaining_gap or "未知知识缺口")[:40]
            logger.info(
                "[GuardedApplicator] 求解未完全闭合 (trace_id=%s, outcome=%s, 耗时=%.2fs, gap='%s')",
                envelope.trace_id,
                validated_resolution.outcome.value,
                elapsed,
                gap_preview,
            )
            emit_component_status(
                f" 【运用】知识缺口（{gap_preview}...），准备触发定向采集...\n",
            )

        return result_envelope.model_copy(
            update={"problem_resolution": validated_resolution}
        )
