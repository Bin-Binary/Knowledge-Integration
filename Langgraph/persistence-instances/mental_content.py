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
    SCALAR = auto()
    VECTOR = auto()
    MATRIX = auto()
    TENSOR = auto()
    GRAPH = auto()

class MentalContent(ABC):
    """
    Cognizer saved the Mental Content in Memory, and can retrieve it. 
    The Mental Content can be Explicit Proposition, Embedded Question or Hidden Question via Noun Phrase
    (e.g., *the price* ≈ what is the price).

    Two retrieve manners:
    - Deterministic Indexing Keys: (mental_content_id, thread_id)
    - Algorithmically Computed Feature Items: (vector, scalar, matrix, tensor, graph)

    Manifest following polymorphic forms when mental content exhibit discrepancies across task scenarios:

    1. Communication Mission Scenario (⚡ Ultra Light-weight Flow)
       - Characterized by high-frequency, ephemeral dialog logic.
       - No heavy multidimensional matrices or state tensors are computed or attached.
       
       Example structure:
       - mental_content: "Cognizer saved the Mental Content in Memory, and can retrieve it"
       - algorithmically_feature_items: {}  # Kept blank or only containing minimal SCALAR anchor

    2. Learning Knowledge Mission Scenario (🧠 Deep Axiomatic/Ontology Ingestion)
       - Characterized by low-frequency, high-value framework/fact consolidation.
       - Fully hyper-dimensionalized with topological, semantic, and joint probability state tensors.
       
       Example structure:
       - mental_content: "Cognizer saved the Mental Content in Memory, and can retrieve it"
       - periphery_topic: ["SAVE MEMORY", "RETRIEVE MEMORY"]
       - periphery_accuracy: [1.0]  # Stamped as absolute factive presupposition via FrameNet v17
       - algorithmically_feature_items:
         {
             "SCALAR": {"axiom_confidence": 1.0},
             "VECTOR": [0.015, -0.234, 0.789, ..., 0.456],
             "MATRIX": {
                 "headers": ["Cognizer", "Mental_Content", "Memory", "Retrieve"],
                 "weights": [
                     [1.00, 0.85, 0.70, 0.90],  
                     [0.85, 1.00, 0.95, 0.80],  
                     [0.70, 0.95, 1.00, 0.75], 
                     [0.90, 0.80, 0.75, 1.00]   
                 ],
                 "purpose": "concept_cross_attention_weights"        
             },
             "TENSOR": {
                 "shape":,
                 "dense_data": [
                     [[0.12, 0.88], [0.45, 0.55], [0.90, 0.10]],  # Candidate Layer
                     [[0.05, 0.95], [0.20, 0.80], [0.70, 0.30]],  # Silver Layer
                     [[0.00, 1.00], [0.00, 1.00], [0.01, 0.99]]   # Golden Layer
                 ],
                 "purpose": "cognitive_state_hidden_tensor_embedding"
             },
             "GRAPH": {  # 🔒 Fixed: Added outer bracket for valid JSON/Dict structure
                 "nodes": [
                     {"id": "Cognizer", "type": "Core_FE"},
                     {"id": "Mental_content", "type": "Core_FE"},
                     {"id": "Memory", "type": "Internal_Schema"},
                     {"id": "Retrieval", "type": "Behavioral_Action"}
                 ],
                 "edges": [
                     {"source": "Cognizer", "target": "Mental_content", "relation": "encodes_and_preserves"},
                     {"source": "Mental_content", "target": "Memory", "relation": "saved_in"},
                     {"source": "Cognizer", "target": "Mental_content", "relation": "can_retrieve"}
                 ]        
             }
         }
    """
    def __init__(
        self, 
        cognizer_id: str,        
        mental_content: str,
        deterministic_mental_content_id: str,
        algorithmically_feature_items: Optional[
            Dict[AlgorithmicallyComputedFeatureItems, Any]
        ] = None,
        periphery_topic: Optional[List[str]] = None,
        periphery_accuracy: Optional[List[float]] = None,
        periphery_timestamp: Optional[float] = None,
    ):
        self.cognizer_id = cognizer_id    
        self.mental_content = mental_content
        self.deterministic_mental_content_id = deterministic_mental_content_id
        self.algorithmically_feature_items = algorithmically_feature_items
        self.periphery_topic = periphery_topic
        self.periphery_accuracy = periphery_accuracy
        self.periphery_timestamp = periphery_timestamp

class ExplicitProposition(MentalContent):
    """Explicit Proposition: It centers on the literal information presented, 
    tending toward paraphrase-level rewording of the source text rather than introducing concepts
    """

class EmbeddedQuestion(MentalContent):
    """Embedded Question: Framing the context as an interrogative structure triggers retrieval of domain-specific parametric knowledge not present in the prompt, 
    yielding outputs with deeper technical granularity and causal reasoning compared to the explicit proposition condition
    """
    def __init__(
        self, 
        *args, 
        anchor_proposition_ids: Optional[List[str]] = None, 
        causal_expansion_ratio: float = 0.0,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.anchor_proposition_ids = anchor_proposition_ids
        self.causal_expansion_ratio = causal_expansion_ratio

class NounPhrase(MentalContent):
    """Hidden Question: A highly compressed noun phrase forces reliance on internal schema for decompression; 
    this is contingent upon prior knowledge and prone to schema-biased semantic drift rather than decoding failure.
    via Noun Phrase(e.g. *the price* ≈ what is the price)
    schemata vs instances:
    target_schemata_id associated schemata; anchor_proposition_ids associated ExplicitProposition(instances).
    """
    def __init__(
        self, 
        *args, 
        target_schemata_id: Optional[str] = None, 
        anchor_proposition_ids: Optional[List[str]] = None, 
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.target_schemata_id = target_schemata_id
        self.anchor_proposition_ids = anchor_proposition_ids
