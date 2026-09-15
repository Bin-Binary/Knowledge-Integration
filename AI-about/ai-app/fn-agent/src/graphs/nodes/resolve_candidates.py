"""resolve_candidates node.

Reads:  state["frame_instances"], state["entity_registry"],
        state["unit_registry"], state["artifact_registry"], state["context"],
        state["candidates"]
Writes: state["candidates"]

What it does:
  - For each frame instance FE, look up frame-name-index.by_candidate_paths.
  - For each registered candidate path, resolve it to a candidate list.
  - Append candidates under key "{frame_id}.{fe_name}".

Four kinds of candidate paths:
  - entity_relation : traverse an entity's relations, filter by target type.
  - unit_field      : read a field from units, optional filter.
  - artifact_field  : read a field from artifacts, optional filter.
  - context_key     : read a value directly from context.

Design:
  - Fully declarative. No hardcoded FE or entity names.
  - Reads only from the schema (frame-name-index) and runtime registries.

Not responsibilities:
  - Scoring.
  - Convergence decision.
  - Hardcoded entity-name rules (those are deprecated).
"""

from __future__ import annotations

from typing import Any

from src.graphs.state import GraphState, append_trace
from src.loader.index import SchemaIndex
from src.registry.entity_registry import EntityRegistry
from src.registry.unit_registry import UnitRegistry
from src.registry.artifact_registry import ArtifactRegistry
from src.registry.frame_instance import FrameInstance
from src.convergence.candidate import Candidate, SOURCE_ENTITY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _candidate_key(frame_id: str, fe_name: str) -> str:
    return f"{frame_id}.{fe_name}"


def _resolve_path(path: str, context: dict[str, Any]) -> Any:
    """Resolve 'context.version' to context['version'].

    Only 'context.*' is supported in the first version.
    """
    parts = path.split(".")
    if not parts or parts[0] != "context":
        return None
    obj: Any = context
    for p in parts[1:]:
        if isinstance(obj, dict):
            obj = obj.get(p)
        else:
            return None
        if obj is None:
            return None
    return obj


def _pick_value(obj: Any, value_field: str) -> Any:
    """Pick a value from an object using value_field.

    value_field:
      - "id"   : obj.id
      - "self" : obj itself
      - other  : obj.<field>
    """
    if value_field == "id":
        return getattr(obj, "id", None)
    if value_field == "self":
        return obj
    return getattr(obj, value_field, None)


def _match_filters(obj: Any, filters: dict[str, Any], context: dict[str, Any]) -> bool:
    """Return True if all filters match obj's attributes.

    Filter value may be:
      - a literal value
      - a string starting with "context." resolved against context
    """
    for key, expected in (filters or {}).items():
        actual = getattr(obj, key, None)
        if isinstance(expected, str) and expected.startswith("context."):
            expected_val = _resolve_path(expected, context)
            if expected_val is None:
                # If the referenced context value is missing, skip this filter.
                continue
            if actual != expected_val:
                return False
        else:
            if actual != expected:
                return False
    return True


# ---------------------------------------------------------------------------
# Kind dispatchers
# ---------------------------------------------------------------------------

def _resolve_entity_relation(
    spec: dict,
    context: dict,
    entity_registry: EntityRegistry,
) -> list[Candidate]:
    from_path = spec.get("from")
    relation = spec.get("relation")
    target_types = spec.get("target_types") or []
    value_field = spec.get("value_field", "id")

    if not from_path or not relation:
        return []

    source_id = _resolve_path(from_path, context)
    if not isinstance(source_id, str) or not source_id:
        return []

    source = entity_registry.get(source_id)
    if source is None:
        return []

    out: list[Candidate] = []
    for target_id in source.relation_targets(relation):
        target = entity_registry.get(target_id)
        if target is None:
            continue
        if target_types and target.type not in target_types:
            continue
        value = _pick_value(target, value_field)
        if value is None:
            continue
        out.append(Candidate(
            value=value,
            source=SOURCE_ENTITY,
            metadata={
                "kind": "entity_relation",
                "from": from_path,
                "relation": relation,
                "target_id": target.id,
            },
        ))
    return out


def _resolve_unit_field(
    spec: dict,
    context: dict,
    unit_registry: UnitRegistry | None,
) -> list[Candidate]:
    if unit_registry is None:
        return []
    field = spec.get("field")
    filters = spec.get("filter") or {}
    if not field:
        return []

    out: list[Candidate] = []
    for u in unit_registry.all():
        if not _match_filters(u, filters, context):
            continue
        raw = getattr(u, field, None)
        if raw is None:
            continue
        values = raw if isinstance(raw, list) else [raw]
        for v in values:
            if v is None:
                continue
            out.append(Candidate(
                value=v,
                source=SOURCE_ENTITY,
                metadata={
                    "kind": "unit_field",
                    "unit_id": u.id,
                    "field": field,
                },
            ))
    return out


def _resolve_artifact_field(
    spec: dict,
    context: dict,
    artifact_registry: ArtifactRegistry | None,
) -> list[Candidate]:
    if artifact_registry is None:
        return []
    field = spec.get("field")
    filters = spec.get("filter") or {}
    if not field:
        return []

    out: list[Candidate] = []
    for a in artifact_registry.all():
        if not _match_filters(a, filters, context):
            continue
        raw = getattr(a, field, None)
        if raw is None:
            continue
        values = raw if isinstance(raw, list) else [raw]
        for v in values:
            if v is None:
                continue
            out.append(Candidate(
                value=v,
                source=SOURCE_ENTITY,
                metadata={
                    "kind": "artifact_field",
                    "artifact_id": a.id,
                    "field": field,
                },
            ))
    return out


def _resolve_context_key(
    spec: dict,
    context: dict,
) -> list[Candidate]:
    key = spec.get("key")
    if not key:
        return []
    v = context.get(key)
    if v is None:
        return []
    values = v if isinstance(v, list) else [v]
    return [
        Candidate(
            value=x,
            source=SOURCE_ENTITY,
            metadata={"kind": "context_key", "key": key},
        )
        for x in values if x is not None
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_candidates(
    state: GraphState,
    *,
    index: SchemaIndex,
) -> GraphState:
    """Populate candidates from candidate_paths entries."""
    instances: list[FrameInstance] = state.get("frame_instances", [])
    entity_registry: EntityRegistry | None = state.get("entity_registry")
    unit_registry: UnitRegistry | None = state.get("unit_registry")
    artifact_registry: ArtifactRegistry | None = state.get("artifact_registry")
    context = state.get("context", {})

    if entity_registry is None:
        append_trace(state, "resolve_candidates", "filling",
                     "skipped: no entity_registry in state")
        return state

    index_content = index.bundle.indexes.get("frame-name-index.json", {})
    by_paths = index_content.get("reference_map", {}).get("by_candidate_paths", {})
    entries = by_paths.get("entries", {})

    candidates = state.setdefault("candidates", {})
    total = 0
    matched_fe = 0

    for inst in instances:
        for fe_name in inst.fe_bindings.keys():
            prefix = f"{inst.frame_id}.{fe_name}.candidate_paths"
            matching = {k: v for k, v in entries.items() if k.startswith(prefix)}
            if not matching:
                continue

            matched_fe += 1
            fe_candidates: list[Candidate] = []

            for _key, spec in matching.items():
                kind = spec.get("kind")
                if kind == "entity_relation":
                    fe_candidates.extend(_resolve_entity_relation(
                        spec, context, entity_registry))
                elif kind == "unit_field":
                    fe_candidates.extend(_resolve_unit_field(
                        spec, context, unit_registry))
                elif kind == "artifact_field":
                    fe_candidates.extend(_resolve_artifact_field(
                        spec, context, artifact_registry))
                elif kind == "context_key":
                    fe_candidates.extend(_resolve_context_key(
                        spec, context))

            if fe_candidates:
                key = _candidate_key(inst.frame_id, fe_name)
                existing = candidates.get(key, [])
                candidates[key] = existing + fe_candidates
                total += len(fe_candidates)

    append_trace(
        state,
        node="resolve_candidates",
        phase="filling",
        summary=f"matched {matched_fe} FE slot(s), generated {total} candidate(s)",
    )
    return state