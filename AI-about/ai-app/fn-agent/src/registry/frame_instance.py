"""Runtime view over activated frames.

Responsibilities:
  - Hold FrameInstance: a runtime instantiation of a frame file.
  - Hold FEBinding:   per-FE binding state during filling.

Not responsibilities:
  - Frame activation (later node).
  - FE filling logic (later node).
  - Full inheritance merge (later node `resolve_inheritance`).
  - For now, `_resolve_inherited_fe_def` does a minimal inherit-path
    resolution so that pure-inherit FEs are visible in the binding list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.loader.loader import SchemaBundle, load_all
from src.loader.index import SchemaIndex, build_index


# ---------------------------------------------------------------------------
# FEBinding
# ---------------------------------------------------------------------------

@dataclass
class FEBinding:
    """Runtime binding state for a single FE."""

    fe_name: str
    fe_role: str                   # "core" | "peripheral"
    fe_required: bool = False
    fe_type_ref: dict[str, Any] = field(default_factory=dict)

    value: Any = None
    source: str | None = None
    confidence: float = 0.0
    status: str = "missing"
    candidates: list[Any] = field(default_factory=list)

    def set_value(self, value: Any, source: str, confidence: float = 1.0) -> None:
        self.value = value
        self.source = source
        self.confidence = confidence
        self.status = "filled"
        self.candidates = []

    def set_candidates(self, candidates: list[Any]) -> None:
        self.candidates = list(candidates)
        self.status = "multi_candidate"
        self.value = None
        self.source = None
        self.confidence = 0.0

    def set_conflict(self, candidates: list[Any]) -> None:
        self.candidates = list(candidates)
        self.status = "conflict"

    def clear(self) -> None:
        self.value = None
        self.source = None
        self.confidence = 0.0
        self.status = "missing"
        self.candidates = []

    def is_filled(self) -> bool:
        return self.status == "filled"

    def is_missing(self) -> bool:
        return self.status == "missing"

    def has_candidates(self) -> bool:
        return self.status in ("multi_candidate", "conflict")

    def to_dict(self) -> dict[str, Any]:
        return {
            "fe_name": self.fe_name,
            "fe_role": self.fe_role,
            "fe_required": self.fe_required,
            "fe_type_ref": self.fe_type_ref,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "status": self.status,
            "candidates": self.candidates,
        }


# ---------------------------------------------------------------------------
# FrameInstance
# ---------------------------------------------------------------------------

@dataclass
class FrameInstance:
    """A runtime instantiation of a frame file."""

    frame_id: str
    frame_name: str
    parent_frame_id: str | None = None
    domain: str | None = None
    resolved: bool = False

    fe_bindings: dict[str, FEBinding] = field(default_factory=dict)
    status: str = "active"

    def bind_fe(
        self,
        fe_name: str,
        fe_role: str,
        fe_required: bool = False,
        fe_type_ref: dict[str, Any] | None = None,
    ) -> FEBinding:
        if fe_name in self.fe_bindings:
            raise ValueError(f"FE already bound: {fe_name}")
        binding = FEBinding(
            fe_name=fe_name,
            fe_role=fe_role,
            fe_required=fe_required,
            fe_type_ref=fe_type_ref or {},
        )
        self.fe_bindings[fe_name] = binding
        return binding

    def get_binding(self, fe_name: str) -> FEBinding | None:
        return self.fe_bindings.get(fe_name)

    def set_status(self, status: str) -> None:
        self.status = status

    def list_core_fe(self) -> list[str]:
        return [n for n, b in self.fe_bindings.items() if b.fe_role == "core"]

    def list_peripheral_fe(self) -> list[str]:
        return [n for n, b in self.fe_bindings.items() if b.fe_role == "peripheral"]

    def list_missing(self) -> list[str]:
        return [n for n, b in self.fe_bindings.items() if b.status == "missing"]

    def list_filled(self) -> list[str]:
        return [n for n, b in self.fe_bindings.items() if b.status == "filled"]

    def list_required_missing(self) -> list[str]:
        return [
            n for n, b in self.fe_bindings.items()
            if b.fe_required and b.status == "missing"
        ]

    def is_saturated(self) -> bool:
        return len(self.list_required_missing()) == 0

    def is_blocked(self) -> bool:
        return self.status == "blocked"

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "frame_name": self.frame_name,
            "parent_frame_id": self.parent_frame_id,
            "domain": self.domain,
            "resolved": self.resolved,
            "status": self.status,
            "fe_bindings": {n: b.to_dict() for n, b in self.fe_bindings.items()},
        }


# ---------------------------------------------------------------------------
# Inheritance helper (minimal)
# ---------------------------------------------------------------------------

def _find_frame_content(bundle: SchemaBundle, frame_id: str) -> dict | None:
    for _, fc in bundle.frames.items():
        if fc.get("metadata", {}).get("frame_schema_id") == frame_id:
            return fc
    return None


def _resolve_inherited_fe_def(
    fe_def: dict,
    parent_content: dict | None,
) -> dict:
    """Return an effective FE definition.

    If fe_def has `inherit`, base is looked up in parent_content
    and then `override` is applied. Otherwise fe_def is returned as-is.
    """
    if "inherit" not in fe_def:
        return fe_def

    path = fe_def["inherit"]
    parts = path.split(".")
    if len(parts) != 3:
        return fe_def

    parent_id, role_key, fe_name = parts

    if parent_content is None:
        return fe_def

    parent_fe_block = parent_content.get(role_key, {})
    parent_fe_def = parent_fe_block.get(fe_name, {})

    base = dict(parent_fe_def)

    override = fe_def.get("override")
    if override:
        for key, val in override.items():
            if key == "constraint":
                merged = dict(base.get("constraint", {}))
                merged.update(val)
                base["constraint"] = merged
            else:
                base[key] = val

    return base


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _build_fe_bindings(
    frame_content: dict[str, Any],
    instance: FrameInstance,
    bundle: SchemaBundle,
) -> None:
    parent_id = frame_content.get("metadata", {}).get("parent_frame_schema_id")
    parent_content = _find_frame_content(bundle, parent_id) if parent_id else None

    for role_key, role_name in [("core_fe", "core"), ("peripheral_fe", "peripheral")]:
        fe_block = frame_content.get(role_key, {})
        for fe_name, fe_def in fe_block.items():
            if not isinstance(fe_def, dict):
                continue

            effective = _resolve_inherited_fe_def(fe_def, parent_content)

            required = effective.get("required", False)
            constraint = effective.get("constraint", {})
            type_ref = constraint.get("type", {})

            instance.bind_fe(
                fe_name=fe_name,
                fe_role=role_name,
                fe_required=required,
                fe_type_ref=type_ref,
            )


def _lookup_domain(bundle: SchemaBundle, frame_id: str) -> str | None:
    index_content = bundle.indexes.get("frame-name-index.json", {})
    for f in index_content.get("frames", []):
        if f.get("frame_schema_id") == frame_id:
            return f.get("domain")
    return None


def build_frame_instance(
    frame_id: str,
    bundle: SchemaBundle | None = None,
    index: SchemaIndex | None = None,
) -> FrameInstance:
    """Build an empty FrameInstance from a frame file by frame_schema_id."""
    if bundle is None:
        bundle = load_all()
    if index is None:
        index = build_index(bundle)

    content = _find_frame_content(bundle, frame_id)
    if content is None:
        raise ValueError(f"Frame not found: {frame_id}")

    meta = content.get("metadata", {})
    instance = FrameInstance(
        frame_id=frame_id,
        frame_name=meta.get("frame_schema_name", ""),
        parent_frame_id=meta.get("parent_frame_schema_id"),
        domain=_lookup_domain(bundle, frame_id),
    )

    _build_fe_bindings(content, instance, bundle)
    return instance


def build_frame_instance_by_name(
    frame_name: str,
    bundle: SchemaBundle | None = None,
    index: SchemaIndex | None = None,
) -> FrameInstance:
    if bundle is None:
        bundle = load_all()
    if index is None:
        index = build_index(bundle)
    fid = index.frame_name_to_id.get(frame_name)
    if fid is None:
        raise ValueError(f"Frame name not found: {frame_name}")
    return build_frame_instance(fid, bundle, index)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    frame_id = "F-INTENTIONALLY-ACT-00"
    inst = build_frame_instance(frame_id)

    print(f"FrameInstance: {inst.frame_id} ({inst.frame_name})")
    print(f"  parent_frame_id = {inst.parent_frame_id}")
    print(f"  domain          = {inst.domain}")
    print(f"  resolved        = {inst.resolved}")
    print(f"  status          = {inst.status}")
    print()

    print(f"core FE ({len(inst.list_core_fe())}):")
    for name in inst.list_core_fe():
        b = inst.get_binding(name)
        print(f"  - {name:12s} required={b.fe_required} type_ref={b.fe_type_ref}")
    print()

    print(f"peripheral FE ({len(inst.list_peripheral_fe())}):")
    for name in inst.list_peripheral_fe():
        b = inst.get_binding(name)
        print(f"  - {name:12s} required={b.fe_required} type_ref={b.fe_type_ref}")
    print()

    print("initial missing (required):")
    print(f"  {inst.list_required_missing()}")
    print()

    inst.get_binding("agent").set_value("human:user123", source="explicit", confidence=1.0)
    inst.get_binding("act").set_value("build", source="explicit", confidence=0.92)
    inst.get_binding("purpose").set_candidates(["发布", "回滚", "追溯"])

    print("after partial fill:")
    for name in ["agent", "act", "purpose"]:
        b = inst.get_binding(name)
        print(f"  - {name:12s} status={b.status:16s} value={b.value} candidates={b.candidates}")
    print()

    print(f"saturated? {inst.is_saturated()}")
    print(f"required missing: {inst.list_required_missing()}")


if __name__ == "__main__":
    _main()