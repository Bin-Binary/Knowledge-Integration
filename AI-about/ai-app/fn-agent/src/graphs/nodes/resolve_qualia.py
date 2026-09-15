"""resolve_qualia node.

Reads:  state["frame_instances"], state["entity_registry"], state["context"]
Writes: state["candidates"]

What it does:
  - For each (frame_instance, FE), look up frame-name-index.by_qualia_paths.
  - If an entry exists, resolve it to a candidate list.
  - Store candidates under key "{frame_id}.{fe_name}".

Qualia path kinds:
  - placeholder : "{entity}"      -> context patient/version entity
                  "{material}"    -> value of 'material' FE in same frame
                  "{instrument}"  -> value of 'instrument' FE in same frame
  - entity      : "ConfigUnit.qualia.telic" etc.
                  Resolved from entity_registry by type.
  - fe_source   : "chosen.qualia.telic" etc.
                  Resolved from another FE in the same frame instance.

Note:
  When a placeholder references {material} / {instrument} whose FE has not
  been filled yet, the resolver returns an empty list. A second pass after
  self_fill will populate those.

Not responsibilities:
  - Convergence decision.
  - LLM calls.
  - Relation-based resolution (see resolve_relations).
"""

from __future__ import annotations

from typing import Any

from src.graphs.state import GraphState, append_trace
from src.loader.index import SchemaIndex
from src.registry.entity_registry import EntityRegistry
from src.registry.frame_instance import FrameInstance
from src.convergence.candidate import Candidate, SOURCE_QUALIA


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _candidate_key(frame_id: str, fe_name: str) -> str:
    return f"{frame_id}.{fe_name}"


def _context_entity_types(context: dict[str, Any]) -> dict[str, str]:
    """Extract {type: entity_id} hints from context."""
    hints: dict[str, str] = {}
    for key, etype in [
        ("patient", "Version"),
        ("version", "Version"),
        ("product", "Product"),
        ("code_repo", "CodeRepo"),
        ("repo", "CodeRepo"),
        ("config_unit", "ConfigUnit"),
        ("unit", "ConfigUnit"),
    ]:
        v = context.get(key)
        if isinstance(v, str) and v:
            hints[etype] = v
    return hints


def _values_from_qualia(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    return [raw]


def _resolve_placeholder(
    target: str,
    qualia_role: str,
    frame_instance: FrameInstance,
    context: dict[str, Any],
    registry: EntityRegistry,
) -> list[Candidate]:
    """Resolve a placeholder path.

    The raw target is expected to be wrapped in braces, e.g. "{entity}".
    We strip the braces before dispatching.

    Supported placeholders:
      {entity}     : entity from context patient/version
      {material}   : value of 'material' FE in the same frame instance
      {instrument} : value of 'instrument' FE in the same frame instance
    """
    # Normalize: "{material}" -> "material"
    target_key = target.strip("{}")

    candidates: list[Candidate] = []

    # --- {entity}: from context ---
    if target_key == "entity":
        ctx_types = _context_entity_types(context)
        for etype, eid in ctx_types.items():
            entity = registry.get(eid)
            if entity is None:
                continue
            raw = entity.qualia_role(qualia_role)
            for v in _values_from_qualia(raw):
                candidates.append(Candidate(
                    value=v,
                    source=SOURCE_QUALIA,
                    metadata={
                        "entity_id": eid,
                        "entity_type": etype,
                        "qualia_role": qualia_role,
                        "placeholder": target,
                    },
                ))
        return candidates

    # --- {material} / {instrument}: from frame instance FE ---
    if target_key in ("material", "instrument"):
        binding = frame_instance.get_binding(target_key)
        if binding is None or binding.value is None:
            return []
        raw_val = binding.value
        eids = raw_val if isinstance(raw_val, list) else [raw_val]
        for eid in eids:
            if not isinstance(eid, str):
                continue
            entity = registry.get(eid)
            if entity is None:
                continue
            role_val = entity.qualia_role(qualia_role)
            for v in _values_from_qualia(role_val):
                candidates.append(Candidate(
                    value=v,
                    source=SOURCE_QUALIA,
                    metadata={
                        "entity_id": eid,
                        "qualia_role": qualia_role,
                        "placeholder": target,
                    },
                ))
        return candidates

    return []


def _resolve_entity(
    entity_type: str,
    qualia_role: str,
    registry: EntityRegistry,
) -> list[Candidate]:
    """Resolve a path like ConfigUnit.qualia.telic."""
    candidates: list[Candidate] = []
    for entity in registry.list_by_type(entity_type):
        raw = entity.qualia_role(qualia_role)
        for v in _values_from_qualia(raw):
            candidates.append(Candidate(
                value=v,
                source=SOURCE_QUALIA,
                metadata={
                    "entity_id": entity.id,
                    "entity_type": entity_type,
                    "qualia_role": qualia_role,
                },
            ))
    return candidates


def _resolve_fe_source(
    fe_source: str,
    qualia_role: str,
    frame_instance: FrameInstance,
    registry: EntityRegistry,
) -> list[Candidate]:
    """Resolve a path like chosen.qualia.telic.

    fe_source must be a binding in the same frame instance whose value
    is an entity id or a list of entity ids.
    """
    binding = frame_instance.get_binding(fe_source)
    if binding is None or binding.value is None:
        return []

    candidates: list[Candidate] = []
    raw = binding.value
    eids = raw if isinstance(raw, list) else [raw]
    for eid in eids:
        if not isinstance(eid, str):
            continue
        entity = registry.get(eid)
        if entity is None:
            continue
        role_val = entity.qualia_role(qualia_role)
        for v in _values_from_qualia(role_val):
            candidates.append(Candidate(
                value=v,
                source=SOURCE_QUALIA,
                metadata={
                    "entity_id": eid,
                    "qualia_role": qualia_role,
                    "fe_source": fe_source,
                },
            ))
    return candidates


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_qualia(
    state: GraphState,
    *,
    index: SchemaIndex,
    pass_number: int = 1,
) -> GraphState:
    """Populate candidates from qualia_paths entries.

    Parameters
    ----------
    state : GraphState
    index : SchemaIndex
    pass_number : int
        1 for the first pass, 2 for the second pass.
        Recorded in trace for debugging.
    """
    instances: list[FrameInstance] = state.get("frame_instances", [])
    registry: EntityRegistry | None = state.get("entity_registry")
    context = state.get("context", {})

    if registry is None:
        append_trace(state, "resolve_qualia", "filling",
                     f"pass={pass_number} skipped: no entity_registry in state")
        return state

    index_content = index.bundle.indexes.get("frame-name-index.json", {})
    by_qualia = index_content.get("reference_map", {}).get("by_qualia_paths", {})
    entries = by_qualia.get("entries", {})

    candidates = state.setdefault("candidates", {})
    total = 0
    matched_fe = 0

    for inst in instances:
        for fe_name in inst.fe_bindings.keys():
            prefix = f"{inst.frame_id}.{fe_name}.qualia_paths"
            matching = {k: v for k, v in entries.items() if k.startswith(prefix)}
            if not matching:
                continue

            matched_fe += 1
            fe_candidates: list[Candidate] = []
            for _key, spec in matching.items():
                qualia_role = spec.get("qualia")
                if not qualia_role:
                    continue

                if "placeholder" in spec:
                    fe_candidates.extend(_resolve_placeholder(
                        target=spec["placeholder"],
                        qualia_role=qualia_role,
                        frame_instance=inst,
                        context=context,
                        registry=registry,
                    ))
                elif "entity" in spec:
                    fe_candidates.extend(_resolve_entity(
                        entity_type=spec["entity"],
                        qualia_role=qualia_role,
                        registry=registry,
                    ))
                elif "fe_source" in spec:
                    fe_candidates.extend(_resolve_fe_source(
                        fe_source=spec["fe_source"],
                        qualia_role=qualia_role,
                        frame_instance=inst,
                        registry=registry,
                    ))

            if fe_candidates:
                key = _candidate_key(inst.frame_id, fe_name)
                existing = candidates.get(key, [])
                candidates[key] = existing + fe_candidates
                total += len(fe_candidates)

    append_trace(
        state,
        node="resolve_qualia",
        phase="filling",
        summary=f"pass={pass_number} matched {matched_fe} FE slot(s), "
                f"generated {total} candidate(s)",
    )
    return state