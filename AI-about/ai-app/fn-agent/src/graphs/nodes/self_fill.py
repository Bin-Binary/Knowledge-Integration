"""self_fill node.

Reads:  state["frame_instances"], state["candidates"]
Writes: state["frame_instances"] (updated FE bindings)

What it does:
  - For each frame instance FE that has candidates but is still missing,
    pick the first candidate (default_top1) and bind it.
  - Do not call LLM. Convergence scoring is deferred to converge node.

Source of the bound value is taken from the candidate, not hardcoded.

Not responsibilities:
  - Candidate scoring.
  - LLM calls.
  - Gap detection / question generation.
"""

from __future__ import annotations

from src.graphs.state import GraphState, append_trace
from src.registry.frame_instance import FrameInstance
from src.convergence.candidate import Candidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _candidate_key(frame_id: str, fe_name: str) -> str:
    return f"{frame_id}.{fe_name}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def self_fill(state: GraphState) -> GraphState:
    """Fill FE bindings from candidates (first candidate wins)."""
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

            chosen: Candidate = cands[0]
            binding.set_value(
                value=chosen.value,
                source=chosen.source,
                confidence=1.0,
            )
            filled_count += 1

    append_trace(
        state,
        node="self_fill",
        phase="filling",
        summary=f"filled {filled_count} FE binding(s)",
    )
    return state