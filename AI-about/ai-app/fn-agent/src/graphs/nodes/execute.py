"""execute node.

Reads:  state["frame_instances"], state["decision"], state["parsed_intent"]
Writes: state["execution_plan"]

What it does:
  - Turn filled frame instances into a linear execution plan.
  - Each step corresponds to a required FE that is filled.
  - Record source and value for each step.

Plan shape:
  {
    "status": "ready" | "blocked" | "downgraded" | "escalated",
    "steps": [
      {"order": 1, "frame_id": "...", "fe": "...", "value": ..., "source": "..."},
      ...
    ],
    "assumptions": [...],
    "reason": "..."
  }

Design:
  - Deterministic, no LLM.
  - Reads the decision.action to determine plan status:
      * proceed_to_convergence -> status = "ready"
      * downgrade             -> status = "downgraded"
      * escalate              -> status = "escalated"
      * block                 -> status = "blocked"
  - Only fills steps for required FEs; peripheral FEs are skipped.

Not responsibilities:
  - Actual execution against external systems.
  - Convergence (already done by converge node).
"""

from __future__ import annotations

from src.graphs.state import GraphState, append_trace
from src.registry.frame_instance import FrameInstance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STATUS_BY_ACTION = {
    "proceed_to_convergence": "ready",
    "execute": "ready",
    "downgrade": "downgraded",
    "escalate": "escalated",
    "block": "blocked",
}


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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def execute(state: GraphState) -> GraphState:
    """Build the execution plan."""
    instances: list[FrameInstance] = state.get("frame_instances", [])
    decision = state.get("decision", {})

    action = decision.get("action", "")
    status = _STATUS_BY_ACTION.get(action, "blocked")

    steps = _build_steps(instances)

    plan = {
        "status": status,
        "steps": steps,
        "assumptions": [],
        "reason": decision.get("reason", ""),
    }

    state["execution_plan"] = plan

    append_trace(
        state,
        node="execute",
        phase="execution",
        summary=f"status={status}, steps={len(steps)}",
    )
    return state