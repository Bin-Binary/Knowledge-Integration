# /components/planning/llm_planner.py
import json
import logging
from typing import Dict, List

from protocols.components import PlannerProtocol
from protocols.llm import StructuredLLMProtocol
from schemas.context import RouteContext
from schemas.decision import RouteDecision
from schemas.execution import AgentStep
from schemas.plan import ExecutionPlan
from infra.observability import log_execution

logger = logging.getLogger(__name__)


class LLMPlanner(PlannerProtocol):
    """
    基于结构化大模型的任务规划器（实现 PlannerProtocol）：
    1. create_plan: 将复杂目标拆解为带 DAG 依赖关系的原子执行步骤；
    2. replan: 当某一步骤执行失败时，保留已完成步骤的成果，动态调整剩余执行路径。
    """

    def __init__(
        self,
        llm_client: StructuredLLMProtocol,
        available_executors: Dict[str, str],
        default_executor: str = "general_chat_agent",
    ) -> None:
        """
        Args:
            llm_client: 角色为 'planner' 的结构化大模型适配器
            available_executors: 可用原子执行器映射表，如 {"general_chat_agent": "通用问答与文本总结", ...}
            default_executor: 兜底原子执行器 ID
        """
        if not available_executors:
            raise ValueError("LLMPlanner 初始化失败：available_executors 不能为空。")
        self._llm = llm_client
        self._available_executors = available_executors
        self._default_executor = default_executor
        self._schema_guide = ExecutionPlan.to_prompt_guide()

    def _format_executor_catalog(self) -> str:
        return "\n".join(
            f"- `{node_id}`: {desc}" for node_id, desc in self._available_executors.items()
        )

    def _sanitize_plan_nodes(self, plan: ExecutionPlan) -> ExecutionPlan:
        """防御性校验：若模型输出了未注册的 assigned_node，自动收敛至 default_executor"""
        sanitized_steps = []
        changed = False
        for step in plan.steps:
            if step.assigned_node not in self._available_executors:
                logger.warning(
                    "[LLMPlanner] Step %d assigned unknown node '%s', falling back to '%s'",
                    step.step_id,
                    step.assigned_node,
                    self._default_executor,
                )
                sanitized_steps.append(
                    step.model_copy(update={"assigned_node": self._default_executor})
                )
                changed = True
            else:
                sanitized_steps.append(step)

        return plan.model_copy(update={"steps": sanitized_steps}) if changed else plan

    @log_execution("LLMPlanner.create_plan")
    async def create_plan(
        self, context: RouteContext, decision: RouteDecision
    ) -> ExecutionPlan:
        sys_prompt = (
            "你是一个企业级智能体系统的任务规划专家（Task Planner）。\n"
            "请将用户的复杂需求拆解为清晰、可独立执行的原子步骤（DAG 有向无环图）。\n\n"
            f"【可用的原子执行器列表（assigned_node 必须严格从以下标识中选择）】\n"
            f"{self._format_executor_catalog()}\n\n"
            f"【输出数据结构规范】\n{self._schema_guide}\n\n"
            "【规划原则】\n"
            "1. 颗粒度适中：每个步骤只聚焦一个明确的子目标，避免过度碎片化。\n"
            "2. 依赖精准：无前置依赖的步骤 `depends_on` 设为空列表 `[]`；需要前序结果的步骤必须填写对应的 `step_id`。\n"
            "3. 信息透传：在 `expected_output` 中明确写出该步骤应输出的关键信息，方便下游步骤消费。\n"
            "4. 首次规划时 `is_replan` 必须为 `false`，`replan_count` 为 `0`。"
        )

        user_parts = [f"【用户当前目标】\n{context.current_input}"]
        if decision.params:
            user_parts.append(f"【路由提取参数】\n{json.dumps(decision.params, ensure_ascii=False)}")
        if context.rag_context:
            user_parts.append(f"【内部知识库已有背景资料】\n{context.rag_context}")

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ]

        raw_plan = await self._llm.generate_structured(messages, ExecutionPlan)
        return self._sanitize_plan_nodes(raw_plan)

    @log_execution("LLMPlanner.replan")
    async def replan(
        self,
        context: RouteContext,
        original_plan: ExecutionPlan,
        completed_steps: List[AgentStep],
        error_reason: str,
    ) -> ExecutionPlan:
        next_replan_count = original_plan.replan_count + 1

        completed_summary = [
            {
                "step_index": s.step_index,
                "action": s.action,
                "observation": s.observation,
            }
            for s in completed_steps
        ]

        sys_prompt = (
            "你是一个企业级智能体系统的动态重规划专家（Dynamic Replanner）。\n"
            "原计划在执行过程中遭遇了异常或阻塞，请结合【已完成步骤的成果】与【失败原因】，重新制定后续执行计划。\n\n"
            f"【可用的原子执行器列表（assigned_node 必须严格从以下标识中选择）】\n"
            f"{self._format_executor_catalog()}\n\n"
            f"【输出数据结构规范】\n{self._schema_guide}\n\n"
            "【重规划约束】\n"
            "1. 严禁重复规划已经成功完成的步骤，请直接基于已有成果规划剩余必要步骤（若已有信息已足够回答用户，可仅规划 1 个汇总步骤）。\n"
            "2. 针对失败原因调整策略（如更换执行器、简化查询条件或采用降级路径）。\n"
            f"3. 输出中 `is_replan` 必须为 `true`，`replan_count` 必须设为 `{next_replan_count}`。"
        )

        user_content = (
            f"【原始任务目标】\n{original_plan.goal}\n\n"
            f"【原计划步骤】\n{original_plan.model_dump_json(indent=2)}\n\n"
            f"【已成功完成的步骤及观察结果】\n{json.dumps(completed_summary, ensure_ascii=False, indent=2)}\n\n"
            f"【本次执行失败原因】\n{error_reason}"
        )

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_content},
        ]

        raw_replan = await self._llm.generate_structured(messages, ExecutionPlan)
        sanitized = self._sanitize_plan_nodes(raw_replan)
        return sanitized.model_copy(
            update={"is_replan": True, "replan_count": next_replan_count}
        )
