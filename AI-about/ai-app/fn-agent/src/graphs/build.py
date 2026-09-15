"""Graph builder.

Assembles the LangGraph for step A (declarative candidate paths).

Chain:
    START → parse_request → activate_frames
          → resolve_qualia (pass 1)
          → resolve_relations
          → resolve_candidates
          → self_fill
          → resolve_qualia_2 (pass 2)
          → check_gaps
          → aggregate_questions
          → user_answers
          → recheck
          ─┬→ converge → execute → END
           ├→ downgrade_with_notice → END
           ├→ escalate_to_human → END
           └→ END

Usage:
    python -m src.graphs.build
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from src.graphs.state import GraphState, initial_state
from src.graphs.edges import after_recheck

from src.graphs.nodes.parse_request import parse_request
from src.graphs.nodes.activate_frames import activate_frames
from src.graphs.nodes.resolve_qualia import resolve_qualia
from src.graphs.nodes.resolve_relations import resolve_relations
from src.graphs.nodes.resolve_candidates import resolve_candidates
from src.graphs.nodes.self_fill import self_fill
from src.graphs.nodes.check_gaps import check_gaps
from src.graphs.nodes.aggregate_questions import aggregate_questions
from src.graphs.nodes.user_answers import user_answers
from src.graphs.nodes.recheck import recheck
from src.graphs.nodes.converge import converge
from src.graphs.nodes.execute import execute
from src.graphs.nodes.downgrade_with_notice import downgrade_with_notice
from src.graphs.nodes.escalate_to_human import escalate_to_human

from src.loader.loader import load_all
from src.loader.index import build_index
from src.registry.entity_registry import build_entity_registry
from src.registry.unit_registry import build_unit_registry
from src.registry.artifact_registry import build_artifact_registry
from src.providers.candidate_provider import CandidateProvider


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph(provider: CandidateProvider, index):
    """Assemble and return the graph (step A chain)."""
    g = StateGraph(GraphState)

    g.add_node("parse_request",
               lambda s: parse_request(s, provider=provider))
    g.add_node("activate_frames",
               lambda s: activate_frames(s, index=index))
    g.add_node("resolve_qualia",
               lambda s: resolve_qualia(s, index=index, pass_number=1))
    g.add_node("resolve_relations",
               lambda s: resolve_relations(s, index=index))
    g.add_node("resolve_candidates",
               lambda s: resolve_candidates(s, index=index))
    g.add_node("self_fill",
               lambda s: self_fill(s))
    g.add_node("resolve_qualia_2",
               lambda s: resolve_qualia(s, index=index, pass_number=2))
    g.add_node("check_gaps",
               lambda s: check_gaps(s))
    g.add_node("aggregate_questions",
               lambda s: aggregate_questions(s))
    g.add_node("user_answers",
               lambda s: user_answers(s))
    g.add_node("recheck",
               lambda s: recheck(s))
    g.add_node("converge",
               lambda s: converge(s))
    g.add_node("execute",
               lambda s: execute(s))
    g.add_node("downgrade_with_notice",
               lambda s: downgrade_with_notice(s, index=index))
    g.add_node("escalate_to_human",
               lambda s: escalate_to_human(s))

    g.add_edge(START, "parse_request")
    g.add_edge("parse_request", "activate_frames")
    g.add_edge("activate_frames", "resolve_qualia")
    g.add_edge("resolve_qualia", "resolve_relations")
    g.add_edge("resolve_relations", "resolve_candidates")
    g.add_edge("resolve_candidates", "self_fill")
    g.add_edge("self_fill", "resolve_qualia_2")
    g.add_edge("resolve_qualia_2", "check_gaps")
    g.add_edge("check_gaps", "aggregate_questions")
    g.add_edge("aggregate_questions", "user_answers")
    g.add_edge("user_answers", "recheck")

    g.add_conditional_edges(
        "recheck",
        after_recheck,
        {
            "converge": "converge",
            "downgrade_with_notice": "downgrade_with_notice",
            "escalate_to_human": "escalate_to_human",
            "__end__": END,
        },
    )

    g.add_edge("converge", "execute")
    g.add_edge("execute", END)
    g.add_edge("downgrade_with_notice", END)
    g.add_edge("escalate_to_human", END)

    return g.compile()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    bundle = load_all()
    index = build_index(bundle)
    entity_registry = build_entity_registry(bundle)
    unit_registry = build_unit_registry(bundle)
    artifact_registry = build_artifact_registry(bundle)

    provider = CandidateProvider(
        index=index,
        entity_registry=entity_registry,
        unit_registry=unit_registry,
        artifact_registry=artifact_registry,
    )

    graph = build_graph(provider, index)

    state = initial_state(
        request="帮我搭建新版本",
        context={
            "product": "P",
            "version": "entity:Version:V2.3.0",
            "domain": "ci",
        },
    )
    state["entity_registry"] = entity_registry
    state["unit_registry"] = unit_registry
    state["artifact_registry"] = artifact_registry

    print("=== Running graph ===")
    result = graph.invoke(state)

    print()
    print("=== parsed_intent ===")
    parsed = result.get("parsed_intent", {})
    for k in ["action", "purpose", "patient_type", "confidence"]:
        print(f"  {k} = {parsed.get(k)}")

    print()
    print("=== decision ===")
    d = result.get("decision", {})
    print(f"  action       = {d.get('action')}")
    print(f"  reason       = {d.get('reason')}")
    print(f"  hard_missing = {d.get('hard_missing')}")

    plan = result.get("execution_plan")
    if plan:
        print()
        print("=== execution_plan ===")
        print(f"  status  = {plan.get('status')}")
        print(f"  steps   = {len(plan.get('steps', []))}")
        for s in plan.get("steps", []):
            print(f"    {s['order']}. [{s['frame_id']}] {s['fe']} "
                  f"= {s['value']}  (source={s['source']})")

    print()
    print("=== trace ===")
    for t in result.get("trace", []):
        print(f"  [{t['phase']}] {t['node']}: {t['summary']}")


if __name__ == "__main__":
    _main()