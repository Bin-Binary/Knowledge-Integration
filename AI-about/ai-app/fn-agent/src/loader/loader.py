"""Loader for schema JSON files.

Responsibilities:
  - Locate the top-level `schema/` directory.
  - Load all JSON files.
  - Check cross-file references at a shallow level.

Not responsibilities:
  - Full validation (deferred to a later step).
  - Type coercion (schema is plain dict).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _find_schema_root() -> Path:
    """Locate the top-level `schema/` directory.

    Search order:
      1. Environment variable SCHEMA_ROOT (if set).
      2. Walk up from this file until a `schema/` directory is found.
    """
    import os

    env_root = os.getenv("SCHEMA_ROOT")
    if env_root:
        path = Path(env_root).resolve()
        if path.is_dir():
            return path
        raise FileNotFoundError(f"SCHEMA_ROOT points to non-existent dir: {env_root}")

    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "schema"
        if candidate.is_dir():
            return candidate

    raise FileNotFoundError("Could not locate top-level `schema/` directory.")


# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------

@dataclass
class SchemaBundle:
    """Container for all loaded schema data."""

    schema_root: Path
    specs: dict[str, Any] = field(default_factory=dict)
    registries: dict[str, Any] = field(default_factory=dict)
    frames: dict[str, Any] = field(default_factory=dict)
    indexes: dict[str, Any] = field(default_factory=dict)
    entity: dict[str, Any] = field(default_factory=dict)
    unit: dict[str, Any] = field(default_factory=dict)
    artifact: dict[str, Any] = field(default_factory=dict)

    def all_files(self) -> dict[str, Any]:
        """Flatten all loaded data into {relative_path: content}."""
        out: dict[str, Any] = {}
        for group_name, group in [
            ("specs", self.specs),
            ("registries", self.registries),
            ("frames", self.frames),
            ("indexes", self.indexes),
            ("entity", self.entity),
            ("unit", self.unit),
            ("artifact", self.artifact),
        ]:
            for name, content in group.items():
                out[f"{group_name}/{name}"] = content
        return out


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_dir(dir_path: Path) -> dict[str, Any]:
    """Load all *.json files under a directory (non-recursive)."""
    result: dict[str, Any] = {}
    if not dir_path.is_dir():
        return result
    for file in sorted(dir_path.glob("*.json")):
        result[file.name] = _load_json(file)
    return result


def load_all(schema_root: Path | None = None) -> SchemaBundle:
    """Load all schema files into a SchemaBundle."""
    root = schema_root or _find_schema_root()

    bundle = SchemaBundle(schema_root=root)

    bundle.specs = _load_dir(root / "specs")
    bundle.registries = _load_dir(root / "registries")
    bundle.frames = _load_dir(root / "frames")
    bundle.indexes = _load_dir(root / "indexes")
    bundle.entity = _load_dir(root / "entity")
    bundle.unit = _load_dir(root / "unit")
    bundle.artifact = _load_dir(root / "artifact")

    _check_references(bundle)

    return bundle


# ---------------------------------------------------------------------------
# Shallow reference checks
# ---------------------------------------------------------------------------

def _check_references(bundle: SchemaBundle) -> None:
    """Shallow checks that key files and cross-refs exist.

    Raises FileNotFoundError if a required file is missing.
    Warns via print if a logical reference is missing.
    """
    required = {
        "specs": [
            "constraint-field-spec.json",
            "frame-inheritance-spec.json",
            "entity-spec.json",
        ],
        "registries": ["R-ROLES-00.json", "system-queries.json"],
        "indexes": ["frame-name-index.json"],
        "entity": [
            "entity-attribute-index.json",
            "relation-type-index.json",
            "entity-registry.schema.json",
            "entity-registry-example.json",
        ],
    }

    for group_name, files in required.items():
        group = getattr(bundle, group_name)
        for fname in files:
            if fname not in group:
                raise FileNotFoundError(
                    f"Missing required schema file: {group_name}/{fname}"
                )

    if not bundle.frames:
        raise FileNotFoundError("No frame files found under schema/frames/.")

    index = bundle.indexes.get("frame-name-index.json", {})
    name_to_id = index.get("name_to_id", {})
    id_to_name = index.get("id_to_name", {})

    if not name_to_id or not id_to_name:
        print("[warn] frame-name-index.json has empty name_to_id / id_to_name.")

    frame_ids_on_disk = {
        content.get("metadata", {}).get("frame_schema_id")
        for content in bundle.frames.values()
    }
    frame_ids_in_index = set(name_to_id.values())

    missing_on_disk = frame_ids_in_index - frame_ids_on_disk
    if missing_on_disk:
        print(f"[warn] frame ids in index but missing on disk: {sorted(missing_on_disk)}")

    extra_on_disk = frame_ids_on_disk - frame_ids_in_index
    if extra_on_disk:
        print(f"[warn] frame ids on disk but missing in index: {sorted(extra_on_disk)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    bundle = load_all()

    print(f"Schema root: {bundle.schema_root}")
    print()

    for group_name in ["specs", "registries", "frames", "indexes", "entity", "unit", "artifact"]:
        group = getattr(bundle, group_name)
        if not group:
            continue
        print(f"[{group_name}] {len(group)} file(s)")
        for name, content in sorted(group.items()):
            top_keys = list(content.keys())[:6]
            print(f"  - {name}: top_keys={top_keys}")
        print()


if __name__ == "__main__":
    _main()