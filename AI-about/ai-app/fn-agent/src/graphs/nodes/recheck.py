"""recheck node.

Reads:  state["frame_instances"], state["candidates"], state["user_answers"]
Writes: state["decision"]

What it does:
  - Determine whether the system can proceed to convergence.
  - Rules:
      1. All required FEs filled or have candidates
         -> action = "proceed_to_convergence"
      2. Some required FE still hard-missing (no value, no candidates)
         -> action = "downgrade"
      3. Otherwise
         -> action = "escalate"

Design:
  - "proceed_to_convergence" is not "execute".
    It means the graph may move to the convergence stage.
  - "execute" is reserved for the final decision after convergence.
"""

from __future__ import annotations

from src.graphs.state import GraphState, append_trace
from src.registry.frame_instance import FrameInstance


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def recheck(state: GraphState) -> GraphState:
    """Decide next action based on current state."""
    instances: list[FrameInstance] = state.get("frame_instances", [])
    candidates = state.get("candidates", {})

    all_ok = True
    hard_missing: list[str] = []

    for inst in instances:
        for fe_name, binding in inst.fe_bindings.items():
            if not binding.fe_required:
                continue
            key = f"{inst.frame_id}.{fe_name}"
            has_candidates = bool(candidates.get(key))

            if binding.status == "filled":
                continue
            if has_candidates:
                continue

            all_ok = False
            hard_missing.append(key)

    if all_ok:
        action = "proceed_to_convergence"
        reason = "all required FEs either filled or have candidates"
    elif hard_missing:
        action = "downgrade"
        reason = f"hard missing FEs: {hard_missing}"
    else:
        action = "escalate"
        reason = "unreachable in current rules"

    state["decision"] = {
        "action": action,
        "reason": reason,
        "hard_missing": hard_missing,
    }

    append_trace(
        state,
        node="recheck",
        phase="gaps",
        summary=f"action={action}, hard_missing={len(hard_missing)}",
    )
    return state