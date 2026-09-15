"""Runtime view over the entity registry.

Responsibilities:
  - Hold Entity instances loaded from schema/entity/entity-registry-example.json.
  - Support runtime injection of additional entities.
  - Provide lookup by id, type, domain.

Not responsibilities:
  - Validation (loader already did shallow checks).
  - Frame-related logic (belongs to frame_instance.py).
  - Graph state (belongs to graphs/state.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.loader.loader import SchemaBundle, load_all


# ---------------------------------------------------------------------------
# Entity dataclass
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    """A runtime entity instance."""

    id: str
    type: str
    name: str
    qualia: dict[str, Any] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)
    state: str | None = None
    relations: list[dict[str, Any]] = field(default_factory=list)
    domain: str | None = None
    tags: list[str] = field(default_factory=list)

    # -- convenience accessors ------------------------------------------

    def qualia_role(self, role: str) -> Any:
        """Return the qualia value for a given role.

        role ∈ {formal, constitutive, telic, agentive}
        """
        return self.qualia.get(role)

    def relation_targets(self, relation_type: str) -> list[str]:
        """Return targets of a given relation type."""
        return [
            r.get("target")
            for r in self.relations
            if r.get("type") == relation_type
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "qualia": self.qualia,
            "attributes": self.attributes,
            "state": self.state,
            "relations": self.relations,
            "domain": self.domain,
            "tags": self.tags,
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass
class EntityRegistry:
    """A collection of runtime entities."""

    _by_id: dict[str, Entity] = field(default_factory=dict)

    # -- mutation -------------------------------------------------------

    def add(self, entity: Entity) -> None:
        if entity.id in self._by_id:
            raise ValueError(f"Duplicate entity id: {entity.id}")
        self._by_id[entity.id] = entity

    def add_many(self, entities: list[Entity]) -> None:
        for e in entities:
            self.add(e)

    # -- lookup ---------------------------------------------------------

    def get(self, entity_id: str) -> Entity | None:
        return self._by_id.get(entity_id)

    def all(self) -> list[Entity]:
        return list(self._by_id.values())

    def list_by_type(self, entity_type: str) -> list[Entity]:
        return [e for e in self._by_id.values() if e.type == entity_type]

    def list_by_domain(self, domain: str) -> list[Entity]:
        return [e for e in self._by_id.values() if e.domain == domain]

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, entity_id: str) -> bool:
        return entity_id in self._by_id


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _entity_from_dict(data: dict[str, Any]) -> Entity:
    return Entity(
        id=data["id"],
        type=data["type"],
        name=data["name"],
        qualia=data.get("qualia", {}),
        attributes=data.get("attributes", {}),
        state=data.get("state"),
        relations=data.get("relations", []),
        domain=data.get("domain"),
        tags=data.get("tags", []),
    )


def build_entity_registry(
    bundle: SchemaBundle | None = None,
    extra_entities: list[dict[str, Any]] | None = None,
) -> EntityRegistry:
    """Build an EntityRegistry from schema example + optional injection."""
    if bundle is None:
        bundle = load_all()

    registry = EntityRegistry()

    example = bundle.entity.get("entity-registry-example.json", {})
    for raw in example.get("entities", []):
        registry.add(_entity_from_dict(raw))

    if extra_entities:
        for raw in extra_entities:
            registry.add(_entity_from_dict(raw))

    return registry


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    registry = build_entity_registry()

    print(f"Loaded {len(registry)} entities.")
    print()

    print("=== All entities ===")
    for e in registry.all():
        print(f"  {e.id}  [type={e.type}]  name={e.name}")
    print()

    print("=== By type ===")
    for t in ["Version", "Pipeline", "Artifact", "Product", "CodeRepo"]:
        items = registry.list_by_type(t)
        if items:
            print(f"  {t}: {[e.id for e in items]}")
    print()

    print("=== By domain ===")
    for d in ["ci", "general"]:
        items = registry.list_by_domain(d)
        if items:
            print(f"  {d}: {[e.id for e in items]}")
    print()

    print("=== Lookup by id ===")
    sample_id = "entity:Version:V2.3.0"
    e = registry.get(sample_id)
    if e is None:
        print(f"  {sample_id}: NOT FOUND")
    else:
        print(f"  {sample_id}:")
        print(f"    type       = {e.type}")
        print(f"    name       = {e.name}")
        print(f"    formal     = {e.qualia_role('formal')}")
        print(f"    telic      = {e.qualia_role('telic')}")
        print(f"    agentive   = {e.qualia_role('agentive')}")
        print(f"    relations  = {[(r['type'], r['target']) for r in e.relations]}")


if __name__ == "__main__":
    _main()