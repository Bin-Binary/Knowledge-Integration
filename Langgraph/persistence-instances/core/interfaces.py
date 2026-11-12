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

@runtime_checkable
class MCPPruningStrategy(Protocol):
    """
    Model Context Protocol (MCP) Pruning Optimization Interface.
    
    This protocol governs the spatial/tool dimension of the context window.
    It formalizes the end-to-end transformation pipeline to optimize QPS and Latency:
        T' = f_Protocol( f_Schema( pi_mcp(T) ) )
    """

    def prune_tools(
        self,
        current_context: str,
        active_history_names: Set[str],
        token_budget: int,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        Dynamically prune the MCP list based on runtime requirements, 
        retaining only the indispensable components:
        
            pi_mcp(T) = arg max_{M ⊆ M_all} sum_{m ∈ M} S(m, T)
            
        Subject to:
            1. sum_{m ∈ M} TokenSize(m) <= B_token (token_budget)
            2. For all m ∈ M, Score(m, T) >= tau_threshold
            3. For all m ∈ M, Dep(m) ⊆ M (Topological Closure)
            
        Transformation Pipeline Steps:
            1. Optimal Subset Selection via scoring optimization: pi_mcp(T)
            2. Compress tool definitions (retain name, truncated desc, input_schema): f_Schema
            3. Compliance filtering in accordance with protocol validation: f_Protocol
            4. Deterministic sorting by name to maximize upstream prefix caching hits.

        Args:
            current_context (str): The runtime session context 'T' (e.g., current user intent).
            active_history_names (Set[str]): Recently activated components for Recency/Frequency scoring.
            token_budget (int): Hard limit for the injected tools payload (B_token).

        Returns:
            List[Dict[str, Any]]: A compliance-conforming, structurally compressed, 
                                  and deterministically ordered subset of tool schemas (T').
        """
        ...

@runtime_checkable
class LLMProtocolAdapter(Protocol):
    """
    大模型上下游网关协议适配契约 (防腐层接口)。
    负责屏蔽 OpenAI / Anthropic / Gemini 等不同模型请求体的格式差异。
    """
    def can_handle(self, payload: Dict[str, Any]) -> bool:
        """探测当前适配器是否支持解析该请求体格式"""
        ...

    def extract_context(self, payload: Dict[str, Any]) -> Tuple[str, Set[str]]:
        """从原始请求体中提取：(用户最新意图文本 T, 历史已激活工具名集合 H)"""
        ...

    def parse_tools(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        将原始请求体中的 tools 转换为内部标准中间结构列表：
        [{"name": str, "description": str, "input_schema": dict, "raw_tool": Any}, ...]
        """
        ...

    def inject_pruned_tools(
        self,
        payload: Dict[str, Any],
        pruned_schemas: List[Dict[str, Any]],
        registry_lookup: Dict[str, Any]
    ) -> Dict[str, Any]:
        """将裁剪保留下来的工具原样封装并写回请求体，保持上游协议 100% 兼容"""
        ...

@runtime_checkable
class RAGRetrievalStrategy(Protocol):
    """
    RAG 知识检索与上下文组装策略契约。
    负责从海量非结构化知识库中召回高相关文档片段，并在预算内打包为 rag_context。
    """
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        执行多路召回与重排，返回排序后的高相关文档片段列表：
        [{"doc_id": str, "content": str, "score": float, "metadata": dict}, ...]
        """
        ...

    def retrieve_and_pack(
        self,
        query: str,
        max_rag_tokens: int,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        执行检索并将结果按 Token 预算截断拼接，直接产出可喂给滑动窗口的 rag_context 字符串。
        """
