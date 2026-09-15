"""converge node.

Reads:  state["frame_instances"], state["candidates"]
Writes: state["frame_instances"] (updated bindings)

What it does:
  - For each frame instance FE with candidates but not yet filled,
    pick the best candidate and bind it.
  - Uses source-based priority from convergence.decision.

Design:
  - Deterministic, no LLM.
  - Does not ask the user.
  - Leaves candidates in state for observability.

Not responsibilities:
  - Candidate generation.
  - Gap detection / question aggregation.
  - User interaction.
"""

from __future__ import annotations

from src.graphs.state import GraphState, append_trace
from src.registry.frame_instance import FrameInstance
from src.convergence.candidate import Candidate
from src.convergence.decision import pick_best


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _candidate_key(frame_id: str, fe_name: str) -> str:
    return f"{frame_id}.{fe_name}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def converge(state: GraphState) -> GraphState:
    """Fill remaining FE bindings by picking the best candidate."""
    instances: list[FrameInstance] = state.get("frame_instances", [])
    candidates: dict[str, list[Candidate]] = state.get("candidates", {})

    filled_count = 0

    for inst in instances:
        for fe_name in list(inst.fe_bindings.keys()):
            binding = inst.get_binding(fe_name)
            if binding is None or binding.status == "filled":
                continue

            key = _candidate_key(inst.frame_id, fe_name)
            cands = candidates.get(key, [])
            if not cands:
                continue

            best = pick_best(cands)
            if best is None:
                continue

            binding.set_value(
                value=best.value,
                source=best.source,
                confidence=best.score if best.score else 1.0,
            )
            filled_count += 1

    append_trace(
        state,
        node="converge",
        phase="convergence",
        summary=f"filled {filled_count} FE binding(s) from candidates",
    )
    return state