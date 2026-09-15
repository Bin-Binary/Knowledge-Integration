"""Runtime view over the artifact registry.

Responsibilities:
  - Hold Artifact instances loaded from
    schema/artifact/artifact-registry-example.json.
  - Support runtime injection of additional artifacts.
  - Provide lookup by id, status, format, belongs_to.

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
# Artifact dataclass
# ---------------------------------------------------------------------------

@dataclass
class Artifact:
    """A runtime artifact instance."""

    id: str
    type: str
    name: str
    qualia: dict[str, Any] = field(default_factory=dict)
    files: list[dict[str, Any]] = field(default_factory=list)
    checksum: str = ""
    storage: str = ""
    status: str = "pending"
    belongs_to: str | None = None
    produced_by: str | None = None
    produced_at: str | None = None
    format: str | None = None
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
            "files": self.files,
            "checksum": self.checksum,
            "storage": self.storage,
            "status": self.status,
            "belongs_to": self.belongs_to,
            "produced_by": self.produced_by,
            "produced_at": self.produced_at,
            "format": self.format,
            "domain": self.domain,
            "tags": self.tags,
            "relations": self.relations,
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass
class ArtifactRegistry:
    """A collection of runtime artifacts."""

    _by_id: dict[str, Artifact] = field(default_factory=dict)

    def add(self, artifact: Artifact) -> None:
        if artifact.id in self._by_id:
            raise ValueError(f"Duplicate artifact id: {artifact.id}")
        self._by_id[artifact.id] = artifact

    def add_many(self, artifacts: list[Artifact]) -> None:
        for a in artifacts:
            self.add(a)

    def get(self, artifact_id: str) -> Artifact | None:
        return self._by_id.get(artifact_id)

    def all(self) -> list[Artifact]:
        return list(self._by_id.values())

    def list_by_status(self, status: str) -> list[Artifact]:
        return [a for a in self._by_id.values() if a.status == status]

    def list_by_format(self, fmt: str) -> list[Artifact]:
        return [a for a in self._by_id.values() if a.format == fmt]

    def list_by_belongs_to(self, entity_id: str) -> list[Artifact]:
        return [a for a in self._by_id.values() if a.belongs_to == entity_id]

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, artifact_id: str) -> bool:
        return artifact_id in self._by_id


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def _artifact_from_dict(data: dict[str, Any]) -> Artifact:
    return Artifact(
        id=data["id"],
        type=data.get("type", "Artifact"),
        name=data["name"],
        qualia=data.get("qualia", {}),
        files=data.get("files", []),
        checksum=data.get("checksum", ""),
        storage=data.get("storage", ""),
        status=data.get("status", "pending"),
        belongs_to=data.get("belongs_to"),
        produced_by=data.get("produced_by"),
        produced_at=data.get("produced_at"),
        format=data.get("format"),
        domain=data.get("domain"),
        tags=data.get("tags", []),
        relations=data.get("relations", []),
    )


def build_artifact_registry(
    bundle: SchemaBundle | None = None,
    extra_artifacts: list[dict[str, Any]] | None = None,
) -> ArtifactRegistry:
    """Build an ArtifactRegistry from schema example + optional injection."""
    if bundle is None:
        bundle = load_all()

    registry = ArtifactRegistry()

    example = bundle.artifact.get("artifact-registry-example.json", {})
    for raw in example.get("artifacts", []):
        registry.add(_artifact_from_dict(raw))

    if extra_artifacts:
        for raw in extra_artifacts:
            registry.add(_artifact_from_dict(raw))

    return registry


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    registry = build_artifact_registry()

    print(f"Loaded {len(registry)} artifact(s).")
    print()

    print("=== All artifacts ===")
    for a in registry.all():
        print(f"  {a.id}  [status={a.status}]  format={a.format}")
        print(f"    belongs_to = {a.belongs_to}")
        print(f"    produced_by = {a.produced_by}")


if __name__ == "__main__":
    _main()