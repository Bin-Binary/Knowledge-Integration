"""resolve_relations node.

Reads:  state["frame_instances"], state["candidates"]
Writes: state["candidates"]

What it does:
  - For each frame instance FE with frame_refs in frame-name-index,
    resolve the referenced frame's FE value.
  - Append candidates under key "{frame_id}.{fe_name}".

Note:
  Hardcoded entity-relation rules (previously material from patient.depends_on)
  have been removed in favor of declarative candidate_paths handled by
  resolve_candidates node.

Not responsibilities:
  - Convergence decision.
  - LLM calls.
  - Qualia-based resolution (see resolve_qualia).
  - Declarative candidate paths (see resolve_candidates).
"""

from __future__ import annotations

from src.graphs.state import GraphState, append_trace
from src.loader.index import SchemaIndex
from src.registry.frame_instance import FrameInstance
from src.convergence.candidate import Candidate, SOURCE_FRAME


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _candidate_key(frame_id: str, fe_name: str) -> str:
    return f"{frame_id}.{fe_name}"


def _find_instance_by_name(
    instances: list[FrameInstance],
    frame_name: str,
) -> FrameInstance | None:
    """Find a frame instance whose frame_name matches (case-insensitive)."""
    target = frame_name.lower()
    for inst in instances:
        if inst.frame_name.lower() == target:
            return inst
    return None


def _resolve_frame_refs(
    inst: FrameInstance,
    instances: list[FrameInstance],
    by_refs: dict,
) -> dict[str, list[Candidate]]:
    """Resolve frame_refs-based candidates for one frame instance."""
    out: dict[str, list[Candidate]] = {}

    for fe_name in inst.fe_bindings.keys():
        prefix = f"{inst.frame_id}.{fe_name}.frame_refs"
        matching = {k: v for k, v in by_refs.items() if k.startswith(prefix)}
        if not matching:
            continue

        fe_candidates: list[Candidate] = []
        for _key, spec in matching.items():
            ref_frame_name = spec.get("frame")
            ref_fe_name = spec.get("fe")
            if not ref_frame_name or not ref_fe_name:
                continue

            ref_inst = _find_instance_by_name(instances, ref_frame_name)
            if ref_inst is None:
                continue

            ref_binding = ref_inst.get_binding(ref_fe_name)
            if ref_binding is None or ref_binding.value is None:
                continue

            fe_candidates.append(Candidate(
                value=ref_binding.value,
                source=SOURCE_FRAME,
                metadata={
                    "frame": ref_frame_name,
                    "fe": ref_fe_name,
                    "ref_frame_id": ref_inst.frame_id,
                    "via": "frame_refs",
                },
            ))

        if fe_candidates:
            out[fe_name] = fe_candidates

    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_relations(
    state: GraphState,
    *,
    index: SchemaIndex,
) -> GraphState:
    """Populate candidates from frame_refs entries."""
    instances: list[FrameInstance] = state.get("frame_instances", [])
    candidates: dict[str, list[Candidate]] = state.setdefault("candidates", {})

    index_content = index.bundle.indexes.get("frame-name-index.json", {})
    by_refs = index_content.get("reference_map", {}).get("by_frame_refs", {})

    frame_refs_total = 0

    for inst in instances:
        resolved = _resolve_frame_refs(inst, instances, by_refs)
        for fe_name, cands in resolved.items():
            key = _candidate_key(inst.frame_id, fe_name)
            existing = candidates.get(key, [])
            candidates[key] = existing + cands
            frame_refs_total += len(cands)

    append_trace(
        state,
        node="resolve_relations",
        phase="filling",
        summary=f"frame_refs={frame_refs_total}",
    )
    return state