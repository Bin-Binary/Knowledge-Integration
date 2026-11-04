"""
[Schemata@MentalContent]
Cognitive Representation Layer derived from FrameNet v17 'Remembering_information'.

This module models the structured mental data structures (MentalContent) that a Cognizer 
encodes and preserves across distributed agent runtimes. It formalizes three distinct 
levels of literal and implied proposition representations, serving as a typified data 
carrier layer for the Persistence system.

Frame Element (FE) Isomorphism:
    * Core FE: Cognizer        -> `cognizer_id`
    * Core FE: Mental_content  -> `mental_content`
    * Periphery FE: Topic      -> `periphery_topic`
    * Periphery FE: Accuracy   -> `periphery_accuracy`
    * Periphery FE: Time       -> `periphery_timestamp`

Dual-Channel Retrieval Bindings:
    1. Deterministic Keys     -> `deterministic_mental_content_id`, `deterministic_thread_id`
    2. Algorithmic Features   -> `algorithmically_feature_items` (Mapped via Enum tokens)

Dependency Note:
    This file acts as a standalone domain layer. It contains no dependency on the 
    Persistence layer, fulfilling the Single Responsibility Principle (SRP) under Strategy A.
"""
from abc import ABC
from enum import Enum, auto
from typing import List, Optional, Any, Dict

class AlgorithmicallyComputedFeatureItems(Enum):
    """Algorithmically Computed Feature Items (vector, scalar, matrix, tensor, graph)"""
    SCALAR: auto()
    VECTOR: auto()
    MATRIX: auto()
    TENSOR: auto()
    GRAPH: auto()
    
class MentalContent(ABC):
    """Cognizer saved the Mental Content in Memory, and can retrieve it. 
    The Mental Content can be Explicit Proposition，Embedded  Question or Hidden Question via Noun Phrase(e.g. *the price* ≈ what is the price)
    Two retrive manner:
    - Deterministic Indexing Keys（mental_content_id, thread_id）
    - Algorithmically Computed Feature Items (vector, scalar, matrix, tensor, graph)
    """
    def __init__(
        self, 
        cognizer_id: str,        
        mental_content: str,
        deterministic_mental_content_id: str,
        deterministic_thread_id: Optional[str] = None,
        algorithmically_feature_items: Optional[
            Dict[AlgorithmicallyComputedFeatureItems, Any]
        ] = None,
        periphery_topic: Optional[List[str]] = None,
        periphery_accuracy: Optional[List[float]] = None,
        periphery_timestamp: Optional[float] = None
    ):
        self.cognizer_id = cognizer_id    
        self.mental_content = mental_content
        self.deterministic_mental_content_id = deterministic_mental_content_id
        self.deterministic_thread_id = deterministic_thread_id
        self.algorithmically_feature_items = algorithmically_feature_items
        self.periphery_topic = periphery_topic
        self.periphery_accuracy = periphery_accuracy
        self.periphery_timestamp = periphery_timestamp
        # 对应 TargetProcess 要求的时相指针字段
        self._terminal_node_culmination: float = 0.0

    @property
    def chronological_gradient_latch_time(self) -> float:
        """1:1 结构映射：过程快照的锁定时间点"""
        return self._terminal_node_culmination
       
class ExplicitProposition(MentalContent):
    """Explicit Proposition: It centers on the literal information presented, 
    tending toward paraphrase-level rewording of the source text rather than introducing concepts
    """

class EmbeddedQuestion(MentalContent):
    """Embedded Question: Framing the context as an interrogative structure triggers retrieval of domain-specific parametric knowledge not present in the prompt, 
    yielding outputs with deeper technical granularity and causal reasoning compared to the explicit proposition condition
    """

class NounPhrase(MentalContent):
    """Hidden Question: A highly compressed noun phrase forces reliance on internal schema for decompression; 
    this is contingent upon prior knowledge and prone to schema-biased semantic drift rather than decoding failure.
    via Noun Phrase(e.g. *the price* ≈ what is the price)
    """
    @property
    def control_risk_profile(self) -> ControlRiskProfile:
        """1:1 概念映射：高度压缩、极易产生反噬死锁的特征类型"""
        return ControlRiskProfile.HIGHLY_COMPRESSED
