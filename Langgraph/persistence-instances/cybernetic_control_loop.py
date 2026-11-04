"""
[Schemata@CyberneticControlLoop:Strict-1:1-Mapping]
Production-Ready Universal Aspect-Oriented Control Layer.

This module formalizes the exact vocabulary, structural dimensions, and pathological 
failures defined in the '# Activity', '# Event', '# Process', and '# CyberneticControlLoop' 
schemata into reusable Python structural protocols and aspect-oriented decorators.
"""
import time
import functools
from typing import Dict, Any, Optional, List, Protocol, runtime_checkable
from enum import Enum, auto


# =========================================================================
# I. # Activity 图式元标记 ➔ [Agentive Intent] & [Feedback Cybernetics]
# =========================================================================
class OperationalMotive(Enum):
    """[Activity ➔ Agentive Intent ➔ 2. Operational Motive]"""
    SUSTAIN_DYNAMIC_BALANCE = auto()
    REALIZE_AN_INTENTION = auto()


# =========================================================================
# II. # Event 图式元标记 ➔ [Boundary Markers] & [Consequent Artifacts]
# =========================================================================
@runtime_checkable
class ReducedEvent(Protocol):
    """
    [# Event]: A bounded section in a spatiotemporal coordinate system.
    Stressing the result and the cross-section.
    """
    # [Boundary Markers]
    initial_state_trigger: Any
    terminal_node_culmination: float  # Absolute latch time stamped at event complete
    
    # [Consequent Artifacts]
    resultant_state: Any
    imprint_legacy: Dict[str, Any]  # The static remainder/snapshot precipitated by the event


# =========================================================================
# III. # Process 图式元标记 ➔ [Temporal Topology] & [Internal Dynamics]
# =========================================================================
class ControlRiskProfile(Enum):
    """
    [Process ➔ Temporal Topology ➔ 1. Open Horizon]
    Maps the sliding process's structural risk profile based on its horizon compression.
    """
    IMMUNE_OR_STATIC = auto()       # Low drift/literal flow (Open Horizon is safe)
    PARAMETRIC_DYNAMIC = auto()     # Medium drift/causal trajectory (Chronological Gradient sliding)
    HIGHLY_COMPRESSED = auto()      # High risk; fragile compressed remnants prone to abrupt freezing.


@runtime_checkable
class TargetProcess(Protocol):
    """
    [# Process]: A series of continuous and gradual state evolutions over time.
    Stressing the flow and trajectory without conscious control.
    """
    # [Temporal Topology]
    @property
    def chronological_gradient_latch_time(self) -> float:
        """The specific temporal locus where the process state was last captured."""
        ...

    @property
    def control_risk_profile(self) -> ControlRiskProfile:
        """The evolutionary risk matrix of this sliding process environment."""
        ...


# =========================================================================
# IV. # Activity 图式 ➔ [Objective Fact] (核心代价数据载体)
# =========================================================================
class ExecutionCostSnapshot:
    """[Activity ➔ [Objective Fact]]: Captures physical resource dissipation."""
    def __init__(
        self, 
        spatial_span: List[str],        # 1. Spatial Span (Traversed nodes/channels)
        temporal_span_seconds: float,   # 2. Temporal Span (Actual execution duration)
        energy_dissipation: Dict[str, Any]  # Computation cost, tokens, hardware friction
    ):
        self.spatial_span = spatial_span
        self.temporal_span_seconds = temporal_span_seconds
        self.energy_dissipation = energy_dissipation


# =========================================================================
# V. # CyberneticControlLoop 图式 ➔ [Phase Transitions] & [Pathological Failures]
# =========================================================================
class CulminationTrigger(Enum):
    """ Triggers that force the transition from open process to a bounded Event."""
    TARGET_ACHIEVED = auto()      # Activity hit its internal goal.
    TEMPORAL_TIMEOUT = auto()     # Objective Fact time-span exhausted.
    ENTROPIC_FRICTION = auto()    # System friction/exception forced truncation.


class PathologicalFailure(Exception):
    """Base exception for cybernetic loop breakdown."""
    pass

class ImprintReflectionCounterBite(PathologicalFailure):
    """[Pathological Failures ➔ 1. Imprint Reflection Counter-bite]"""
    pass

class ProcessTyrannyInundation(PathologicalFailure):
    """[Pathological Failures ➔ 2. Process Tyranny Inundation]"""
    pass


# =========================================================================
# VI. GOVERNOR INTERCEPTORS (装饰器切面：只面向 Protocol 契约编程)
# =========================================================================

def dimension_stripping_phase(
    default_trigger: CulminationTrigger = CulminationTrigger.TARGET_ACHIEVED
):
    """
    [Phase Transitions ➔ 2. Dimension Stripping Phase]
    Forces an open-horizon running TargetProcess to freeze into an immutable ReducedEvent.
    
    How it maps to the Schemata:
        1. Pinning and shearing the Open Horizon into a Terminal Node of the ReducedEvent.
        2. Computes the [Objective Fact] (Spatial & Temporal Span) from runtime context.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, process_asset: TargetProcess, *args, **kwargs):
            # Enforce Structural Alignment at Runtime
            if not isinstance(process_asset, TargetProcess):
                raise TypeError(f"Asset must fulfill TargetProcess contract, got {type(process_asset)}")

            # Extract [Objective Fact] metrics injected implicitly via runtime context
            control_meta = kwargs.pop("_control_meta", {})
            start_time = control_meta.get("start_time", time.time())
            traversed_nodes = control_meta.get("traversed_nodes", ["default_node"])
            hardware_metrics = control_meta.get("hardware_metrics", {})
            trigger = control_meta.get("trigger", default_trigger)

            # Execution of Terminal Node pinning
            latch_time = time.time()
            
            # Construct [Objective Fact]
            objective_fact = ExecutionCostSnapshot(
                spatial_span=traversed_nodes,
                temporal_span_seconds=latch_time - start_time,
                energy_dissipation=hardware_metrics
            )
            
            # Pack metadata into the runtime object dynamically matching ReducedEvent requirements
            process_asset._terminal_node_culmination = latch_time
            process_asset._objective_fact = objective_fact
            process_asset._culmination_trigger = trigger

            print(f"\n[Governor Activity ➔ Dimension Stripping Phase]")
            print(f" ✂️ Shearing Process Open Horizon. Terminal Node stamped at Unix: {latch_time}")
            print(f" 📊 [Objective Fact] Spatial Span: {objective_fact.spatial_span} | Temporal Span: {objective_fact.temporal_span_seconds:.4f}s")
            
            try:
                return func(self, process_asset, *args, **kwargs)
            except Exception as e:
                # If the continuous flow overpowers the control authority, throw Process Tyranny
                raise ProcessTyrannyInundation(
                    f"System overwhelmed by TargetProcess parameter evolution. Interception failed."
                ) from e
        return wrapper
    return decorator


def baseline_reinjection_phase(
    custom_risk_thresholds: Optional[Dict[ControlRiskProfile, float]] = None
):
    """
    [Phase Transitions ➔ 3. Baseline Re-injection Phase]
    Revives an Imprint Legacy to feed it back into the TargetProcess as its Initial State.
    
    Anti-Pathology Guard:
        Explicitly monitors the Chronological Gradient. Defends against ImprintReflectionCounterBite.
    """
    # Immunity walls matching Macro Invariant thresholds (in seconds)
    thresholds = custom_risk_thresholds if custom_risk_thresholds else {
        ControlRiskProfile.IMMUNE_OR_STATIC: 86400.0,
        ControlRiskProfile.PARAMETRIC_DYNAMIC: 3600.0,
        ControlRiskProfile.HIGHLY_COMPRESSED: 60.0  # 60s sharp limit
    }

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Fetch the raw snapshot from yesterday's pure persistence pipeline
            asset: Optional[TargetProcess] = func(*args, **kwargs)
            
            if not asset:
                return None
            
            if not isinstance(asset, TargetProcess):
                raise TypeError(f"Retrieved data must fulfill TargetProcess contract, got {type(asset)}")
            
            # 2. Macro Invariant rate-matching calculus
            current_time = time.time()
            phase_lag = current_time - asset.chronological_gradient_latch_time
            max_allowed_lag = thresholds.get(asset.control_risk_profile, 60.0)
            
            print(f"\n[Governor Activity ➔ Baseline Re-injection Phase]")
            print(f" 🔍 Scanning Imprint Legacy via {asset.control_risk_profile.name}")
            print(f" ⏱️ Chronological Gradient Phase Lag: {phase_lag:.2f}s (Max Allowed: {max_allowed_lag}s)")

            # 3. Pathological Countermeasure (Enforcing Macro Invariant 2)
            if phase_lag > max_allowed_lag:
                print(f" 🚨 [Pathological Failure]: {ImprintReflectionCounterBite.__name__} detected!")
                print(f" 🔓 Governor executes Unlatching Command! Dropping rigid baseline to restore system plasticity.")
                # Unidirectional stagnation broken: drop baseline to force Plastic Calibration
                return None
            
            print(f" 🔄 Baseline verified safe. Re-injecting into the next cycle of the Target Process.")
            return asset
        return wrapper
    return decorator
