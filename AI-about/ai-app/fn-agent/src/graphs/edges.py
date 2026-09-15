"""Edge definitions for the LangGraph.

This module provides the conditional edge function used after `recheck`.
The function routes on decision.action.

Routing:
    proceed_to_convergence -> converge
    downgrade              -> downgrade_with_notice
    escalate               -> escalate_to_human
    block                  -> __end__
    (default)              -> __end__
"""

from __future__ import annotations

from typing import Literal

from src.graphs.state import GraphState


# ---------------------------------------------------------------------------
# Node names (exported for use in build.py)
# ---------------------------------------------------------------------------

PARSE_REQUEST = "parse_request"
ACTIVATE_FRAMES = "activate_frames"
RESOLVE_QUALIA = "resolve_qualia"
RESOLVE_RELATIONS = "resolve_relations"
SELF_FILL = "self_fill"
RESOLVE_QUALIA_2 = "resolve_qualia_2"
CHECK_GAPS = "check_gaps"
AGGREGATE_QUESTIONS = "aggregate_questions"
USER_ANSWERS = "user_answers"
RECHECK = "recheck"
CONVERGE = "converge"
EXECUTE = "execute"
DOWNGRADE_WITH_NOTICE = "downgrade_with_notice"
ESCALATE_TO_HUMAN = "escalate_to_human"


# ---------------------------------------------------------------------------
# Conditional edge after recheck
# ---------------------------------------------------------------------------

def after_recheck(
    state: GraphState,
) -> Literal[
    "converge",
    "downgrade_with_notice",
    "escalate_to_human",
    "__end__",
]:
    """Route based on decision.action."""
    decision = state.get("decision", {})
    action = decision.get("action", "")

    if action in ("proceed_to_convergence", "execute"):
        return "converge"
    if action == "downgrade":
        return "downgrade_with_notice"
    if action == "escalate":
        return "escalate_to_human"
    if action == "block":
        return "__end__"
    return "__end__"