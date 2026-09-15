"""Runtime view over the unit registry.

Responsibilities:
  - Hold Unit instances loaded from schema/unit/unit-registry-example.json.
  - Support runtime injection of additional units.
  - Provide lookup by id, env, state, domain.

Not responsibilities:
  - Validation.
  - Frame-related logic.
  - Graph state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.loader.loader import SchemaBundle, load_all


# ---------------------------------------------------------------------------
# Unit dataclass
# ---------------------------------------------------------------------------

@dataclass
class Unit:
    """A runtime unit instance."""

    id: str
    type: str
    name: str
    qualia: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    environment: str = ""
    code_repo_refs: list[str] = field(default_factory=list)
    script_repo_ref: str | None = None
    script_refs: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    state: str | None = None
    domain: str | None = None
    tags: list[str] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)

    def qualia_role(self, role: str) -> Any:
        return self.qualia.get(role)

    def relation_targets(self, relation_type: str) -> list[str]:
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
            "parameters": self.parameters,
            "environment": self.environment,
            "code_repo_refs": self.code_repo_refs,
            "script_repo_ref": self.script_repo_ref,
            "script_refs": self.script_refs,
            "dependencies": self.dependencies,
            "state": self.state,
            "domain": self.domain,
            "tags": self.tags,
            "relations": self.relations,
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass
class UnitRegistry:
    """A collection of runtime units."""

    _by_id: dict[str, Unit] = field(default_factory=dict)

    def add(self, unit: Unit) -> None:
        if unit.id in self._by_id:
            raise ValueError(f"Duplicate unit id: {unit.id}")
        self._by_id[unit.id] = unit

    def add_many(self, units: list[Unit]) -> None:
        for u in units:
            self.add(u)

    def get(self, unit_id: str) -> Unit | None:
        return self._by_id.get(unit_id)

    def all(self) -> list[Unit]:
        return list(self._by_id.values())

    def list_by_env(self, env: str) -> list[Unit]:
        return [u for u in self._by_id.values() if u.environment == env]

    def list_by_state(self, state: str) -> list[Unit]:
        return [u for u in self._by_id.values() if u.state == state]

    def list_by_domain(self, domain: str) -> list[Unit]:
        return [u for u in self._by_id.values() if u.domain == domain]

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, unit_id: str) -> bool:
        return unit_id in self._by_id


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _unit_from_dict(data: dict[str, Any]) -> Unit:
    return Unit(
        id=data["id"],
        type=data.get("type", "ConfigUnit"),
        name=data["name"],
        qualia=data.get("qualia", {}),
        parameters=data.get("parameters", {}),
        environment=data.get("environment", ""),
        code_repo_refs=data.get("code_repo_refs", []),
        script_repo_ref=data.get("script_repo_ref"),
        script_refs=data.get("script_refs", []),
        dependencies=data.get("dependencies", []),
        state=data.get("state"),
        domain=data.get("domain"),
        tags=data.get("tags", []),
        relations=data.get("relations", []),
    )


def build_unit_registry(
    bundle: SchemaBundle | None = None,
    extra_units: list[dict[str, Any]] | None = None,
) -> UnitRegistry:
    """Build a UnitRegistry from schema example + optional injection."""
    if bundle is None:
        bundle = load_all()

    registry = UnitRegistry()

    example = bundle.unit.get("unit-registry-example.json", {})
    for raw in example.get("units", []):
        registry.add(_unit_from_dict(raw))

    if extra_units:
        for raw in extra_units:
            registry.add(_unit_from_dict(raw))

    return registry


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    registry = build_unit_registry()

    print(f"Loaded {len(registry)} unit(s).")
    print()

    print("=== All units ===")
    for u in registry.all():
        print(f"  {u.id}  [env={u.environment}]  name={u.name}")
    print()

    print("=== By env ===")
    for env in sorted({u.environment for u in registry.all()}):
        items = registry.list_by_env(env)
        print(f"  {env}: {[u.id for u in items]}")


if __name__ == "__main__":
    _main()