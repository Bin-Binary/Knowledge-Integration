"""aggregate_questions node.

Reads:  state["gaps"]
Writes: state["user_questions"]

What it does:
  - Take only required hard gaps (required, no value, no candidates).
  - Build one aggregated question per FE.
  - Required pending gaps and peripheral gaps are NOT asked to the user;
    they are handled by convergence or ignored.

Design:
  - The user is asked at most once (one aggregated round).
  - For hard gaps there are no candidates, so the question is open.
"""

from __future__ import annotations

from src.graphs.state import GraphState, Gap, append_trace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _question_for(gap: Gap) -> str:
    """Build a minimal question text for a gap."""
    fe = gap.get("fe_name", "")
    frame_id = gap.get("frame_id", "")
    return f"[{frame_id}] 请提供 FE '{fe}' 的值。"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def aggregate_questions(state: GraphState) -> GraphState:
    """Generate one aggregated question list from required hard gaps."""
    gaps: list[Gap] = state.get("gaps", [])

    hard = [
        g for g in gaps
        if g.get("required") and g.get("reason") == "no value and no candidates"
    ]

    questions: list[Gap] = []
    for g in hard:
        g_copy = dict(g)
        g_copy["question"] = _question_for(g)
        questions.append(g_copy)

    state["user_questions"] = questions

    append_trace(
        state,
        node="aggregate_questions",
        phase="gaps",
        summary=f"generated {len(questions)} question(s) "
                f"from {len(hard)} required hard gap(s)",
    )
    return state