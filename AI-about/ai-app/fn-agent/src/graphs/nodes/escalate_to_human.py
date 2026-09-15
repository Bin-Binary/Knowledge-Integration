"""escalate_to_human node.

Reads:  state["decision"], state["frame_instances"], state["gaps"],
        state["request"], state["context"]
Writes: state["escalation"]

What it does:
  - Bundle the full context into an escalation payload.
  - Set pending_human = true.
  - Does NOT execute.

Design:
  - The bundle is stored in state for downstream systems.
  - CLI prints a summary; full bundle is not printed.

Not responsibilities:
  - Actual human handoff (external system).
  - Plan building (see downgrade_with_notice).
"""

from __future__ import annotations

from src.graphs.state import GraphState, append_trace
from src.registry.frame_instance import FrameInstance


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _frame_summary(inst: FrameInstance) -> dict:
    return {
        "frame_id": inst.frame_id,
        "frame_name": inst.frame_name,
        "domain": inst.domain,
        "saturated": inst.is_saturated(),
        "bindings": {
            name: {
                "status": b.status,
                "value": b.value,
                "source": b.source,
                "required": b.fe_required,
            }
            for name, b in inst.fe_bindings.items()
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def escalate_to_human(state: GraphState) -> GraphState:
    """Bundle context for human escalation."""
    decision = state.get("decision", {})
    instances: list[FrameInstance] = state.get("frame_instances", [])
    gaps = state.get("gaps", [])

    context_bundle = {
        "request": state.get("request", ""),
        "context": state.get("context", {}),
        "decision": decision,
        "frames": [_frame_summary(i) for i in instances],
        "gaps": gaps,
        "hard_missing": decision.get("hard_missing", []),
    }

    state["escalation"] = {
        "status": "escalated",
        "reason": decision.get("reason", ""),
        "context_bundle": context_bundle,
        "pending_human": True,
    }

    append_trace(
        state,
        node="escalate_to_human",
        phase="fallback",
        summary=f"pending_human=True, hard_missing={len(context_bundle['hard_missing'])}",
    )
    return state