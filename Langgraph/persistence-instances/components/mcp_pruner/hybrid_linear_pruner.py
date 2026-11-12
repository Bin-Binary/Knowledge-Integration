# components/mcp_pruner/hybrid_linear_pruner.py
"""通过单阶段双路线性加权混合策略管理 MCP 工具负载大小
    核心公式：
    • 线性融合相关性公式：$$\\text{Sim}_{\\text{hybrid}}(m, T) = \\max\\Big(\\alpha \\cdot \\text{Sim}_{\\text{vec}}(E_m, E_T) + (1 - \\alpha) \\cdot \\text{Sim}_{\\text{rule}}(m, T), \\; \\mathbb{I}_{\\text{override}} \\cdot \\text{Sim}_{\\text{rule}}(m, T)\\Big)$$
    • 运行时综合评分公式：$$S(m, T) = w_1 \\cdot \\text{Sim}_{\\text{hybrid}}(m, T) + w_2 \\cdot \\text{Freq}(m, H) + w_3 \\cdot \\text{State}(m) - w_4 \\cdot \\text{Cost}(m)$$
    • 子集优化选择：$$\\pi_{\\text{mcp}}(T) = \\arg\\max_{\\mathcal{M} \\subseteq \\mathcal{M}_{\\text{all}}} \\sum_{m \\in \\mathcal{M}} S(m, T)$$
    • 端到端上下文流水线：$$T^{\\prime} = f_{\\text{Protocol}}\\Big(f_{\\text{Schema}} \\big(\\pi_{\\text{mcp}} \\big( T\\big) \\big) \\Big)$$

    单阶段双路线性加权架构图（当前实现）：
    [开始单轮工具混合裁剪请求 (Intent T)]
           │
           ├──────────────────────────────┐
           ▼ (稠密语义分支: 权重 α)         ▼ (稀疏规则分支: 权重 1-α)
    ┌─────────────────────┐        ┌──────────────────────────┐
    │ VectorEmbedding     │        │ RuleHeuristic            │
    │ (矩阵点积余弦相似度)  │        │ (预编译 CJK/词边界正则)    │
    │ Sim_vec ∈ [-1, 1]   │        │ Sim_rule ∈ {0, [0.85, 1]}│
    └──────────┬──────────┘        └─────────────┬────────────┘
               │                                 │
               └────────────────┬────────────────┘
                                ▼
               ┌─────────────────────────────────┐
               │ 单阶段线性加权融合 + 强规则直通保底 │
               │ Sim_hybrid = α*Sim_vec +        │
               │              (1-α)*Sim_rule     │
               └────────────────┬────────────────┘
                                ▼
               ┌─────────────────────────────────┐
               │ 基类 BaseMCPPruner 统一后处理     │
               │ 1. 综合打分聚合 S(m, T)          │
               │ 2. 阈值截断 (Score >= τ)         │
               │ 3. 原子化拓扑依赖闭包展开         │
               │ 4. Token 预算贪心背包与确定性排序  │
               └────────────────┬────────────────┘
                                ▼
               [输出精简工具集 T' (< 1ms 极低延迟)]

    ====================================================================================
    [架构演进对比] 本方案 (单阶段线性加权) vs 工业级两阶段漏斗方案 (KNN+BM25+RRF+Rerank)：
    
    1. 稀疏检索机制不同：
       - 本方案：启发式正则/关键词匹配（布尔命中 + 命中率平滑分），零统计建模开销，适合结构化工具名与固定指令。
       - 两阶段方案：BM25 概率统计检索（基于词频 TF 与逆文档频率 IDF），无需人工维护关键词，适合海量非结构化长文本。
       
    2. 多路分数融合方式不同：
       - 本方案：线性加权求和（要求 Vector 与 Rule 得分预先对齐到同一量纲 [0, 1]，依赖超参数 α 调优）。
       - 两阶段方案：RRF 倒数排名融合（Score = 1 / (k + rank)），只依赖各路排名顺序，天然屏蔽不同检索器量纲差异。
       
    3. 精排交互深度与延迟不同（核心取舍）：
       - 本方案（单阶段）：无 Cross-Encoder 重排模型，全内存矩阵运算，单次拦截耗时 < 1ms，专攻高并发低延迟网关。
       - 两阶段方案（Retrieve & Rerank）：粗排扩大窗口召回（TopK × 30）后，引入交叉编码器（如 gte-rerank）对前 50 候选
         做深度 Token 级交互精排，精度上限更高，但推理耗时增至 30~150ms，必须配合超时熔断回退 RRF 机制。
         
    4. 适用规模建议：
       - 工具总数 < 2,000 个（常规 MCP 网关场景）：优先使用本方案，兼顾亚毫秒级延迟与高召回精度。
       - 工具总数 > 5,000 个或存在大量高度相似的同义 API：演进为两阶段 RRF + Rerank 架构。
    ====================================================================================
"""
import logging
from typing import List, Dict, Any, Optional
from components.mcp_pruner.base_pruner import BaseMCPPruner
from components.mcp_pruner.vector_pruner import VectorEmbeddingMCPPruner
from components.mcp_pruner.rule_pruner import RuleHeuristicMCPPruner

logger = logging.getLogger(__name__)


class HybridLinearMCPPruner(BaseMCPPruner):
    """
    单阶段双路线性加权 MCP 工具裁剪策略（稠密向量语义召回 + 稀疏启发式规则召回）。

    核心融合逻辑：
        Sim_hybrid(m, T) = α * Sim_vector(m, T) + (1 - α) * Sim_rule(m, T)
        若启用强规则保底 (rule_override=True)，当规则精确命中高置信度关键词 (>= 0.85) 时，
        直接取 max(Sim_hybrid, Sim_rule)，防止专有名词或指令前缀被向量分稀释。
    """

    def __init__(
        self,
        mcp_registry: List[Dict[str, Any]],
        embedding_model: Any,
        tau_threshold: float = 0.60,
        alpha: float = 0.7,
        cache_path: Optional[str] = None,
        rule_override: bool = True
    ) -> None:
        """
        参数：
            mcp_registry: 由 MCPRegistryBuilder 构建的标准化 MCP 元数据池。
            embedding_model: 本地文本向量模型实例。
            tau_threshold: 激活截断的硬性过滤阈值。
            alpha: 向量语义得分的融合权重（默认 0.7，即向量占 70%，规则占 30%）。
            cache_path: 底层向量矩阵的本地 .npz 缓存路径。
            rule_override: 是否开启强规则直通保底（防止专有名词或指令前缀被向量分稀释）。
        """
        super().__init__(mcp_registry=mcp_registry, tau_threshold=tau_threshold)
        self._alpha = max(0.0, min(1.0, alpha))
        self._rule_override = rule_override

        # 组合内部双路引擎
        self._vector_engine = VectorEmbeddingMCPPruner(
            mcp_registry=mcp_registry,
            embedding_model=embedding_model,
            tau_threshold=tau_threshold,
            cache_path=cache_path
        )
        self._rule_engine = RuleHeuristicMCPPruner(
            mcp_registry=mcp_registry,
            tau_threshold=tau_threshold
        )

    def _compute_similarities(self, T: str) -> Dict[str, float]:
        """并行计算双路相关性得分并执行单阶段线性加权融合"""
        vec_sims = self._vector_engine._compute_similarities(T)
        rule_sims = self._rule_engine._compute_similarities(T)

        hybrid_scores: Dict[str, float] = {}
        for name in self._registry_map:
            v_score = vec_sims.get(name, 0.0)
            r_score = rule_sims.get(name, 0.0)

            blended = (self._alpha * v_score) + ((1.0 - self._alpha) * r_score)
            if self._rule_override and r_score >= 0.85:
                hybrid_scores[name] = max(blended, r_score)
            else:
                hybrid_scores[name] = blended

        return hybrid_scores
