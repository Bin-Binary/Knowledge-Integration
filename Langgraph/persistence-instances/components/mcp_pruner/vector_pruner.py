# components/mcp_pruner/vector_pruner.py
import hashlib
import logging
import os
import numpy as np
from typing import List, Dict, Any, Optional
from components.mcp_pruner.base_pruner import BaseMCPPruner

logger = logging.getLogger(__name__)


class VectorEmbeddingMCPPruner(BaseMCPPruner):
    """通过动态语义向量检索管理 MCP 工具负载大小
    核心公式：
    • 运行时评分公式：$$S(m, T) = w_1 \\cdot \\text{Sim}(E_m, E_T) + w_2 \\cdot \\text{Freq}(m, H) + w_3 \\cdot \\text{State}(m) - w_4 \\cdot \\text{Cost}(m)$$
    • 子集优化选择：$$\\pi_{\\text{mcp}}(T) = \\arg\\max_{\\mathcal{M} \\subseteq \\mathcal{M}_{\\text{all}}} \\sum_{m \\in \\mathcal{M}} S(m, T)$$
    • 端到端上下文流水线：$$T^{\\prime} = f_{\\text{Protocol}}\\Big(f_{\\text{Schema}} \\big(\\pi_{\\text{mcp}} \\big( T\\big) \\big) \\Big)$$

    执行流水线：
    [开始单轮工具语义裁剪请求]
      │
      ├──► 1. 运行时意图向量化 ──► 本地化推理计算 E_T = Encoder(T) (使用轻量级本地 Embedding 模型)
      │                                                      
      ├──► 2. 内存级矩阵相似度 ──► 余弦相似度 Sim = Cosine(E_m, E_T) ──► 交由基类结合 Freq/State/Cost 计算综合 S(m, T)
      │
      ├──► 3. 原子化拓扑依赖闭包 ──► 基类展开依赖关系 ──► 满足拓扑闭包约束：∀ m ∈ M, Dep(m) ⊆ M
      │
      └──► 4. 贪心背包与确定性重排 ──► 满足 TokenSize 预算 ──► 预压缩 Schema 输出 ──► 字母表确定性排序
    """

    def __init__(
        self,
        mcp_registry: List[Dict[str, Any]],
        embedding_model: Any,
        tau_threshold: float = 0.65,
        cache_path: Optional[str] = None
    ) -> None:
        """
        参数：
            mcp_registry: 由 MCPRegistryBuilder 构建的标准化 MCP 元数据池。
                          支持预注入 "embedding" 字段，或仅提供 "semantic_text" 由本组件按需批量编码。
            embedding_model: 本地化文本向量模型实例，必须支持 `.encode(text)`（单条）及 `.encode(List[str])`（批量）接口。
            tau_threshold: 语义激活裁剪的硬性阈值，默认值为 0.65。
            cache_path: 可选的本地 .npz 向量缓存路径，用于持久化预归一化矩阵，实现冷启动秒加载。
        """
        super().__init__(mcp_registry=mcp_registry, tau_threshold=tau_threshold)
        self._model = embedding_model
        self._tool_names: List[str] = [m["name"] for m in mcp_registry]
        self._tool_embeddings: np.ndarray = np.empty((0, 0), dtype=np.float32)

        if not mcp_registry:
            logger.warning("[Vector Pruner] 初始化时传入的 mcp_registry 为空。")
            return

        # 计算当前注册表的内容指纹哈希，用于校验磁盘缓存是否过期
        registry_fingerprint = self._compute_registry_fingerprint(mcp_registry)
        cache_hit = False

        # 1. 尝试从磁盘 .npz 缓存加载并校验指纹
        if cache_path and os.path.exists(cache_path):
            try:
                with np.load(cache_path, allow_pickle=False) as data:
                    cached_fp = str(data["fingerprint"].item()) if "fingerprint" in data else ""
                    if cached_fp == registry_fingerprint:
                        self._tool_embeddings = data["embeddings"].astype(np.float32)
                        cache_hit = True
                        logger.info(f"[Vector Pruner] 成功命中向量缓存并秒级恢复矩阵: {cache_path}")
                    else:
                        logger.info("[Vector Pruner] 检测到 MCP 工具名称或语义描述已发生变更，自动使旧缓存失效并重建。")
            except Exception as e:
                logger.warning(f"[Vector Pruner] 读取向量缓存失败 ({e})，将回退至内存重新构建。")

        # 2. 若未命中缓存，按需获取/批量推理向量，预构建连续二维矩阵并执行 L2 归一化
        if not cache_hit:
            raw_vecs = self._extract_or_encode_vectors(mcp_registry)
            norms = np.linalg.norm(raw_vecs, axis=1, keepdims=True)
            # 防御性编程：避免零向量导致的除以零异常
            norms[norms == 0] = 1.0
            self._tool_embeddings = raw_vecs / norms

            if cache_path:
                os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)
                np.savez(
                    cache_path,
                    embeddings=self._tool_embeddings,
                    fingerprint=np.array(registry_fingerprint)
                )
                logger.info(f"[Vector Pruner] 已将预归一化向量矩阵持久化至: {cache_path}")

    def _extract_or_encode_vectors(self, mcp_registry: List[Dict[str, Any]]) -> np.ndarray:
        """
        提取或按需批量计算原始语义向量：
        优先读取 registry 中已存在的 "embedding"；对于缺失向量的条目，收集其 "semantic_text" 进行一次性批量编码。
        """
        vectors: List[Optional[Any]] = [m.get("embedding") for m in mcp_registry]
        missing_indices = [i for i, v in enumerate(vectors) if v is None]

        if missing_indices:
            texts_to_encode = [
                mcp_registry[i].get("semantic_text") or f"{mcp_registry[i]['name']}: {mcp_registry[i].get('description', '')}"
                for i in missing_indices
            ]
            logger.info(f"[Vector Pruner] 缓存未命中，正在为 {len(texts_to_encode)} 个工具批量推理语义向量...")
            encoded_batch = self._model.encode(texts_to_encode)
            for idx_pos, reg_idx in enumerate(missing_indices):
                vectors[reg_idx] = encoded_batch[idx_pos]

        return np.array(vectors, dtype=np.float32)

    def _compute_registry_fingerprint(self, mcp_registry: List[Dict[str, Any]]) -> str:
        """
        基于工具名称与富语义文本（或描述）计算确定性 MD5 指纹。
        确保工具增删、描述修改或参数变更时，磁盘 .npz 缓存能够自动刷新。
        """
        sig_items = [
            f"{m['name']}:{m.get('semantic_text') or m.get('description', '')}"
            for m in mcp_registry
        ]
        raw_sig = "|".join(sig_items).encode("utf-8")
        return hashlib.md5(raw_sig.encode("utf-8") if isinstance(raw_sig, str) else raw_sig).hexdigest()

    def _compute_similarities(self, T: str) -> Dict[str, float]:
        """
        [矩阵加速算子]
        运行时意图向量化 E_T，并利用底层 BLAS 加速库执行 1 × N 矩阵点积，
        在微秒级延迟内并行生成所有工具的余弦相似度 Sim(Em, ET)。
        """
        if self._tool_embeddings.size == 0:
            return {}

        # 1. 运行时意图向量化与 L2 归一化
        query_vector = np.array(self._model.encode(T), dtype=np.float32)
        query_norm = np.linalg.norm(query_vector)
        if query_norm > 0:
            query_vector /= query_norm

        # 2. 纯点积计算余弦相似度（因两侧均已完成 L2 归一化，无需除法开销）
        sim_scores = np.dot(self._tool_embeddings, query_vector)

        return {name: float(sim_scores[i]) for i, name in enumerate(self._tool_names)}
