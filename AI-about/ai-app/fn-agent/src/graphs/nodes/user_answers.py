"""user_answers node.

Reads:  state["user_questions"], state["frame_instances"]
Writes: state["user_answers"], state["frame_instances"]

What it does:
  - Apply simulated answers to the frame instances.
  - The simulation is driven by a lookup table defined at module level.
    In production this would read from user input.

Design:
  - Deterministic simulation for testing.
  - The lookup maps (frame_id, fe_name) -> answer value.
  - Any question without a simulated answer is recorded in
    user_answers as unresolved (None).
"""

from __future__ import annotations

from src.graphs.state import GraphState, Gap, append_trace
from src.registry.frame_instance import FrameInstance


# ---------------------------------------------------------------------------
# Simulated answers
# ---------------------------------------------------------------------------

# Map: (frame_id, fe_name) -> value
SIMULATED_ANSWERS: dict[tuple[str, str], object] = {
    # For F-PROCESSING-MATERIALS-00, no answers needed in the current
    # sample since material is already filled via relations.
    # Add entries here for other FEs when needed for testing.
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def user_answers(state: GraphState) -> GraphState:
    """Apply simulated user answers to frame instances."""
    questions: list[Gap] = state.get("user_questions", [])
    instances: list[FrameInstance] = state.get("frame_instances", [])

    answers: dict[str, object] = {}

    # Build a quick index by frame_id
    inst_by_id: dict[str, FrameInstance] = {i.frame_id: i for i in instances}

    applied = 0
    for q in questions:
        fe = q.get("fe_name")
        frame_id = q.get("frame_id")
        key = (frame_id, fe)

        value = SIMULATED_ANSWERS.get(key)
        answers[f"{frame_id}.{fe}"] = value

        if value is None:
            continue

        inst = inst_by_id.get(frame_id)
        if inst is None:
            continue
        binding = inst.get_binding(fe)
        if binding is None:
            continue
        binding.set_value(value=value, source="explicit", confidence=1.0)
        applied += 1

    state["user_answers"] = answers

    append_trace(
        state,
        node="user_answers",
        phase="gaps",
        summary=f"questions={len(questions)}, applied={applied}, "
                f"unresolved={len(questions) - applied}",
    )
    return state