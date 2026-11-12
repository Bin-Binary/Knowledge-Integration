# components/mcp_pruner/rule_pruner.py
import re
import logging
from typing import List, Dict, Any, Pattern
from components.mcp_pruner.base_pruner import BaseMCPPruner

logger = logging.getLogger(__name__)

# 模块级预编译中日韩 (CJK) 字符集正则，避免每次请求重复编译
_CJK_RE = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]')


class RuleHeuristicMCPPruner(BaseMCPPruner):
    """
    模型上下文协议 (MCP) 规则启发式裁剪优化组件。
    
    该组件在 MCPPruningStrategy 严格契约下实现动态启发式规则裁剪策略，
    专用于优化高并发网关 QPS 并最小化大模型预填充延迟 (Prefill Latency)。
    
    已实现的转换流水线：
        T' = f_Protocol( f_Schema( pi_mcp(T) ) )
    """

    def __init__(self, mcp_registry: List[Dict[str, Any]], tau_threshold: float = 0.5) -> None:
        """
        参数：
            mcp_registry: 所有已注册的可用 MCP 元数据定义全局池。
            tau_threshold: 激活截断的硬性过滤阈值。
        """
        super().__init__(mcp_registry=mcp_registry, tau_threshold=tau_threshold)
        
        # 性能优化：在初始化阶段预编译所有工具的关键词匹配规则，避免运行时重复执行 re.compile
        self._compiled_rules: Dict[str, List[Any]] = self._precompile_keyword_rules()

    def _precompile_keyword_rules(self) -> Dict[str, List[Any]]:
        """
        预编译关键词匹配器：
        1. 自动过滤空字符串，防止 "" in T 恒为 True 导致的误召回。
        2. 对包含中日韩字符的关键词保留原始字符串用于 O(N) 子串快速匹配。
        3. 对纯英文/数字边界关键词预编译带单词边界断言 (\b) 的正则对象；对带特殊符号的词安全退化为忽略大小写匹配。
        """
        rules_map: Dict[str, List[Any]] = {}
        for m in self._registry:
            name = m["name"]
            keywords = m.get("keywords", [])
            compiled_list: List[Any] = []
            
            for kw in keywords:
                if not isinstance(kw, str) or not kw.strip():
                    continue
                kw_clean = kw.strip()
                
                if _CJK_RE.search(kw_clean):
                    compiled_list.append(kw_clean)
                else:
                    prefix = r'\b' if kw_clean[0].isalnum() else ''
                    suffix = r'\b' if kw_clean[-1].isalnum() else ''
                    pattern: Pattern[str] = re.compile(
                        prefix + re.escape(kw_clean) + suffix,
                        re.IGNORECASE
                    )
                    compiled_list.append(pattern)
            rules_map[name] = compiled_list
        return rules_map

    def _compute_similarities(self, T: str) -> Dict[str, float]:
        """
        计算 Sim(Em, ET)：通过基于规则的关键词映射获取相关性得分。
        支持平滑置信度：命中单个关键词基础分为 0.85，命中多个关键词平滑递增至 1.0，
        既能单独突破阈值，又能在与向量策略混合 (Hybrid) 时提供更细腻的排序区分度。
        """
        sim_scores: Dict[str, float] = {}
        for name, matchers in self._compiled_rules.items():
            total_rules = len(matchers)
            if total_rules == 0:
                sim_scores[name] = 0.0
                continue

            hit_count = 0
            for matcher in matchers:
                if isinstance(matcher, str):
                    if matcher in T:
                        hit_count += 1
                else:
                    if matcher.search(T):
                        hit_count += 1

            if hit_count == 0:
                sim_scores[name] = 0.0
            else:
                # 命中即赋予 0.85 高置信度基准分，多词命中最高奖励至 1.0
                bonus = 0.15 * min(1.0, (hit_count - 1) / max(1, total_rules - 1)) if total_rules > 1 else 0.15
                sim_scores[name] = round(0.85 + bonus, 4)

        return sim_scores
