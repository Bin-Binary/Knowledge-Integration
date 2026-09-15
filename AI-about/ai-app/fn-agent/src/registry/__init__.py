"""Runtime registry package.

Holds runtime instances:
  - EntityRegistry:   entity instances
  - UnitRegistry:     unit instances
  - ArtifactRegistry: artifact instances
  - FrameInstance:    activated frame instances
  - Context:          session-scoped context (later step)
"""

from .entity_registry import Entity, EntityRegistry, build_entity_registry
from .unit_registry import Unit, UnitRegistry, build_unit_registry
from .artifact_registry import Artifact, ArtifactRegistry, build_artifact_registry
from .frame_instance import (
    FEBinding,
    FrameInstance,
    build_frame_instance,
    build_frame_instance_by_name,
)

__all__ = [
    "Entity", "EntityRegistry", "build_entity_registry",
    "Unit", "UnitRegistry", "build_unit_registry",
    "Artifact", "ArtifactRegistry", "build_artifact_registry",
    "FEBinding", "FrameInstance",
    "build_frame_instance", "build_frame_instance_by_name",
]