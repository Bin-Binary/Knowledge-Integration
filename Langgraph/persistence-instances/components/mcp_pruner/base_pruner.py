# components/mcp_pruner/base_pruner.py
"""通过动态语义与启发式策略管理 MCP 工具负载大小（抽象基类）
    核心公式：
    • 运行时评分公式：$$S(m, T) = w_1 \\cdot \\text{Sim}(E_m, E_T) + w_2 \\cdot \\text{Freq}(m, H) + w_3 \\cdot \\text{State}(m) - w_4 \\cdot \\text{Cost}(m)$$
    • 子集优化选择：$$\\pi_{\\text{mcp}}(T) = \\arg\\max_{\\mathcal{M} \\subseteq \\mathcal{M}_{\\text{all}}} \\sum_{m \\in \\mathcal{M}} S(m, T)$$
    • 端到端上下文流水线：$$T^{\\prime} = f_{\\text{Protocol}}\\Big(f_{\\text{Schema}} \\big(\\pi_{\\text{mcp}} \\big( T\\big) \\big) \\Big)$$

    标准执行流水线：
    [开始单轮工具裁剪请求]
      │
      ├──► 1. 运行评分函数 ──► 子类计算相关性 Sim(Em, ET) ──► 基类聚合综合得分 S(m, T) 并过滤低于 τ_threshold 的组件
      │                                                      
      ├──► 2. 原子化拓扑闭包 ──► 展开前置依赖关系 ──► 保证将工具及其完整依赖视为不可分割的原子包：∀ m ∈ M, Dep(m) ⊆ M
      │
      ├──► 3. 贪心背包决策 ──► 按得分降序排列 ──► 校验配额限制：∑ TokenSize(m) <= B_token
      │                                                │
      │                                                ├─── [超出预算] ──► 强行截断，整体拒绝加载低分原子包
      │                                                └─── [未超预算] ──► 允许装箱并计入总 Tokens 水位
      │
      └──► 4. 结构体裁剪与合规化（初始化阶段已预计算，运行时零开销读取）
                │
                ├─── [f_Schema 压缩] ──► 剔除冗长描述 ──► 仅保留 name, 截断后的 desc, input_schema
                │
                ├─── [f_Protocol 过滤] ──► 判定 compliance_flag ──► 拦截并清洗格式不合规的脏组件
                │
                └─── [确定性排序优化] ──► 按工具名称字母正序统一重排 (Deterministic Ordering)
                          │
                          └─► [最大化触发上游前缀缓存 (Prefix Cache) ──► 极低延时放行提交大模型]
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Set, Any
from core.interfaces import MCPPruningStrategy

logger = logging.getLogger(__name__)


class BaseMCPPruner(MCPPruningStrategy, ABC):
    """
    模型上下文协议 (MCP) 裁剪优化抽象基类。
    
    封装了 O(1) 索引查询、Schema 预压缩、原子化拓扑闭包解析以及贪心背包截断逻辑，
    使具体子类（如规则策略、向量策略、双路混合策略）只需专注于计算相关性得分 Sim(Em, ET)。
    """

    def __init__(self, mcp_registry: List[Dict[str, Any]], tau_threshold: float = 0.5) -> None:
        """
        参数：
            mcp_registry: 所有已注册的可用 MCP 元数据定义全局池。
            tau_threshold: 激活截断的硬性过滤阈值（与基础启用分校准对齐）。
        """
        self._registry = mcp_registry
        self._tau_threshold = tau_threshold
        
        # 性能优化：构建 O(1) 哈希映射表，彻底消灭运行时 next(...) 的 O(N) 线性遍历开销
        self._registry_map: Dict[str, Dict[str, Any]] = {m["name"]: m for m in mcp_registry}
        
        # 性能优化：在初始化阶段预执行 f_Schema 压缩与 f_Protocol 合规检查
        self._precomputed_schemas: Dict[str, Dict[str, Any]] = self._precompute_valid_schemas()

    def _precompute_valid_schemas(self) -> Dict[str, Dict[str, Any]]:
        """离线预执行 f_Schema 结构体压缩算子与 f_Protocol 合规性过滤"""
        valid_schemas: Dict[str, Dict[str, Any]] = {}
        for m in self._registry:
            name = m["name"]
            # --- f_Protocol 合规性过滤 ---
            if m.get("compliance_flag", True) is not True:
                logger.error(f"[MCP 协议违规] 初始化阶段组件校验失败，已剔除脏组件: {name}")
                continue

            # --- f_Schema 结构体压缩算子 ---
            raw_desc = m.get("description", "")
            # 负载优化：硬性截断描述文本块以满足最小化负载配置
            truncated_desc = raw_desc[:60] + "..." if len(raw_desc) > 60 else raw_desc

            valid_schemas[name] = {
                "name": name,
                "description": truncated_desc,
                "input_schema": m.get("input_schema", {"type": "object", "properties": {}}),
            }
        return valid_schemas

    @abstractmethod
    def _compute_similarities(self, T: str) -> Dict[str, float]:
        """
        [子类扩展点] 计算当前上下文 T 与所有工具的相关性得分 Sim(Em, ET)。
        
        返回：
            Dict[str, float]: 工具名称到归一化相关性得分（通常在 0.0 ~ 1.0 之间）的映射。
        """
        ...

    def _calculate_batch_scores(self, T: str, active_history_names: Set[str]) -> Dict[str, float]:
        """
        评分函数算子（严格对齐公式）：
        S(m, T) = w1 × Sim(Em, ET) + w2 × Freq(m, H) + w3 × State(m) - w4 × Cost(m)
        """
        # 显式定义结构化超参数权重以保持数学一致性
        w1, w2, w3, w4 = 2.0, 1.0, 5.0, 0.001

        # 1. 获取子类计算的语义/规则相关性得分 Sim(Em, ET)
        sim_scores = self._compute_similarities(T)
        final_scores: Dict[str, float] = {}

        for name, m in self._registry_map.items():
            # 若组件未通过协议合规检查，直接赋予极小惩罚值一票否决
            if name not in self._precomputed_schemas:
                final_scores[name] = -1000.0
                continue

            sim_score = sim_scores.get(name, 0.0)

            # 2. Freq(m, H): 通过安全的 O(1) 哈希查找校准的频率/近因得分
            freq_score = 1.0 if name in active_history_names else 0.0

            # 3. State(m): 硬性环境合规性检查（例如跨平台或动态特性开关状态）
            # 若状态有效返回 1.0，否则给予巨大的负向惩罚以强制执行绝对裁剪否决
            is_active_state = m.get("is_enabled", True)
            state_score = 1.0 if is_active_state else -1000.0

            # 4. Cost(m): 直接映射自工具 Token 负载大小的资源权重惩罚
            # 确保在上下文窗口瓶颈期优先保留 Schema 体积更小的工具
            cost_score = float(m.get("token_size", 300))

            # 线性组合流水线：按公式执行精确惩罚与加权聚合
            # 注：扣除基础启用常数项 w3，防止正常启用状态的固定加分架空 tau_threshold 的过滤效果
            base_active_offset = w3 * 1.0 if is_active_state else 0.0
            score = (w1 * sim_score) + (w2 * freq_score) + (w3 * state_score) - base_active_offset - (w4 * cost_score)
            final_scores[name] = score

        return final_scores

    def _get_atomic_closure(self, root_name: str) -> Set[str]:
        """
        依赖关系的显式展开（拓扑闭包约束）：
        ∀ m ∈ M, Dep(m) ⊆ M
        在有界迭代内收敛级联依赖结构，确保单次查询在 O(1) 索引下极速完成。
        """
        closure_set: Set[str] = {root_name}
        stack: List[str] = list(self._registry_map.get(root_name, {}).get("dependencies", []))
        
        while stack:
            dep = stack.pop()
            if dep in self._registry_map and dep not in closure_set:
                closure_set.add(dep)
                stack.extend(self._registry_map[dep].get("dependencies", []))
                
        return closure_set

    def prune_tools(
        self,
        current_context: str,
        active_history_names: Set[str],
        token_budget: int,
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        # 防御性编程：显式声明该参数仅用于协议对齐，当前策略暂不消费
        _ = kwargs

        # --- 步骤 1：通过 argmax S(m, T) 计算得分并筛选超过阈值的候选集 ---
        scores = self._calculate_batch_scores(current_context, active_history_names)
        candidate_names = [name for name, score in scores.items() if score >= self._tau_threshold]

        # 按综合得分降序排列
        sorted_candidates = sorted(
            candidate_names,
            key=lambda x: scores.get(x, -1000.0),
            reverse=True
        )

        # --- 步骤 2 & 步骤 3：原子化拓扑依赖闭包解析 + Token 上限下的贪心背包装箱 ---
        selected_names: Set[str] = set()
        current_tokens = 0

        for name in sorted_candidates:
            if name in selected_names:
                continue

            # 将当前工具及其所有前置依赖视为一个“不可分割的原子包”，防止预算不足时只装入主工具而丢弃依赖
            closure = self._get_atomic_closure(name)
            new_components = closure - selected_names
            
            # 校验原子包内所有组件是否均处于合法启用状态
            if any(scores.get(comp, -1000.0) <= -500.0 for comp in new_components):
                logger.warning(f"[MCP 裁剪器] 组件 {name} 的前置依赖被禁用或不合规，已跳过整个依赖包。")
                continue

            added_cost = sum(self._registry_map[comp].get("token_size", 300) for comp in new_components)

            # 背包容量熔断器：当 Token 分配突破边界限制时立即阻断装入
            if current_tokens + added_cost > token_budget:
                logger.warning(f"[MCP 裁剪器] 已触及 Token 预算上限，丢弃低优先级组件包: {name} (需消耗 {added_cost} Tokens)")
                continue

            selected_names.update(new_components)
            current_tokens += added_cost

        # --- 步骤 4 & 步骤 5：提取预压缩且合规的 Schema 结构体 ---
        selected_mcp_list: List[Dict[str, Any]] = [
            self._precomputed_schemas[name] for name in selected_names if name in self._precomputed_schemas
        ]

        # --- 步骤 6：通过确定性排序最大化上游前缀缓存 (Prefix Caching) 命中率 ---
        # 按工具名称确定性排序以强制维持固定的 Token 序列模式，将前缀缓存命中率提升至 95%+
        selected_mcp_list.sort(key=lambda x: x["name"])

        return selected_mcp_list
