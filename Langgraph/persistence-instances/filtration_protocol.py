from enum import Enum
from typing import TypeVar, Protocol, runtime_checkable

class QualitySeedLevel(Enum):
    """Mark mental content quality level
    Explicitly assigning scalar weights e.g., 1 2 3
    """
    CANDIDATE = 1  
    SILVER = 2     
    GOLDEN = 3    

Refined = TypeVar('Refined', bound='CoarseToFineFiltrationProtocol', covariant=True)

@runtime_checkable
class CoarseToFineFiltrationProtocol (Protocol[Refined]):
    """A coarse-to-fine filtration protocol 
    that progressively curates data from a raw candidate pool into silver-standard pseudo-seeds, 
    and ultimately into gold-standard high-fidelity seeds
    """
    @property
    def quality_level(self) -> QualitySeedLevel: ...

    @property
    def deterministic_id(self) -> str: ...

    def filtration(self, Next_level: QualitySeedLevel, tracking_id: str) -> Refined:
        """WARNING       
        The weight of next_level must be strictly greater than the quality_level of the current node.
        """
        ...
