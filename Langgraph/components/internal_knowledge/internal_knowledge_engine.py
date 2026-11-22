# /components/internal_knowledge/engine.py
import logging
from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope
from schemas.internal_knowledge.resolve_problem import ResolutionOutcome
from protocols.internal_knowledge import (
    InternalKnowledgeEngineProtocol,
    KnowledgeApplicationProtocol,
    KnowledgeAcquisitionProtocol,
    KnowledgeOrganizationProtocol,
    KnowledgeStorageProtocol,
)

logger = logging.getLogger(__name__)

class InternalKnowledgeEngine(InternalKnowledgeEngineProtocol):
    """域内知识库闭环总控编排器（具体实现）。

    严格遵循依赖倒置（DIP）：仅依赖四大环节 Protocol，不感知任何具体算法或存储介质。
    """

    def __init__(
        self,
        storage: KnowledgeStorageProtocol,
        application: KnowledgeApplicationProtocol,
        acquisition: KnowledgeAcquisitionProtocol,
        organization: KnowledgeOrganizationProtocol,
    ):
        self.storage = storage
        self.application = application
        self.acquisition = acquisition
        self.organization = organization

    async def execute(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """执行完整的域内知识库闭合回路，返回最终状态的PipelineEnvelope。"""
        if not envelope.problem_resolution:
            raise ValueError("引擎启动失败：PipelineEnvelope中缺失初始 problem_resolution")

        current_env = envelope

        while True:
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
                logger.info("[Engine] 问题已解决，闭环正常终止 (trace_id=%s)", current_env.trace_id)
                return current_env

            # 4. 闭环终止判定 B：已达最大迭代上限，防止知识缺口无法收敛导致死循环
            if not current_env.can_continue_loop:
                logger.warning(
                    "[Engine] 达到最大迭代次数 (%d)，带遗留缺口熔断退出 (trace_id=%s)",
                    current_env.max_iterations,
                    current_env.trace_id,
                )
                return current_env

            # 5. 存在知识缺口且未超限：触发【采集 -> 组织 -> 存储】增量构建闭环
            current_env = await self.acquisition.acquire(current_env)
            current_env = await self.organization.organize(current_env)
            current_env = await self.storage.save(current_env)

            # 6. 轮次交接：清空本轮工作区缓冲，iteration + 1，进入下一轮检索验证
            current_env = current_env.advance_to_next_iteration()
