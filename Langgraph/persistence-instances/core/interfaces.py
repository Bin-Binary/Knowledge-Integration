# core/interfaces.py
"""
Domain interfaces and protocol contracts for data filtration and heavy computing.
This module defines the purely abstract APIs to enforce dependency inversion.
"""

from enum import Enum
from typing import TypeVar, Any, Dict, List, Optional, Protocol, runtime_checkable

class QualitySeedLevel(Enum):
    """Mark mental content quality level
    Explicitly assigning scalar weights e.g., 1 2 3
    """
    CANDIDATE = 1  
    SILVER = 2     
    GOLDEN = 3    

@runtime_checkable
class FiltrationStrategy(Protocol):
    """
    The abstract contract of the filtering and purification algorithm.
    It is responsible for asserting when an upgrade can be performed and 
    how to denoise and structure the data content.
    """
    def execute_filter(self) -> str:
        """Perform filtering. 
        If the filtering is successful, the refined text is returned. 
        If the filtering fails, a custom exception is thrown.
        """
        ...

@runtime_checkable
class HeavyAxiomaticComputingStrategy(Protocol):
    """
    [Dependency Inversion] Interface for asynchronous heavy feature calculation.
    Actual computing pipelines (e.g., PyTorch tensor lattice solvers, LLM cross-attention matrix 
    extraction, or graph topology assembly) must implement this to keep domain model pure.
    """
    def compute_all_feature_items(self, **kwargs) -> Dict[Any, Any]:
        """
        Execute asynchronous hyper-dimensional mapping and return all-channel 
        algorithmic feature items (SCALAR, VECTOR, MATRIX, TENSOR, GRAPH).
        """
        ...

"""
The upper bound constraint of generics is bound to the protocol itself, forming a closed loop for progressive data purification.
"""
Refined = TypeVar('Refined', bound='CoarseToFineFiltrationProtocol', covariant=True)

@runtime_checkable
class CoarseToFineFiltrationProtocol(Protocol[Refined]):
    """A coarse-to-fine filtration protocol 
    that progressively curates data from a raw candidate pool into silver-standard pseudo-seeds, 
    and ultimately into gold-standard high-fidelity seeds
    """
    @property
    def quality_level(self) -> QualitySeedLevel: 
        ...

    @property
    def deterministic_id(self) -> str: 
        ...

    def filtration(
        self, 
        next_level: QualitySeedLevel, 
        tracking_id: str,
        strategy: FiltrationStrategy
    ) -> Refined:
        """WARNING       
        The weight of next_level must be strictly greater than the quality_level of the current node.
        """
        ...

@runtime_checkable
class SlidingWindowStrategy(Protocol):
    """
    Sliding Window Protocol defined.
    Enforces rigid and explicit API signature to leverage static type verification.
    """
    def slice_history(
        self,
        history_turns: List[Dict[str, str]],
        msg_tokens: List[int], 
        overflow: int,          
        w_input_safe: int,
        **kwargs: Any
    ) -> List[Dict[str, str]]:
        """Slice and filter message pipeline safely under type boundary rules."""
        ...
