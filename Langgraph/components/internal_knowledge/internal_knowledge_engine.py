# /components/internal_knowledge/internal_knowledge_engine.py
import asyncio
import logging
import time
from typing import Optional

from components.internal_knowledge.schemas.pipeline_envelope import PipelineEnvelope
from components.internal_knowledge.schemas.resolve_problem import ResolutionOutcome
from components.internal_knowledge.protocols import (
    InternalKnowledgeEngineProtocol,
    KnowledgeApplicationProtocol,
    KnowledgeAcquisitionProtocol,
    KnowledgeOrganizationProtocol,
    KnowledgeStorageProtocol,
)
from infra.exceptions import KnowledgePipelineError

logger = logging.getLogger(__name__)


class InternalKnowledgeEngine(InternalKnowledgeEngineProtocol):
    """域内知识库闭环总控编排器（支持 P1-2 部分持久化保护 + P2-2 超时语义降级 + 原生异常透传恢复）。"""

    def __init__(
        self,
        storage: KnowledgeStorageProtocol,
        application: KnowledgeApplicationProtocol,
        acquisition: KnowledgeAcquisitionProtocol,
        organization: KnowledgeOrganizationProtocol,
        organize_timeout_seconds: Optional[float] = 150.0,
    ):
        self.storage = storage
        self.application = application
        self.acquisition = acquisition
        self.organization = organization
        self.organize_timeout_seconds = organize_timeout_seconds

    async def fast_retrieve(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        retrieved_env = await self.storage.retrieve(envelope)
        res = retrieved_env.problem_resolution
        if res and res.resolutions and not res.resultant_situation:
            hydrated = await self.storage.load_contents(res.resolutions)
            if hydrated.strip():
                updated_res = res.model_copy(update={"resultant_situation": hydrated})
                return retrieved_env.model_copy(update={"problem_resolution": updated_res})
        return retrieved_env


    async def execute(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """执行完整的域内知识库闭合回路，返回最终状态的 PipelineEnvelope。"""
        if not envelope.problem_resolution:
            raise KnowledgePipelineError(
                message="引擎启动失败：PipelineEnvelope 中缺失初始 problem_resolution",
                stage="engine",
                metadata={"trace_id": envelope.trace_id},
            )

        engine_start = time.perf_counter()
        current_env = envelope

        while True:
            iter_start = time.perf_counter()
            logger.info(
                "[Engine] 开始闭环迭代 (trace_id=%s, iteration=%d/%d)",
                current_env.trace_id,
                current_env.iteration,
                current_env.max_iterations,
            )

            # 1. 【存储.retrieve】检索已有知识填充 resolutions
            current_env = await self.storage.retrieve(current_env)

            # 2. 【运用.resolve】评估求解与缺口诊断
            current_env = await self.application.resolve(current_env)
            resolution = current_env.problem_resolution

            # 3. 闭环终止判定 A：问题已彻底解决
            if resolution and resolution.outcome == ResolutionOutcome.SUCCESS:
                logger.info(
                    "[Engine] 问题已解决，闭环正常终止 (trace_id=%s, 迭代轮次=%d, 总耗时=%.2fs)",
                    current_env.trace_id,
                    current_env.iteration,
                    time.perf_counter() - engine_start,
                )
                return current_env

            # 4. 闭环终止判定 B：已达最大迭代上限，触发 P2-2 语义降级兜底后退出
            if not current_env.can_continue_loop:
                logger.warning(
                    "[Engine] 达到最大迭代次数 (%d)，执行最终语义汇总降级 (trace_id=%s, 总耗时=%.2fs)",
                    current_env.max_iterations,
                    current_env.trace_id,
                    time.perf_counter() - engine_start,
                )
                return await self._semantic_fallback(current_env, reason="达到最大闭环迭代上限")

            # 5. 存在知识缺口且未超限：触发【采集 -> 组织 -> 存储】增量构建闭环
            current_env = await self.acquisition.acquire(current_env)

            # 保护性组织与部分持久化（P1-2）：
            # - 若配置了总阶段超时并触发 asyncio.TimeoutError，保底将已采集的 raw_infos 落盘；
            # - 若为业务降级异常（KnowledgePipelineError）同样保底落盘；
            # - 其他底层模型限流/网络异常（如 RateLimitError）直接向上透传给恢复节点重试。
            try:
                if self.organize_timeout_seconds:
                    current_env = await asyncio.wait_for(
                        self.organization.organize(current_env),
                        timeout=self.organize_timeout_seconds,
                    )
                else:
                    current_env = await self.organization.organize(current_env)
            except (asyncio.TimeoutError, KnowledgePipelineError) as exc:
                logger.warning(
                    "[Engine] 组织环节触发降级保护 (trace_id=%s): %s；继续执行部分持久化。",
                    current_env.trace_id,
                    exc,
                )

            # 只要信封内有任意阶段产物（raw_infos / labels / relations / complexes），立即落盘
            current_env = await self.storage.save(current_env)

            logger.info(
                "[Engine] 本轮增量闭环迭代结束 (trace_id=%s, iteration=%d, 本轮耗时=%.2fs)",
                current_env.trace_id,
                current_env.iteration,
                time.perf_counter() - iter_start,
            )

            # 6. 轮次交接：清空本轮工作区缓冲，iteration + 1
            current_env = current_env.advance_to_next_iteration()

    async def _semantic_fallback(self, envelope: PipelineEnvelope, reason: str) -> PipelineEnvelope:
        """P2-2 语义降级兜底：利用已落盘的 L1/L2 产物进行一次轻量检索与摘要组装"""
        resolution = envelope.problem_resolution
        if not resolution:
            return envelope

        if resolution.resultant_situation:
            return envelope

        recalled_env = await self.storage.retrieve(envelope)
        recalled_res = recalled_env.problem_resolution
        if recalled_res and recalled_res.resolutions:
            snippets = await self.storage.load_contents(recalled_res.resolutions[:3])
            fallback_answer = (
                f"当前闭环因「{reason}」提前收敛，但已从相关数据源提炼并沉淀了 "
                f"{len(recalled_res.resolutions)} 条相关知识节点（ID: {', '.join(recalled_res.resolutions[:5])}）。\n\n"
                f"### 已沉淀核心线索摘要：\n{snippets[:1500]}"
            )
            return recalled_env.model_copy(
                update={
                    "problem_resolution": recalled_res.model_copy(
                        update={
                            "outcome": ResolutionOutcome.PARTIAL,
                            "resultant_situation": fallback_answer,
                        }
                    )
                }
            )

        return envelope
