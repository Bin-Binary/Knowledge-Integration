"""
Unified Abstract Factory Layer aligned 1:1 with FrameNet v17 'Remembering_information'.

This module provides complete all-English signatures and encapsulates both lightweight 
Communication (Scenario 1) and asynchronous high-dimensional Learning (Scenario 2) 
ingestion workflows within a single, cohesive file boundary.
"""
from abc import ABC, abstractmethod
import time
import asyncio
from uuid import uuid4
from typing import List, Optional, Any, Dict

from core.mental_content import ExplicitProposition, EmbeddedQuestion, NounPhrase
from core.compute_feature_items import HeavyAxiomaticComputingStrategy


# =========================================================================
# II. Unified Abstract Factory (All-English Signatures)
# =========================================================================
class MentalContentFactory(ABC):
    """
    Cognitive Memory Factory contract. Ensures that all deterministic keys 
    are generated consistently with strict semantic routing prefixes.
    """
    @staticmethod
    def _generate_deterministic_id(prefix: str) -> str:
        """Automate deterministic id generation for physical data routing."""
        return f"mem_{prefix}_{uuid4().hex[:8]}"

    @abstractmethod
    def create_explicit_proposition(
        self, 
        cognizer_id: str, 
        mental_content: str, 
        **kwargs
    ) -> ExplicitProposition: 
        pass

    @abstractmethod
    def create_embedded_question(
        self, 
        cognizer_id: str, 
        mental_content: str, 
        anchor_proposition_ids: List[str], 
        **kwargs
    ) -> EmbeddedQuestion: 
        pass

    @abstractmethod
    def create_noun_phrase(
        self, 
        cognizer_id: str, 
        mental_content: str, 
        target_schemata_id: str, 
        anchor_proposition_ids: List[str], 
        **kwargs
    ) -> NounPhrase: 
        pass


# =========================================================================
# III. Implementation 1: Communication Scenario Factory (⚡ Light-weight Flow)
# =========================================================================
class CommunicationContextFactory(MentalContentFactory):
    """
    Scenario 1: High-frequency, volatile conversational memory flow.
    Algorithmically computed feature items are kept blank to maintain maximum performance.
    """
    def create_explicit_proposition(
        self, 
        cognizer_id: str, 
        mental_content: str, 
        **kwargs
    ) -> ExplicitProposition:
        return ExplicitProposition(
            cognizer_id=cognizer_id,
            mental_content=mental_content,
            deterministic_mental_content_id=self._generate_deterministic_id("exp"),
            algorithmically_feature_items={},  # Empty for ultra-fast processing
            periphery_topic=kwargs.get('periphery_topic') or [],
            periphery_accuracy=kwargs.get('periphery_accuracy') or [1.0],
            periphery_timestamp=kwargs.get('periphery_timestamp') or time.time()
        )

    def create_embedded_question(
        self, 
        cognizer_id: str, 
        mental_content: str, 
        anchor_proposition_ids: List[str], 
        **kwargs
    ) -> EmbeddedQuestion:
        # Prevent parameter unpack collision with multi-inheritance signature
        causal_expansion_ratio = kwargs.pop('causal_expansion_ratio', 0.0)
        
        return EmbeddedQuestion(
            cognizer_id=cognizer_id,
            mental_content=mental_content,
            deterministic_mental_content_id=self._generate_deterministic_id("emb"),
            algorithmically_feature_items={},
            periphery_topic=kwargs.get('periphery_topic') or [],
            periphery_accuracy=kwargs.get('periphery_accuracy') or [1.0],
            periphery_timestamp=kwargs.get('periphery_timestamp') or time.time(),
            anchor_proposition_ids=anchor_proposition_ids,
            causal_expansion_ratio=causal_expansion_ratio,
            **kwargs
        )

    def create_noun_phrase(
        self, 
        cognizer_id: str, 
        mental_content: str, 
        target_schemata_id: str, 
        anchor_proposition_ids: List[str], 
        **kwargs
    ) -> NounPhrase:
        return NounPhrase(
            cognizer_id=cognizer_id,
            mental_content=mental_content,
            deterministic_mental_content_id=self._generate_deterministic_id("noun"),
            algorithmically_feature_items={},
            periphery_topic=kwargs.get('periphery_topic') or [],
            periphery_accuracy=kwargs.get('periphery_accuracy') or [1.0],
            periphery_timestamp=kwargs.get('periphery_timestamp') or time.time(),
            target_schemata_id=target_schemata_id,
            anchor_proposition_ids=anchor_proposition_ids,
            **kwargs
        )


# =========================================================================
# IV. Implementation 2: Learning Scenario Factory (🧠 Asynchronous Ingestion)
# =========================================================================
class LearningAxiomFactory(MentalContentFactory):
    """
    Scenario 2: Low-frequency, high-value framework/fact consolidation.
    Hooks into external HeavyAxiomaticComputingStrategy to ingest asynchronous 
    pre-computed hyper-dimensional grid features.
    """
    async def create_explicit_proposition(self, cognizer_id: str, mental_content: str, **kwargs) -> ExplicitProposition:
        async_strategy: Optional[HeavyAxiomaticComputingStrategy] = kwargs.get('computing_strategy')
        
        if async_strategy:
            # 💡 利用 await 挂起当前协程，让出 CPU 执行权，实现真正的非阻塞异步调用
            feature_items = await async_strategy.compute_all_feature_items(
                text=mental_content, 
                node_type="explicit", 
                context_meta=kwargs.get('context_meta') or {}
            )
        else:
            feature_items = kwargs.get('algorithmically_feature_items')
            
        if not feature_items:
            raise ValueError("🚨 Learning Scenario requires an active computing_strategy or pre-computed feature_items.")

        return ExplicitProposition(
            cognizer_id=cognizer_id,
            mental_content=mental_content,
            deterministic_mental_content_id=self._generate_deterministic_id("gold_exp"),
            algorithmically_feature_items=feature_items,
            periphery_topic=kwargs.get('periphery_topic') or ["SAVE MEMORY", "RETRIEVE MEMORY"],
            periphery_accuracy=kwargs.get('periphery_accuracy') or [1.0],
            periphery_timestamp=time.time()
        )
