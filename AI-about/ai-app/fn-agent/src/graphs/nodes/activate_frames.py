"""activate_frames node.

Reads:  state["parsed_intent"]
Writes: state["frame_instances"]

What it does:
  - Reads the chosen action.
  - Looks up its target frame via Role.values[action].frame.
  - Instantiates that frame (via build_frame_instance).
  - Stores the FrameInstance in state.

Design:
  - For step 6, activate exactly ONE main frame (the one mapped from action).
  - Multi-frame activation (e.g. also activate State / Change) is deferred.
"""

from __future__ import annotations

from src.graphs.state import GraphState, append_trace
from src.loader.index import SchemaIndex
from src.registry.frame_instance import build_frame_instance


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def activate_frames(
    state: GraphState,
    *,
    index: SchemaIndex,
) -> GraphState:
    """Activate frame(s) based on parsed_intent.

    Parameters
    ----------
    state : GraphState
        Must contain "parsed_intent".
    index : SchemaIndex
        Injected schema index.

    Returns
    -------
    GraphState
        Updated state with "frame_instances".
    """
    parsed = state.get("parsed_intent", {})
    action = parsed.get("action")

    instances = []

    if action:
        # Look up the action's target frame from R-ROLES-00
        role = index.role("ActionType")
        target_frame_name = None
        if role:
            for v in role.get("values", []):
                if v.get("value") == action:
                    target_frame_name = v.get("frame")
                    break

        if target_frame_name:
            fid = index.frame_name_to_id.get(target_frame_name)
            if fid:
                inst = build_frame_instance(fid, index=index)
                instances.append(inst)

    state["frame_instances"] = instances
    append_trace(
        state,
        node="activate_frames",
        phase="activation",
        summary=f"activated {len(instances)} frame(s): "
                f"{[i.frame_id for i in instances]}",
    )
    return state