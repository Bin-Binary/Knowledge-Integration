"""In-memory schema index.

Builds lookup structures from a SchemaBundle:
  - name_to_id / id_to_name for frames
  - frame_schema_id -> frame content
  - entity_type -> attribute definitions
  - relation_type -> definition

Authoritative source for frame names:
  - frame-name-index.json#/name_to_id and id_to_name.
  - The frame files' metadata.frame_schema_name is NOT used for lookup.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .loader import SchemaBundle, load_all


@dataclass
class SchemaIndex:
    """Lookup structures derived from a SchemaBundle."""

    bundle: SchemaBundle

    frame_name_to_id: dict[str, str] = field(default_factory=dict)
    frame_id_to_name: dict[str, str] = field(default_factory=dict)
    frame_id_to_content: dict[str, Any] = field(default_factory=dict)

    entity_type_to_attributes: dict[str, list[dict]] = field(default_factory=dict)
    relation_type_to_def: dict[str, dict] = field(default_factory=dict)

    role_to_def: dict[str, dict] = field(default_factory=dict)
    query_to_def: dict[str, dict] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Frame lookups
    # ------------------------------------------------------------------

    def frame_by_name(self, name: str) -> Any | None:
        fid = self.frame_name_to_id.get(name)
        if fid is None:
            return None
        return self.frame_id_to_content.get(fid)

    def frame_by_id(self, fid: str) -> Any | None:
        return self.frame_id_to_content.get(fid)

    # ------------------------------------------------------------------
    # Entity lookups
    # ------------------------------------------------------------------

    def attributes_for(self, entity_type: str) -> list[dict] | None:
        return self.entity_type_to_attributes.get(entity_type)

    def relation_def(self, relation_type: str) -> dict | None:
        return self.relation_type_to_def.get(relation_type)

    # ------------------------------------------------------------------
    # Role / query lookups
    # ------------------------------------------------------------------

    def role(self, role_id: str) -> dict | None:
        return self.role_to_def.get(role_id)

    def query(self, query_id: str) -> dict | None:
        return self.query_to_def.get(query_id)


def build_index(bundle: SchemaBundle | None = None) -> SchemaIndex:
    """Build a SchemaIndex from a SchemaBundle."""
    if bundle is None:
        bundle = load_all()

    index = SchemaIndex(bundle=bundle)

    # ------------------------------------------------------------------
    # Frames: load content first, then apply authoritative name mapping
    # ------------------------------------------------------------------
    for fname, content in bundle.frames.items():
        meta = content.get("metadata", {})
        fid = meta.get("frame_schema_id")
        if not fid:
            print(f"[warn] frame file {fname} missing metadata.frame_schema_id; skipped.")
            continue
        index.frame_id_to_content[fid] = content

    # Authoritative name mapping from frame-name-index.json
    index_content = bundle.indexes.get("frame-name-index.json", {})
    name_to_id = index_content.get("name_to_id", {})
    id_to_name = index_content.get("id_to_name", {})

    if name_to_id:
        index.frame_name_to_id = dict(name_to_id)
    if id_to_name:
        index.frame_id_to_name = dict(id_to_name)

    # Cross-check: warn if content ids and index ids differ
    content_ids = set(index.frame_id_to_content.keys())
    index_ids = set(index.frame_id_to_name.keys())
    missing_content = index_ids - content_ids
    extra_content = content_ids - index_ids
    if missing_content:
        print(f"[warn] frame ids in index but missing on disk: {sorted(missing_content)}")
    if extra_content:
        print(f"[warn] frame ids on disk but missing in index: {sorted(extra_content)}")

    # ------------------------------------------------------------------
    # Entity
    # ------------------------------------------------------------------
    attr_index = bundle.entity.get("entity-attribute-index.json", {})
    for entity_type, defn in attr_index.get("attribute_index", {}).items():
        index.entity_type_to_attributes[entity_type] = defn.get("attributes", [])

    rel_index = bundle.entity.get("relation-type-index.json", {})
    for rel_type, defn in rel_index.get("relation_types", {}).items():
        index.relation_type_to_def[rel_type] = defn

    # ------------------------------------------------------------------
    # Roles
    # ------------------------------------------------------------------
    roles = bundle.registries.get("R-ROLES-00.json", {})
    for role_id, defn in roles.get("roles", {}).items():
        index.role_to_def[role_id] = defn

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    queries = bundle.registries.get("system-queries.json", {})
    for query_id, defn in queries.get("queries", {}).items():
        index.query_to_def[query_id] = defn

    return index


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    index = build_index()

    print("=== Frames ===")
    for name, fid in sorted(index.frame_name_to_id.items()):
        print(f"  {name} -> {fid}")
    print()

    print("=== Entity attribute types ===")
    for etype in sorted(index.entity_type_to_attributes.keys()):
        n = len(index.entity_type_to_attributes[etype])
        print(f"  {etype}: {n} attribute(s)")
    print()

    print("=== Relation types ===")
    for rtype in sorted(index.relation_type_to_def.keys()):
        print(f"  {rtype}")
    print()

    print("=== Roles ===")
    for role_id in sorted(index.role_to_def.keys()):
        print(f"  {role_id}")
    print()

    print("=== System queries ===")
    for qid in sorted(index.query_to_def.keys()):
        print(f"  {qid}")


if __name__ == "__main__":
    _main()