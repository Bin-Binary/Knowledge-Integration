# components/mcp_pruner/vector_pruner.py
import logging
import numpy as np
from typing import List, Dict, Set, Any, Optional
from core.interfaces import MCPPruningStrategy

logger = logging.getLogger(__name__)

class VectorEmbeddingMCPPruner(MCPPruningStrategy):
    """Manage MCP tools payload size via dynamic semantic embedding retrieval
    Formulas:
    • Run Time Scoring Formula: $$S(m, T) = w_1 \\cdot \\text{Sim}(E_m, E_T) + w_2 \\cdot \\text{Freq}(m, H) + w_3 \\cdot \\text{State}(m) - w_4 \\cdot \\text{Cost}(m)$$
    • Subset Optimization Selection: $$\\pi_{\\text{mcp}}(T) = \\arg\\max_{\\mathcal{M} \\subseteq \\mathcal{M}_{\\text{all}}} \\sum_{m \\in \\mathcal{M}} S(m, T)$$
    • End-to-End Context Pipeline: $$T^{\\prime} = f_{\\text{Protocol}}\\Big(f_{\\text{Schema}} \\big(\\pi_{\\text{mcp}} \\big( T\\big) \\big) \\Big)$$

    Execution Pipeline：
    [开始单轮工具语义裁剪请求]
      │
      ├──► 1. 运行时意图向量化 ──► 本地化推理计算 E_T = Encoder(T) (使用轻量级本地 Embedding 模型)
      │                                                      
      ├──► 2. 内存级矩阵相似度 ──► 余弦相似度 Sim = Cosine(E_m, E_T) ──► 结合 Freq/State/Cost 计算综合 S(m, T)
      │
      ├──► 3. 拓扑依赖闭包自愈 ──► 展开依赖关系 ──► 满足拓扑闭包约束：∀ m ∈ M, Dep(m) ⊆ M
      │
      └──► 4. 贪心背包与确定性重排 ──► 满足 TokenSize 预算 ──► f_Schema 压缩 + f_Protocol 过滤 ──► Alphabetical 排序
    """

    def __init__(
        self, 
        mcp_registry: List[Dict[str, Any]], 
        embedding_model: Any, 
        tau_threshold: float = 0.65
    ) -> None:
        """
        Args:
        mcp_registry: The global MCP metadata pool. Dynamic components must pre-inject 
                    pre-computed vector representations, structured as "embedding": np.ndarray.
                    
        embedding_model: A localized text-embedding model instance. The instance must strictly 
                        comply with standard vectorization interfaces supporting the `.encode(text)` 
                        method (e.g., HuggingFace Transformers or SentenceTransformers).
                        
        tau_threshold: The rigid threshold \tau_{threshold} for semantic activation pruning, 
                    with a default value of 0.65. Note that semantic retrieval thresholds 
                    are typically configured higher than those for deterministic rule-based matching.
        """
        self._registry = mcp_registry
        self._model = embedding_model
        self._tau_threshold = tau_threshold
        
        """Pre-construct a two-dimensional contiguous matrix in memory to condense the \(O(N)\) dot product operations into a single, 
        highly efficient \(O(1)\) block-level NumPy matrix multiplication.
        """ 
        self._tool_names = [m["name"] for m in self._registry]
        self._tool_embeddings = np.array([m["embedding"] for m in self._registry], dtype=np.float32)
        """Pre-execute \(L_{2}\) norm normalization so that computing the cosine similarity at runtime can be directly simplified into a pure dot product operation, 
        completely eliminating division overhead.
        """
        norms = np.linalg.norm(self._tool_embeddings, axis=1, keepdims=True)
        """Defense against zero-vector division exception / Defend against division-by-zero exceptions caused by zero vectors."""
        norms[norms == 0] = 1.0
        self._tool_embeddings /= norms

    def _calculate_batch_scores(self, T: str, active_history_names: Set[str]) -> Dict[str, float]:
        """[Matrix Acceleration Operator] 
        Concurrently evaluate the S(m, T) scores for all MCP components in memory via a single-shot execution.
        """
        w1, w2, w3, w4 = 2.0, 1.0, 5.0, 0.001
        
        """1.Runtime Intent Vectorization and Inference \(E_{T}\)"""
        query_vector = np.array(self._model.encode(T), dtype=np.float32)
        query_norm = np.linalg.norm(query_vector)
        if query_norm > 0:
            query_vector /= query_norm
            
        """2. \(\text{Sim}(E_m, E_T)\): Leveraging underlying BLAS acceleration libraries to execute a \(1 \times N\) matrix multiplication, 
        generating all similarity scores in parallel at microsecond-scale latencies.
        """
        sim_scores = np.dot(self._tool_embeddings, query_vector)
        
        scores: Dict[str, float] = {}
        for idx, name in enumerate(self._tool_names):
            m = self._registry[idx]
            
            """3. Freq(m, H): Multi-dimensional Dynamic Calibration"""
            freq_score = 1.0 if name in active_history_names else 0.0
            
            """4. State(m): Rigid Defense Gate for Environment Variables"""
            state_score = 1.0 if m.get("is_enabled", True) else -1000.0
            
            """Cost(m): Watermark Penalty Term"""
            cost_score = float(m.get("token_size", 300))
            
            """Linear Aggregation"""
            scores[name] = (w1 * float(sim_scores[idx])) + (w2 * freq_score) + (w3 * state_score) - (w4 * cost_score)
            
        return scores

    def _resolve_topological_closure(self, selected_names: Set[str]) -> Set[str]:
        """
        Explicit Expansion of Dependencies (Topological Closure) Constraint:
        ∀ m ∈ M, Dep(m) ⊆ M
        """
        closure_set = set(selected_names)
        changed = True
        while changed:
            changed = False
            current_snapshot = list(closure_set)
            for name in current_snapshot:
                tool_meta = next((t for t in self._registry if t["name"] == name), None)
                if tool_meta and "dependencies" in tool_meta:
                    deps: Set[str] = tool_meta["dependencies"]
                    for dep in deps:
                        if dep not in closure_set:
                            closure_set.add(dep)
                            changed = True  
        return closure_set

    def prune_tools(
        self,
        current_context: str,
        active_history_names: Set[str],
        token_budget: int,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Google-grade linter defense: Explicitly declare that the parameter exists solely for protocol alignment."""
        _ = kwargs
        
        """Step 1: Batch calculate semantic scores and extract the winning candidate set that breaches \(\tau _{\text{threshold}}\)."""
        scores = self._calculate_batch_scores(current_context, active_history_names)
        candidate_names = {name for name, score in scores.items() if score >= self._tau_threshold}

        """Step 2: Execute the directed dependency bounded state machine to accomplish topological closure self-healing."""
        closed_candidate_names = self._resolve_topological_closure(candidate_names)

        """Step 3: Greedy Knapsack Seamless Truncation Optimization"""
        sorted_names = sorted(
            closed_candidate_names, 
            key=lambda x: scores.get(x, -100.0), 
            reverse=True
        )

        selected_mcp_list: List[Dict[str, Any]] = []
        current_tokens = 0

        for name in sorted_names:
            tool_meta = next((t for t in self._registry if t["name"] == name), None)
            if not tool_meta:
                continue

            size_cost = tool_meta.get("token_size", 300)
            if current_tokens + size_cost > token_budget:
                logger.warning(f"[Vector Pruner] Token budget bottleneck breached. Evicting lower element: {name}")
                continue  

            current_tokens += size_cost

            """Step 4: f_Schema & f_Protocol Data-Stream Shaping and Dehydrated Compression"""
            raw_desc = tool_meta.get("description", "")
            truncated_desc = raw_desc[:60] + "..." if len(raw_desc) > 60 else raw_desc

            compressed_schema = {
                "name": tool_meta["name"],
                "description": truncated_desc,
                "input_schema": tool_meta.get("input_schema", {"type": "object", "properties": {}}),
                "compliance_flag": tool_meta.get("compliance_flag", True)  
            }

            if compressed_schema["compliance_flag"] is True:
                compressed_schema.pop("compliance_flag", None)
                selected_mcp_list.append(compressed_schema)

        """Step 5: Deterministic Signature Serialization to Safeguard Upstream LLM Prefix Caching Hit Rates"""
        selected_mcp_list.sort(key=lambda x: x["name"])

        return selected_mcp_list
