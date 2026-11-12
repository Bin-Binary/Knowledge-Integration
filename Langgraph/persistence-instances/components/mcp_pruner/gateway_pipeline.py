# components/mcp_pruner/gateway_pipeline.py
"""大模型网关 MCP 工具动态裁剪总装拦截器（轻量级亚毫秒级门面组件）
    全链路端到端执行架构图：
    [上游客户端请求 Payload (OpenCode / Claude / Cursor / Gemini)]
           │
           ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ 1. 防腐层协议适配 (ProtocolAdapterManager)                    │
    │    • 自动探测 OpenAI / Anthropic / Gemini 请求格式            │
    │    • 抽取最新用户意图 T 与历史激活工具集 H                      │
    └──────────────────────────────┬───────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ 2. 无状态注册表标准化 (MCPRegistryBuilder)                    │
    │    • 纯内存将异构工具定义为标准结构，构建富语义文本与 Token 计量  │
    │    • 无损保留 raw_tool 引用，确保出站格式 100% 兼容上游协议      │
    └──────────────────────────────┬───────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ 3. 进程级策略实例池 (Thread-Safe Pruner Pool)                 │
    │    • 按工具集签名哈希 O(1) 复用已预热实例，免除重复矩阵/正则构建  │
    │    • 外层统一包裹 CachedMCPPruner (线程安全 LRU 热缓存)        │
    │    • 内核按需路由（全部为单阶段 < 1ms 极速策略）：               │
    │        ├─ mode="hybrid" -> HybridLinearMCPPruner (线性加权)   │
    │        ├─ mode="vector" -> VectorEmbeddingMCPPruner (纯向量)  │
    │        └─ mode="rule"   -> RuleHeuristicMCPPruner (纯规则)    │
    └──────────────────────────────┬───────────────────────────────┘
                                   │
                                   ▼
    ┌──────────────────────────────────────────────────────────────┐
    │ 4. 协议回写与放行 (adapter.inject_pruned_tools)               │
    │    • 按工具名称字母序重排（最大化上游 LLM Prefix Cache 命中率）  │
    │    • 将保留工具的原协议对象写回 Payload["tools"] 并放行下游      │
    └──────────────────────────────────────────────────────────────┘
"""
import hashlib
import logging
import os
import threading
from typing import Dict, Any, Optional, Callable, Literal

from core.interfaces import MCPPruningStrategy
from components.protocol_adapter.manager import ProtocolAdapterManager
from components.mcp_pruner.registry_builder import MCPRegistryBuilder
from components.mcp_pruner.vector_pruner import VectorEmbeddingMCPPruner
from components.mcp_pruner.rule_pruner import RuleHeuristicMCPPruner
from components.mcp_pruner.hybrid_linear_pruner import HybridLinearMCPPruner
from components.mcp_pruner.cached_pruner import CachedMCPPruner

logger = logging.getLogger(__name__)

PrunerMode = Literal["hybrid", "vector", "rule"]


class MCPGatewayInterceptor:
    """
    大模型网关 MCP 工具动态裁剪总装拦截器。
    集成多协议自动识别、无状态注册表转换、轻量级单阶段策略路由与双层缓存实例池。
    """

    def __init__(
        self,
        embedding_model: Optional[Any] = None,
        mode: PrunerMode = "hybrid",
        tau_threshold: float = 0.60,
        alpha: float = 0.7,
        cache_dir: str = "./data/mcp_cache",
        max_lru_size: int = 2048,
        token_counter: Optional[Callable[[str], int]] = None
    ) -> None:
        """
        参数：
            embedding_model: 本地轻量级向量模型实例（用于混合或纯向量模式）。
            mode: 裁剪策略模式，支持 "hybrid"（单阶段线性加权）、"vector"（纯向量）、"rule"（纯规则）。
            tau_threshold: 语义与规则综合激活阈值。
            alpha: 混合模式下向量语义得分的融合权重（默认 0.7）。
            cache_dir: 底层向量矩阵 .npz 磁盘缓存目录。
            max_lru_size: 运行时线程安全 LRU 热缓存最大条目数。
            token_counter: 可选的精确 Token 计算函数。
        """
        self._model = embedding_model
        self._mode = mode
        self._tau_threshold = tau_threshold
        self._alpha = alpha
        self._cache_dir = cache_dir
        self._max_lru_size = max_lru_size

        self._adapter_manager = ProtocolAdapterManager()
        self._registry_builder = MCPRegistryBuilder(token_counter=token_counter)

        # 进程级裁剪器实例池（Key: 工具集合指纹, Value: 包装了 LRU 缓存的策略实例）
        self._pruner_pool: Dict[str, MCPPruningStrategy] = {}
        self._pool_lock = threading.Lock()

        if self._mode in ("hybrid", "vector") and self._model is None:
            logger.warning("[Gateway Interceptor] 未提供 embedding_model，自动降级为纯规则模式 (mode='rule')。")
            self._mode = "rule"

    def _get_or_create_pruner(self, mcp_registry: list[Dict[str, Any]]) -> MCPPruningStrategy:
        """按工具池签名获取或构建线程安全的裁剪器单例"""
        sig_raw = "|".join(sorted(m["name"] for m in mcp_registry)).encode("utf-8")
        pool_key = hashlib.md5(sig_raw).hexdigest()

        with self._pool_lock:
            if pool_key in self._pruner_pool:
                return self._pruner_pool[pool_key]

        npz_path = os.path.join(self._cache_dir, f"vec_{pool_key[:12]}.npz")

        # 轻量级单阶段策略工厂路由
        if self._mode == "hybrid":
            core_pruner: MCPPruningStrategy = HybridLinearMCPPruner(
                mcp_registry=mcp_registry,
                embedding_model=self._model,
                tau_threshold=self._tau_threshold,
                alpha=self._alpha,
                cache_path=npz_path
            )
        elif self._mode == "vector":
            core_pruner = VectorEmbeddingMCPPruner(
                mcp_registry=mcp_registry,
                embedding_model=self._model,
                tau_threshold=self._tau_threshold,
                cache_path=npz_path
            )
        else:
            core_pruner = RuleHeuristicMCPPruner(
                mcp_registry=mcp_registry,
                tau_threshold=self._tau_threshold
            )

        # 最外层统一包裹运行时 LRU 热缓存装饰器
        wrapped_pruner = CachedMCPPruner(inner_pruner=core_pruner, max_cache_size=self._max_lru_size)

        with self._pool_lock:
            self._pruner_pool[pool_key] = wrapped_pruner

        return wrapped_pruner

    def process_request(self, payload: Dict[str, Any], token_budget: int = 2500) -> Dict[str, Any]:
        """
        网关拦截主入口：接收上游客户端请求体，返回裁剪工具后的精简请求体。
        """
        if not payload.get("tools"):
            return payload

        # 1. 自动识别协议并提取当前意图与历史激活工具
        adapter = self._adapter_manager.resolve(payload)
        current_context, active_history = adapter.extract_context(payload)

        if not current_context.strip():
            return payload

        # 2. 纯内存标准化构建
        mcp_registry = self._registry_builder.build_from_payload(payload, adapter)
        if not mcp_registry:
            return payload

        # 3. 获取预热好的裁剪器实例并执行裁剪
        pruner = self._get_or_create_pruner(mcp_registry)
        pruned_schemas = pruner.prune_tools(
            current_context=current_context,
            active_history_names=active_history,
            token_budget=token_budget
        )

        # 4. 将留下的工具按原协议格式写回请求体
        registry_lookup = {m["name"]: m for m in mcp_registry}
        optimized_payload = adapter.inject_pruned_tools(payload, pruned_schemas, registry_lookup)

        logger.info(
            f"[Gateway Interceptor] 工具裁剪完成: 原始 {len(mcp_registry)} 个 -> 保留 {len(pruned_schemas)} 个 "
            f"(策略={self._mode}, 预算={token_budget} Tokens)"
        )
        return optimized_payload
