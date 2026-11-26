# /app/resilience_pipeline.py
from typing import Tuple
from infra.default_exception_specs import DEFAULT_EXCEPTION_SPECS
from infra.registry_exception_mapper import ExceptionMappingSpec

ACTIVE_EXCEPTION_SPECS: Tuple[ExceptionMappingSpec, ...] = (
    *DEFAULT_EXCEPTION_SPECS,
)

RECOVERY_PIPELINE_ORDER: Tuple[str, ...] = (
    "llm_json_repair",     # 1. 处理极少数主备双模型均未能通过 L1 清洗的复杂 JSON 畸形
    "model_degrade",       # 2. 当主备双模型全部不可用时：意图阶段有损降级为默认意图，或返回限流提示
    "user_hint_fallback",  # 3. 处理业务可预期引导话术（如低置信度意图反问澄清、知识库业务提示）
)
