"""parse_request node.

Reads:  state["request"], state["context"]
Writes: state["parsed_intent"]

What it does:
  - Gives the LLM three candidate groups (ActionType / PurposeType / EntityType).
  - Asks the LLM to select one from each group (open-choice).
  - Uses action-based hints to stabilize purpose and patient selection.

Design:
  - Uses the open-choice pattern, not free-form extraction.
  - LLM chooses from R-ROLES-00 role values.
  - Hints are advisory; the LLM may still choose freely.
"""

from __future__ import annotations

from typing import Any

from src.graphs.state import GraphState, append_trace
from src.llm.selectors import select_one
from src.providers.candidate_provider import CandidateProvider


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------

# Advisory mapping from action to likely purpose type.
# These are hints for the LLM, not hard rules.
ACTION_TO_PURPOSE_HINT: dict[str, str] = {
    "build":     "Change（构建产生新版本）",
    "release":   "Change（发布改变版本状态）",
    "rollback":  "Change（回滚改变版本状态）",
    "verify":    "State（验证关注版本状态）",
    "test":      "State（测试关注状态）",
    "deploy":    "Using（部署是使用流水线作用于版本）",
    "configure": "Using（配置是使用工具改变设置）",
    "notify":    "Communication（通知是传递信息）",
}

# Advisory mapping from action to likely patient type.
# These are hints for the LLM, not hard rules.
ACTION_TO_PATIENT_HINT: dict[str, str] = {
    "build":     "Version（构建新版本）",
    "release":   "Version（发布版本）",
    "rollback":  "Version（回滚版本）",
    "verify":    "Version（验证版本状态）",
    "test":      "Version（测试版本）",
    "deploy":    "Version（部署版本）",
    "configure": "ConfigUnit（配置对象通常是配置单元）",
    "notify":    "Version（通知版本相关消息）",
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_request(
    state: GraphState,
    *,
    provider: CandidateProvider,
) -> GraphState:
    """Parse the user request into structured intent.

    Parameters
    ----------
    state : GraphState
        Must contain "request".
    provider : CandidateProvider
        Injected candidate provider.

    Returns
    -------
    GraphState
        Updated state with "parsed_intent".
    """
    request = state.get("request", "")
    context = state.get("context", {})

    base_known: dict[str, Any] = {
        "user_request": request,
        "context": context,
    }

    parsed: dict[str, Any] = {}

    # ---- action (from ActionType) -------------------------------------
    action_candidates = provider.from_role("ActionType")
    action_result = select_one(
        fe_name="action",
        fe_type_ref={"kind": "role", "ref": "ActionType"},
        candidates=action_candidates,
        known=dict(base_known),
    )
    parsed["action"] = action_result.chosen
    parsed["action_confidence"] = action_result.confidence
    parsed["action_basis"] = action_result.basis
    parsed["action_missing"] = action_result.missing

    # ---- purpose (from PurposeType) -----------------------------------
    purpose_known = dict(base_known)
    purpose_known["chosen_action"] = action_result.chosen
    if action_result.chosen and action_result.chosen in ACTION_TO_PURPOSE_HINT:
        purpose_known["hint"] = ACTION_TO_PURPOSE_HINT[action_result.chosen]

    purpose_candidates = provider.from_role("PurposeType")
    purpose_result = select_one(
        fe_name="purpose",
        fe_type_ref={"kind": "role", "ref": "PurposeType"},
        candidates=purpose_candidates,
        known=purpose_known,
    )
    parsed["purpose"] = purpose_result.chosen
    parsed["purpose_confidence"] = purpose_result.confidence
    parsed["purpose_basis"] = purpose_result.basis
    parsed["purpose_missing"] = purpose_result.missing

    # ---- patient_type (from EntityType) -------------------------------
    entity_known = dict(base_known)
    entity_known["chosen_action"] = action_result.chosen
    entity_known["chosen_purpose"] = purpose_result.chosen
    if action_result.chosen and action_result.chosen in ACTION_TO_PATIENT_HINT:
        entity_known["hint"] = ACTION_TO_PATIENT_HINT[action_result.chosen]

    entity_candidates = provider.from_role("EntityType")
    entity_result = select_one(
        fe_name="patient_type",
        fe_type_ref={"kind": "role", "ref": "EntityType"},
        candidates=entity_candidates,
        known=entity_known,
    )
    parsed["patient_type"] = entity_result.chosen
    parsed["patient_confidence"] = entity_result.confidence
    parsed["patient_basis"] = entity_result.basis
    parsed["patient_missing"] = entity_result.missing

    # ---- aggregate missing --------------------------------------------
    missing: list[str] = []
    missing.extend(action_result.missing)
    missing.extend(purpose_result.missing)
    missing.extend(entity_result.missing)
    parsed["missing"] = missing

    # ---- final confidence ---------------------------------------------
    confs = [
        c for c in [
            action_result.confidence,
            purpose_result.confidence,
            entity_result.confidence,
        ] if c > 0
    ]
    parsed["confidence"] = sum(confs) / len(confs) if confs else 0.0

    state["parsed_intent"] = parsed
    append_trace(
        state,
        node="parse_request",
        phase="parsing",
        summary=f"action={parsed['action']} purpose={parsed['purpose']} patient={parsed['patient_type']}",
        data={"confidence": parsed["confidence"], "missing": missing},
    )
    return state