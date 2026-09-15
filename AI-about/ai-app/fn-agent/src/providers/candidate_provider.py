"""Candidate provider.

Generates Candidate lists from schema sources and runtime registries.

Sources:
  1. Role value domains (R-ROLES-00).
  2. Entity instances by type (EntityRegistry).
  3. Unit instances (UnitRegistry).
  4. Artifact instances (ArtifactRegistry).
  5. System queries (placeholder).
  6. Entity / Unit / Artifact qualia derivation.

Not responsibilities:
  - Scoring.
  - Filtering by permission / state.
  - Convergence decision.
"""

from __future__ import annotations

from typing import Any

from src.loader.index import SchemaIndex
from src.registry.entity_registry import EntityRegistry
from src.registry.unit_registry import UnitRegistry
from src.registry.artifact_registry import ArtifactRegistry
from src.convergence.candidate import (
    Candidate,
    SOURCE_ROLE,
    SOURCE_ENTITY,
    SOURCE_QUERY,
    SOURCE_QUALIA,
)


# ---------------------------------------------------------------------------
# CandidateProvider
# ---------------------------------------------------------------------------

class CandidateProvider:
    """Generate candidates from schema and runtime data."""

    def __init__(
        self,
        index: SchemaIndex,
        entity_registry: EntityRegistry,
        unit_registry: UnitRegistry | None = None,
        artifact_registry: ArtifactRegistry | None = None,
    ) -> None:
        self.index = index
        self.entity_registry = entity_registry
        self.unit_registry = unit_registry
        self.artifact_registry = artifact_registry

    # -- 1. Role value domain -------------------------------------------

    def from_role(self, role_id: str) -> list[Candidate]:
        role = self.index.role(role_id)
        if role is None:
            return []
        candidates: list[Candidate] = []
        for v in role.get("values", []):
            value = v.get("value")
            if value is None:
                continue
            candidates.append(Candidate(
                value=value,
                source=SOURCE_ROLE,
                metadata={
                    "role_id": role_id,
                    "frame": v.get("frame"),
                    "domain": v.get("domain"),
                    "note": v.get("note", ""),
                },
            ))
        return candidates

    # -- 2. Entity instances by type ------------------------------------

    def from_entity_type(self, entity_type: str) -> list[Candidate]:
        entities = self.entity_registry.list_by_type(entity_type)
        candidates: list[Candidate] = []
        for e in entities:
            candidates.append(Candidate(
                value=e.id,
                source=SOURCE_ENTITY,
                metadata={
                    "entity_type": entity_type,
                    "entity": e.to_dict(),
                },
            ))
        return candidates

    # -- 3. Unit instances ----------------------------------------------

    def from_unit(self, unit_id: str) -> list[Candidate]:
        """One candidate for a specific unit id."""
        if self.unit_registry is None:
            return []
        u = self.unit_registry.get(unit_id)
        if u is None:
            return []
        return [Candidate(
            value=u.id,
            source=SOURCE_ENTITY,
            metadata={"unit": u.to_dict(), "via": "unit_id"},
        )]

    def from_unit_env(self, env: str) -> list[Candidate]:
        """Candidates from all units in a given environment."""
        if self.unit_registry is None:
            return []
        units = self.unit_registry.list_by_env(env)
        return [
            Candidate(
                value=u.id,
                source=SOURCE_ENTITY,
                metadata={"unit": u.to_dict(), "via": "unit_env"},
            )
            for u in units
        ]

    def from_unit_field(self, field: str) -> list[Candidate]:
        """Candidates from a specific field of all units.

        Supported fields: code_repo_refs, script_repo_ref, script_refs,
        dependencies.
        """
        if self.unit_registry is None:
            return []
        out: list[Candidate] = []
        for u in self.unit_registry.all():
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
                    metadata={"unit_id": u.id, "field": field},
                ))
        return out

    # -- 4. Artifact instances ------------------------------------------

    def from_artifact(self, artifact_id: str) -> list[Candidate]:
        if self.artifact_registry is None:
            return []
        a = self.artifact_registry.get(artifact_id)
        if a is None:
            return []
        return [Candidate(
            value=a.id,
            source=SOURCE_ENTITY,
            metadata={"artifact": a.to_dict(), "via": "artifact_id"},
        )]

    def from_artifact_belongs_to(self, entity_id: str) -> list[Candidate]:
        """Candidates for all artifacts belonging to an entity."""
        if self.artifact_registry is None:
            return []
        artifacts = self.artifact_registry.list_by_belongs_to(entity_id)
        return [
            Candidate(
                value=a.id,
                source=SOURCE_ENTITY,
                metadata={"artifact": a.to_dict(), "via": "belongs_to"},
            )
            for a in artifacts
        ]

    def from_artifact_field(self, field: str) -> list[Candidate]:
        """Candidates from a specific field of all artifacts.

        Supported fields: storage, checksum, files.
        """
        if self.artifact_registry is None:
            return []
        out: list[Candidate] = []
        for a in self.artifact_registry.all():
            raw = getattr(a, field, None)
            if raw is None:
                continue
            if field == "files":
                for f in raw:
                    if isinstance(f, dict) and "path" in f:
                        out.append(Candidate(
                            value=f["path"],
                            source=SOURCE_ENTITY,
                            metadata={"artifact_id": a.id, "field": "files.path"},
                        ))
                continue
            values = raw if isinstance(raw, list) else [raw]
            for v in values:
                if v is None:
                    continue
                out.append(Candidate(
                    value=v,
                    source=SOURCE_ENTITY,
                    metadata={"artifact_id": a.id, "field": field},
                ))
        return out

    # -- 5. System queries ----------------------------------------------

    def from_query(self, query_id: str) -> list[Candidate]:
        """Placeholder; runtime values are not wired yet."""
        _ = self.index.query(query_id)
        return []

    # -- 6. Qualia derivation -------------------------------------------

    def from_qualia(self, entity_id: str, qualia_role: str) -> list[Candidate]:
        entity = self.entity_registry.get(entity_id)
        if entity is None:
            return []
        raw = entity.qualia_role(qualia_role)
        if raw is None:
            return []
        values = raw if isinstance(raw, list) else [raw]
        return [
            Candidate(
                value=v,
                source=SOURCE_QUALIA,
                metadata={
                    "entity_id": entity_id,
                    "qualia_role": qualia_role,
                },
            )
            for v in values
        ]

    def from_unit_qualia(self, unit_id: str, qualia_role: str) -> list[Candidate]:
        if self.unit_registry is None:
            return []
        u = self.unit_registry.get(unit_id)
        if u is None:
            return []
        raw = u.qualia_role(qualia_role)
        if raw is None:
            return []
        values = raw if isinstance(raw, list) else [raw]
        return [
            Candidate(
                value=v,
                source=SOURCE_QUALIA,
                metadata={
                    "unit_id": unit_id,
                    "qualia_role": qualia_role,
                },
            )
            for v in values
        ]

    def from_artifact_qualia(self, artifact_id: str, qualia_role: str) -> list[Candidate]:
        if self.artifact_registry is None:
            return []
        a = self.artifact_registry.get(artifact_id)
        if a is None:
            return []
        raw = a.qualia_role(qualia_role)
        if raw is None:
            return []
        values = raw if isinstance(raw, list) else [raw]
        return [
            Candidate(
                value=v,
                source=SOURCE_QUALIA,
                metadata={
                    "artifact_id": artifact_id,
                    "qualia_role": qualia_role,
                },
            )
            for v in values
        ]

    # -- Utility: aggregate ---------------------------------------------

    def aggregate(
        self,
        role_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        qualia_role: str | None = None,
    ) -> list[Candidate]:
        result: list[Candidate] = []
        if role_id:
            result.extend(self.from_role(role_id))
        if entity_type:
            result.extend(self.from_entity_type(entity_type))
        if entity_id and qualia_role:
            result.extend(self.from_qualia(entity_id, qualia_role))
        return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    from src.loader.loader import load_all
    from src.loader.index import build_index
    from src.registry.entity_registry import build_entity_registry
    from src.registry.unit_registry import build_unit_registry
    from src.registry.artifact_registry import build_artifact_registry

    bundle = load_all()
    index = build_index(bundle)
    registry = build_entity_registry(bundle)
    unit_registry = build_unit_registry(bundle)
    artifact_registry = build_artifact_registry(bundle)

    provider = CandidateProvider(
        index=index,
        entity_registry=registry,
        unit_registry=unit_registry,
        artifact_registry=artifact_registry,
    )

    print("=== from_role('ActionType') ===")
    print(f"  {len(provider.from_role('ActionType'))} candidates")

    print()
    print("=== from_unit_env('staging') ===")
    for c in provider.from_unit_env("staging"):
        print(f"  {c.value}")

    print()
    print("=== from_unit_field('code_repo_refs') ===")
    for c in provider.from_unit_field("code_repo_refs"):
        print(f"  {c.value}  (unit={c.metadata.get('unit_id')})")

    print()
    print("=== from_artifact_belongs_to('entity:Version:V2.3.0') ===")
    for c in provider.from_artifact_belongs_to("entity:Version:V2.3.0"):
        print(f"  {c.value}")

    print()
    print("=== from_artifact_field('files') ===")
    for c in provider.from_artifact_field("files"):
        print(f"  {c.value}  (artifact={c.metadata.get('artifact_id')})")


if __name__ == "__main__":
    _main()