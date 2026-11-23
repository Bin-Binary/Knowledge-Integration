# /components/_shared/base_evaluator.py
import logging
from abc import ABC, abstractmethod
from typing import Callable, ClassVar, Dict, Generic, Hashable, Optional, TypeVar

from protocols import QualityEvaluatorProtocol

logger = logging.getLogger(__name__)

# 泛型输入对象（如 Information、Message、str 等）
ItemT = TypeVar("ItemT")

# 第一级规则快筛函数签名：
# - 返回 float [0.0, 1.0]：命中明确噪声或高价值特征，直接短路返回分值（零 Token 消耗）
# - 返回 None：规则无法定夺，放行至第二级语义深度评分
HeuristicRuleFn = Callable[[ItemT], Optional[float]]

class BaseQualityEvaluator(ABC, QualityEvaluatorProtocol[ItemT], Generic[ItemT]):
    """通用两级信息质量评估抽象基类（实现 QualityEvaluatorProtocol[ItemT]）。

    设计模式：模板方法模式（Template Method） + 策略路由注册表（Strategy Registry）
    执行漏斗：
        1. 文本提取与前置空值拦截（Hook: `_extract_text`）
        2. 第一级启发式规则快筛（按 `_resolve_routing_key` 路由专属策略，未命中则走 `_default_heuristic_check`）
        3. 第二级深度语义评估（抽象方法: `_semantic_score`，如调用结构化 LLM 打分）
        4. 分值归一化保护（强制钳制在 [0.0, 1.0] 合法区间）
    """

    # 子类可覆盖独立的策略注册表（默认每个子类拥有隔离的路由表，防止不同业务域规则互相污染）
    _heuristic_registry: ClassVar[Dict[Hashable, HeuristicRuleFn]] = {}

    def __init_subclass__(cls, **kwargs):
        """确保每个继承 BaseQualityEvaluator 的子类拥有独立的策略注册表"""
        super().__init_subclass__(**kwargs)
        if "_heuristic_registry" not in cls.__dict__:
            cls._heuristic_registry = {}

    def __init__(self, min_valid_length: int = 15):
        """
        Args:
            min_valid_length: 有效文本最小字符长度阈值，低于此长度直接判为 0.0 分噪声。
        """
        if min_valid_length < 0:
            raise ValueError("min_valid_length 不能为负数")
        self.min_valid_length = min_valid_length

    @classmethod
    def register_heuristic(cls, *keys: Hashable):
        """类装饰器：为指定的路由键（如 SourceScheme.REPO、'chat' 等）注册第一级零成本快筛策略"""
        def wrapper(fn: HeuristicRuleFn) -> HeuristicRuleFn:
            for key in keys:
                cls._heuristic_registry[key] = fn
            return fn
        return wrapper

    # ------------------------------------------------------------------
    # 核心模板方法（实现 QualityEvaluatorProtocol 契约）
    # ------------------------------------------------------------------

    async def evaluate(self, item: ItemT) -> float:
        """统一质量评估入口：前置空短文本拦截 -> 第一级规则快筛 -> 第二级语义评分 -> 边界钳制"""
        text = self._extract_text(item).strip()
        if len(text) < self.min_valid_length:
            return 0.0

        # 第一级：路由匹配专属快筛规则（若无专属规则，降级执行通用默认钩子）
        routing_key = self._resolve_routing_key(item)
        rule_fn = self._heuristic_registry.get(routing_key) if routing_key is not None else None

        fast_score = rule_fn(item) if rule_fn is not None else self._default_heuristic_check(item)
        if fast_score is not None:
            return self._clamp_score(fast_score)

        # 第二级：通过快筛的高潜内容，交由子类执行深度语义评估
        semantic_score = await self._semantic_score(item)
        return self._clamp_score(semantic_score)

    # ------------------------------------------------------------------
    # 钩子方法（Hook Methods：子类按需重写以适配不同数据模型）
    # ------------------------------------------------------------------

    def _extract_text(self, item: ItemT) -> str:
        """钩子 1：从泛型输入对象中提取待评估的纯文本内容（默认兼容 str 及常见文本属性）"""
        if isinstance(item, str):
            return item
        for attr in ("information", "content", "text", "page_content"):
            val = getattr(item, attr, None)
            if isinstance(val, str):
                return val
        return str(item)

    def _resolve_routing_key(self, item: ItemT) -> Optional[Hashable]:
        """钩子 2：提取当前数据的策略路由键（例如知识库子类可重写返回 item.source.scheme）"""
        return None

    def _default_heuristic_check(self, item: ItemT) -> Optional[float]:
        """钩子 3：未命中专属路由规则时的通用兜底快筛逻辑（默认放行至第二级）"""
        return None

    # ------------------------------------------------------------------
    # 抽象扩展点与内部辅助工具
    # ------------------------------------------------------------------

    @abstractmethod
    async def _semantic_score(self, item: ItemT) -> float:
        """子类必须实现的第二级语义评估核心逻辑（如调用 StructuredLLMProtocol 打分）"""
        ...

    @staticmethod
    def _clamp_score(score: float) -> float:
        """防御性边界钳制：确保任何子类或规则返回的分值严格落在 [0.0, 1.0] 闭区间"""
        return max(0.0, min(1.0, float(score)))
