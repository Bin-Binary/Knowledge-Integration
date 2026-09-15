"""LangGraph state definition.

This module defines the single state object that flows through all nodes.
Every node reads from and writes to this state.

Design notes:
  - Keys are grouped by phase: input → parsing → activation → filling
    → convergence → decision → execution → meta.
  - Values may be None until the phase that fills them runs.
  - State is not validated at runtime; nodes are expected to check.
"""

from __future__ import annotations

from typing import Any, TypedDict

from src.registry.entity_registry import EntityRegistry
from src.registry.unit_registry import UnitRegistry
from src.registry.artifact_registry import ArtifactRegistry
from src.registry.frame_instance import FrameInstance
from src.convergence.candidate import Candidate


# ---------------------------------------------------------------------------
# Auxiliary structures
# ---------------------------------------------------------------------------

class Gap(TypedDict, total=False):
    """A missing piece of information blocking progress."""
    fe_name: str
    frame_id: str
    required: bool
    reason: str
    candidates: list[Candidate]
    question: str


class Trace(TypedDict, total=False):
    """One trace entry; used for audit and debugging."""
    node: str
    phase: str
    timestamp: str
    summary: str
    data: dict[str, Any]


# ---------------------------------------------------------------------------
# GraphState
# ---------------------------------------------------------------------------

class GraphState(TypedDict, total=False):
    """The single state object flowing through the graph."""

    # -- input ----------------------------------------------------------
    request: str
    context: dict[str, Any]

    # -- parsing --------------------------------------------------------
    parsed_intent: dict[str, Any]

    # -- activation -----------------------------------------------------
    frame_instances: list[FrameInstance]

    # -- runtime registries ---------------------------------------------
    entity_registry: EntityRegistry
    unit_registry: UnitRegistry
    artifact_registry: ArtifactRegistry

    # -- filling --------------------------------------------------------
    candidates: dict[str, list[Candidate]]
    gaps: list[Gap]

    # -- user round -----------------------------------------------------
    user_questions: list[Gap]
    user_answers: dict[str, Any]

    # -- fallback -------------------------------------------------------
    downgrade_plan: dict[str, Any]
    downgrade_notice: dict[str, Any]
    escalation: dict[str, Any]

    # -- decision -------------------------------------------------------
    decision: dict[str, Any]

    # -- execution ------------------------------------------------------
    execution_plan: dict[str, Any]

    # -- meta -----------------------------------------------------------
    trace: list[Trace]


# ---------------------------------------------------------------------------
# Helper constructors
# ---------------------------------------------------------------------------

def initial_state(request: str, context: dict[str, Any] | None = None) -> GraphState:
    """Return a minimal state with only input fields populated."""
    return GraphState(
        request=request,
        context=context or {},
        trace=[],
    )


def append_trace(state: GraphState, node: str, phase: str, summary: str,
                 data: dict[str, Any] | None = None) -> None:
    """Append one trace entry."""
    from datetime import datetime, timezone

    entry: Trace = {
        "node": node,
        "phase": phase,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
    }
    if data:
        entry["data"] = data

    state.setdefault("trace", []).append(entry)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    st = initial_state("帮我搭建新版本", {"product": "P", "version": "V"})
    append_trace(st, "init", "input", "state created")

    print("Initial state keys:")
    for k in st.keys():
        print(f"  - {k}")


if __name__ == "__main__":
    _main()