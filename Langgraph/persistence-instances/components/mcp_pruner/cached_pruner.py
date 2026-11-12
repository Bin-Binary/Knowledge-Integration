# components/mcp_pruner/cached_pruner.py
import hashlib
import logging
import threading
from collections import OrderedDict
from typing import List, Dict, Set, Any
from core.interfaces import MCPPruningStrategy

logger = logging.getLogger(__name__)


class CachedMCPPruner(MCPPruningStrategy):
    """
    [通用运行时热缓存装饰器]
    可套在任何遵循 MCPPruningStrategy 协议的策略（纯向量、纯规则、双路混合策略）外层，
    提供线程安全的 LRU 内存级热缓存，将高频重复意图的裁剪耗时降至 0.01ms 级别。

    使用示例：
        # 1. 初始化带磁盘持久化(.npz)的向量裁剪器
        vec_pruner = VectorEmbeddingMCPPruner(
            mcp_registry=registry,
            embedding_model=model,
            cache_path="./cache/tools.npz"
        )

        # 2. 初始化规则裁剪器
        rule_pruner = RuleHeuristicMCPPruner(mcp_registry=registry)

        # 3. 组合成“双路混合策略”（向量 70% + 规则 30%）
        hybrid_pruner = HybridMCPPruner(vector_pruner=vec_pruner, rule_pruner=rule_pruner, alpha=0.7)

        # 4. 最外层套上“运行时热缓存装饰器”
        final_pruner = CachedMCPPruner(inner_pruner=hybrid_pruner, max_cache_size=2048)

        # 上游调用方完全无感知，依然只调用标准的 MCPPruningStrategy 接口！
        tools = final_pruner.prune_tools("帮我查一下今天北京的天气", {"weather_api"}, token_budget=1500)
    """

    def __init__(self, inner_pruner: MCPPruningStrategy, max_cache_size: int = 1024) -> None:
        self._inner = inner_pruner
        self._max_size = max(1, max_cache_size)
        self._lru_cache: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict()
        self._lock = threading.Lock()
        
        # 统计指标，方便网关监控缓存命中率
        self._hits = 0
        self._misses = 0

    def _get_registry_signature(self) -> str:
        """提取内部裁剪器当前挂载的工具池名称签名，防止不同工具集的请求发生缓存串扰"""
        registry_map = getattr(self._inner, "_registry_map", None)
        if isinstance(registry_map, dict):
            return ",".join(sorted(registry_map.keys()))
        return ""

    def _make_cache_key(self, context: str, history: Set[str], budget: int, kwargs: Dict[str, Any]) -> str:
        """将输入参数与当前工具池签名生成唯一的确定性 MD5 哈希键"""
        reg_sig = self._get_registry_signature()
        extra_sig = str(sorted(kwargs.items())) if kwargs else ""
        raw_key = f"{reg_sig}|{context}|{sorted(history)}|{budget}|{extra_sig}"
        return hashlib.md5(raw_key.encode("utf-8")).hexdigest()

    def prune_tools(
        self,
        current_context: str,
        active_history_names: Set[str],
        token_budget: int,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        key = self._make_cache_key(current_context, active_history_names, token_budget, kwargs)

        # 1. 线程安全地查询热缓存
        with self._lock:
            if key in self._lru_cache:
                self._lru_cache.move_to_end(key)
                self._hits += 1
                # 返回浅拷贝列表，防止外部调用方修改列表结构污染缓存
                return list(self._lru_cache[key])
            self._misses += 1

        # 2. 未命中：在锁外执行内部策略计算（避免推理耗时阻塞其他并发线程）
        result = self._inner.prune_tools(current_context, active_history_names, token_budget, **kwargs)

        # 3. 线程安全地写入缓存并维持容量上限
        with self._lock:
            self._lru_cache[key] = list(result)
            self._lru_cache.move_to_end(key)
            if len(self._lru_cache) > self._max_size:
                self._lru_cache.popitem(last=False)

        return list(result)

    def clear_cache(self) -> None:
        """支持在 MCP 工具动态上下线时手动清空热缓存"""
        with self._lock:
            self._lru_cache.clear()
            self._hits = 0
            self._misses = 0

    @property
    def stats(self) -> Dict[str, Any]:
        """暴露缓存命中率监控指标"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total) if total > 0 else 0.0
            return {
                "size": len(self._lru_cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4)
            }
