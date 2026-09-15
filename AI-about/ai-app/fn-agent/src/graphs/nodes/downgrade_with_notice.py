"""downgrade_with_notice node.

Reads:  state["decision"], state["frame_instances"], state["gaps"]
Writes: state["execution_plan"], state["downgrade_notice"]

What it does:
  - If decision.action == "downgrade", build a best-effort plan:
      * steps = filled required FEs
      * assumptions = default assumptions from each frame's FE default
      * status = "downgraded"
  - Produce a human-readable notice, and set pending_confirmation = true.
  - Does NOT execute. Execution is gated on user confirmation.

Design:
  - No silent execution: any downgrade must be announced.
  - Assumptions are collected from FE definitions in the frame files
    (specifically the FE constraint.default.assumptions).
  - Frames are read via SchemaIndex.

Not responsibilities:
  - Actual execution.
  - Convergence.
"""

from __future__ import annotations

from src.graphs.state import GraphState, append_trace
from src.loader.index import SchemaIndex
from src.registry.frame_instance import FrameInstance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_steps(instances: list[FrameInstance]) -> list[dict]:
    """Collect one step per filled required FE, in frame order."""
    steps: list[dict] = []
    order = 0

    for inst in instances:
        for fe_name in sorted(inst.fe_bindings.keys()):
            binding = inst.get_binding(fe_name)
            if binding is None:
                continue
            if not binding.fe_required:
                continue
            if binding.status != "filled":
                continue

            order += 1
            steps.append({
                "order": order,
                "frame_id": inst.frame_id,
                "fe": fe_name,
                "value": binding.value,
                "source": binding.source,
            })

    return steps


def _collect_assumptions(
    instances: list[FrameInstance],
    index: SchemaIndex,
) -> list[str]:
    """Read default assumptions from the FE definitions of each frame."""
    assumptions: list[str] = []

    for inst in instances:
        frame_content = index.frame_by_id(inst.frame_id)
        if not frame_content:
            continue

        for role_key in ("core_fe", "peripheral_fe"):
            fe_block = frame_content.get(role_key, {}) or {}
            for fe_name, fe_def in fe_block.items():
                if not isinstance(fe_def, dict):
                    continue
                effective = fe_def.get("override", fe_def) if "override" in fe_def else fe_def
                constraint = effective.get("constraint", {}) or {}
                default = constraint.get("default", {}) or {}
                for a in default.get("assumptions", []) or []:
                    assumptions.append(f"[{inst.frame_id}.{fe_name}] {a}")

    return assumptions


def _build_notice(decision: dict, assumptions: list[str]) -> dict:
    hard_missing = decision.get("hard_missing", []) or []
    if hard_missing:
        msg = (
            "以下 required FE 缺失，我将按默认值继续，但不会立即执行，"
            "请确认后再继续：\n" + "\n".join(f"  - {m}" for m in hard_missing)
        )
    else:
        msg = (
            "存在降级条件，我将按默认值继续，但不会立即执行，请确认。"
        )

    return {
        "message": msg,
        "hard_missing": hard_missing,
        "assumptions": assumptions,
        "pending_confirmation": True,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def downgrade_with_notice(
    state: GraphState,
    *,
    index: SchemaIndex,
) -> GraphState:
    """Build a downgraded plan and a user-facing notice."""
    instances: list[FrameInstance] = state.get("frame_instances", [])
    decision = state.get("decision", {})

    steps = _build_steps(instances)
    assumptions = _collect_assumptions(instances, index)
    notice = _build_notice(decision, assumptions)

    state["execution_plan"] = {
        "status": "downgraded",
        "steps": steps,
        "assumptions": assumptions,
        "reason": decision.get("reason", ""),
    }
    state["downgrade_notice"] = notice

    append_trace(
        state,
        node="downgrade_with_notice",
        phase="fallback",
        summary=f"steps={len(steps)}, assumptions={len(assumptions)}, "
                f"pending_confirmation=True",
    )
    return state