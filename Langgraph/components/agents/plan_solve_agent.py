# /components/agents/plan_solve_agent.py
import asyncio
import logging
from typing import AsyncIterator, Dict, List, Set

from protocols import AgentProtocol, PlannerProtocol, AgentResolverProtocol
from schemas import (
    RouteContext,
    RouteDecision,
    AgentResponse,
    AgentStatus,
    AgentStep,
    AgentToken,
    PlanStep,
    ExecutionPlan,
)
from infra import log_execution
from components.agents.registry import AgentPluginCatalog

logger = logging.getLogger(__name__)


@AgentPluginCatalog.register_plugin(
    agent_id="plan_solve_agent",
    description="复杂任务编排（内部调度器，不作为原子节点参与规划）",
    plannable=False,  # 语义自洽：编排器本身不可被再次规划
    default_llm_role="executor",
)
class PlanAndSolveAgent(AgentProtocol):
    """
    Plan-and-Solve 复杂任务编排执行器：
    职责严格收敛为：调用 Planner 获取蓝图 -> 按 DAG 分层并发调度原子 Agent -> 触发 Replan 自愈 -> 流式汇总答复。
    """

    def __init__(
        self,
        planner: PlannerProtocol,
        resolver: AgentResolverProtocol,
        synthesizer_node: str = "general_chat_agent",
        max_replans: int = 2,
    ) -> None:
        self._planner = planner
        self._resolver = resolver
        self._synthesizer_node = synthesizer_node
        self._max_replans = max_replans

    @property
    def agent_id(self) -> str:
        return "plan_solve_agent"

    def _resolve_worker(self, node_id: str) -> AgentProtocol:
        if node_id == self.agent_id:
            raise ValueError(f"Recursive dispatch forbidden: '{node_id}' cannot schedule itself.")
        return self._resolver.get(node_id)

    # 提示：请确保保留你原有的 _execute_single_step 与 _build_synthesis_context 方法
    # 若 _build_synthesis_context 尚未抽离，可参考下方实现：
    def _build_synthesis_context(
        self,
        context: RouteContext,
        plan: ExecutionPlan,
        completed_steps: List[AgentStep],
    ) -> RouteContext:
        observations_block = "\n".join(
            f"- 步骤 {s.step_index} ({s.thought}): {s.observation}"
            for s in completed_steps
        )
        synthesis_prompt = (
            f"【原始用户请求】\n{context.current_input}\n\n"
            f"【总体执行目标】\n{plan.goal}\n\n"
            f"【各子步骤执行结果】\n{observations_block}\n\n"
            "请基于以上所有步骤的执行结果，为用户整理一份完整、连贯、直接的最终答复。"
        )
        return context.model_copy(update={"current_input": synthesis_prompt})

    async def _stream_synthesize_final_answer(
        self,
        context: RouteContext,
        decision: RouteDecision,
        plan: ExecutionPlan,
        completed_steps: List[AgentStep],
    ) -> AsyncIterator[AgentToken | str]:
        """流式汇总最终答复：实时吐出 AgentToken，并在结束时返回完整拼接字符串"""
        synth_context = self._build_synthesis_context(context, plan, completed_steps)
        synthesizer = self._resolve_worker(self._synthesizer_node)

        final_text = ""
        async for item in synthesizer.stream(synth_context, decision):
            if isinstance(item, AgentToken):
                yield item
            elif isinstance(item, AgentResponse):
                final_text = item.final_answer

        yield final_text

    async def _execute_with_stream(
        self, context: RouteContext, decision: RouteDecision
    ) -> AsyncIterator[AgentStep | AgentToken | AgentResponse]:
        """统一核心执行生成器：前置步骤吐出 AgentStep，最终汇总吐出 AgentToken"""
        yield AgentStep(
            step_index=1,
            thought="正在分析复杂任务并制定多步骤执行计划...",
            action="create_plan",
        )
        plan = await self._planner.create_plan(context, decision)
        plan_overview = " -> ".join(
            f"[{s.step_id}:{s.assigned_node}] {s.description}" for s in plan.steps
        )
        yield AgentStep(
            step_index=2,
            thought=f"已生成执行蓝图（共 {len(plan.steps)} 步）",
            action="plan_ready",
            observation=plan_overview,
        )

        completed_steps: List[AgentStep] = []
        replan_attempts = 0
        trace_idx = 2

        # 1. DAG 子步骤调度与动态重规划循环
        while True:
            step_outputs: Dict[int, str] = {}
            done_ids: Set[int] = set()
            pending_steps: Dict[int, PlanStep] = {s.step_id: s for s in plan.steps}
            prior_observations = list(completed_steps)

            try:
                while pending_steps:
                    ready_batch = [
                        step
                        for step in pending_steps.values()
                        if all(dep in done_ids for dep in step.depends_on)
                    ]
                    if not ready_batch:
                        raise RuntimeError("Plan DAG 调度死锁：存在循环依赖或缺失的前置步骤。")

                    batch_results = await asyncio.gather(
                        *(
                            self._execute_single_step(
                                context, decision, plan, step, step_outputs, prior_observations
                            )
                            for step in ready_batch
                        )
                    )

                    for finished_step, resp in batch_results:
                        step_outputs[finished_step.step_id] = resp.final_answer
                        done_ids.add(finished_step.step_id)
                        del pending_steps[finished_step.step_id]

                        trace_idx += 1
                        step_record = AgentStep(
                            step_index=trace_idx,
                            thought=finished_step.description,
                            action=finished_step.assigned_node,
                            action_input={"step_id": finished_step.step_id},
                            observation=resp.final_answer,
                        )
                        completed_steps.append(step_record)
                        yield step_record

                # 所有子步骤均成功完成，跳出重规划循环进入流式汇总
                break

            except Exception as exc:
                if replan_attempts >= self._max_replans:
                    raise
                replan_attempts += 1
                trace_idx += 1
                yield AgentStep(
                    step_index=trace_idx,
                    thought=f"步骤执行受阻（{exc}），正在触发第 {replan_attempts} 次动态重规划...",
                    action="replan",
                )
                plan = await self._planner.replan(
                    context=context,
                    original_plan=plan,
                    completed_steps=completed_steps,
                    error_reason=str(exc),
                )

        # 2. 独立执行最终流式汇总（避免一旦吐出 Token 后因异常触发重规划导致文本重叠）
        final_answer = ""
        async for synth_item in self._stream_synthesize_final_answer(
            context, decision, plan, completed_steps
        ):
            if isinstance(synth_item, AgentToken):
                yield synth_item
            elif isinstance(synth_item, str):
                final_answer = synth_item

        yield AgentResponse(
            status=AgentStatus.COMPLETED,
            final_answer=final_answer,
            steps=completed_steps,
            metadata={
                "goal": plan.goal,
                "total_steps": len(completed_steps),
                "replan_count": replan_attempts,
            },
        )

    @log_execution("PlanAndSolveAgent.run")
    async def run(self, context: RouteContext, decision: RouteDecision) -> AgentResponse:
        final_response: AgentResponse | None = None
        async for item in self._execute_with_stream(context, decision):
            if isinstance(item, AgentResponse):
                final_response = item
        assert final_response is not None
        return final_response

    async def stream(
        self, context: RouteContext, decision: RouteDecision
    ) -> AsyncIterator[AgentStep | AgentToken | AgentResponse]:
        async for item in self._execute_with_stream(context, decision):
            yield item
