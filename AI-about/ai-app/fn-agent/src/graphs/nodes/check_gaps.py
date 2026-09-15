"""check_gaps node.

Reads:  state["frame_instances"], state["candidates"]
Writes: state["gaps"]

What it does:
  - Scan all frame instances.
  - Classify each non-filled FE into one of:
      * required hard gap  : required FE, no value, no candidates
      * required pending   : required FE, has candidates, not yet filled
      * peripheral gap     : peripheral FE, no value, no candidates
                             (recorded for audit, not asked to user)

Design:
  - Only required hard gaps drive user questions.
  - Peripheral gaps are kept for observability.
"""

from __future__ import annotations

from src.graphs.state import GraphState, Gap, append_trace
from src.registry.frame_instance import FrameInstance


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_gaps(state: GraphState) -> GraphState:
    """Collect gaps from all frame instances."""
    instances: list[FrameInstance] = state.get("frame_instances", [])
    candidates = state.get("candidates", {})

    gaps: list[Gap] = []

    for inst in instances:
        for fe_name, binding in inst.fe_bindings.items():
            if binding.status == "filled":
                continue

            key = f"{inst.frame_id}.{fe_name}"
            has_candidates = bool(candidates.get(key))

            if binding.fe_required:
                if binding.status == "missing" and not has_candidates:
                    gaps.append({
                        "fe_name": fe_name,
                        "frame_id": inst.frame_id,
                        "required": True,
                        "reason": "no value and no candidates",
                        "candidates": [],
                        "question": "",
                    })
                else:
                    gaps.append({
                        "fe_name": fe_name,
                        "frame_id": inst.frame_id,
                        "required": True,
                        "reason": "candidates available, not yet filled",
                        "candidates": candidates.get(key, []),
                        "question": "",
                    })
            else:
                # peripheral
                if binding.status == "missing" and not has_candidates:
                    gaps.append({
                        "fe_name": fe_name,
                        "frame_id": inst.frame_id,
                        "required": False,
                        "reason": "peripheral missing",
                        "candidates": [],
                        "question": "",
                    })

    state["gaps"] = gaps

    required_hard = [
        g for g in gaps
        if g.get("required") and g.get("reason") == "no value and no candidates"
    ]
    required_pending = [
        g for g in gaps
        if g.get("required") and g.get("reason") == "candidates available, not yet filled"
    ]
    peripheral = [
        g for g in gaps if not g.get("required")
    ]

    append_trace(
        state,
        node="check_gaps",
        phase="gaps",
        summary=f"required_hard={len(required_hard)}, "
                f"required_pending={len(required_pending)}, "
                f"peripheral={len(peripheral)}",
    )
    return state