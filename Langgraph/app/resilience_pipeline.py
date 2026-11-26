# /app/resilience_pipeline.py
from typing import Tuple
from infra.default_exception_specs import DEFAULT_EXCEPTION_SPECS
from infra.registry_exception_mapper import ExceptionMappingSpec

ACTIVE_EXCEPTION_SPECS: Tuple[ExceptionMappingSpec, ...] = (
    *DEFAULT_EXCEPTION_SPECS,
)

RECOVERY_PIPELINE_ORDER: Tuple[str, ...] = (
    "llm_json_repair",     # 1. 处理主备双模型均未能通过 L1 清洗的复杂 JSON 畸形
    "user_hint_fallback",  # 2. 统一承接 intent.* / knowledge.* / model.* 的友好引导与降级提示
)
