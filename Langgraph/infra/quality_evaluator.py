# /infra/quality_evaluator.py
from typing import Awaitable, Callable, Dict, Generic, Hashable, Optional, TypeVar
from protocols.evaluation import QualityEvaluatorProtocol

ItemT = TypeVar("ItemT")

HeuristicRuleFn = Callable[[ItemT], Optional[float]]
TextExtractorFn = Callable[[ItemT], str]
RoutingKeyFn = Callable[[ItemT], Optional[Hashable]]
SemanticScorerFn = Callable[[ItemT], Awaitable[float]]


def _default_extract_text(item: object) -> str:
    if isinstance(item, str):
        return item
    for attr in ("information", "content", "text", "page_content"):
        val = getattr(item, attr, None)
        if isinstance(val, str):
            return val
    return str(item)


class TwoStageQualityEvaluator(QualityEvaluatorProtocol[ItemT], Generic[ItemT]):
    """
    组合式两级信息质量评估器（零继承、直接实现 QualityEvaluatorProtocol）：
    L1（前置长度拦截 + 路由规则快筛，零 Token 消耗） -> L2（异步语义深度评分） -> 分值钳制
    """

    def __init__(
        self,
        semantic_scorer: SemanticScorerFn[ItemT],
        *,
        min_valid_length: int = 15,
        text_extractor: TextExtractorFn[ItemT] = _default_extract_text,
        routing_key_resolver: Optional[RoutingKeyFn[ItemT]] = None,
        default_heuristic: Optional[HeuristicRuleFn[ItemT]] = None,
        heuristic_rules: Optional[Dict[Hashable, HeuristicRuleFn[ItemT]]] = None,
    ) -> None:
        if min_valid_length < 0:
            raise ValueError("min_valid_length 不能为负数")
        self._semantic_scorer = semantic_scorer
        self._min_valid_length = min_valid_length
        self._extract_text = text_extractor
        self._resolve_routing_key = routing_key_resolver
        self._default_heuristic = default_heuristic
        # 实例级隔离注册表（彻底告别 ClassVar 与 __init_subclass__ 黑魔法）
        self._rules: Dict[Hashable, HeuristicRuleFn[ItemT]] = dict(heuristic_rules or {})

    def register_rule(self, key: Hashable, fn: HeuristicRuleFn[ItemT]) -> "TwoStageQualityEvaluator[ItemT]":
        """支持实例级链式注册快筛规则，遵守 OCP"""
        self._rules[key] = fn
        return self

    async def evaluate(self, item: ItemT) -> float:
        text = self._extract_text(item).strip()
        if len(text) < self._min_valid_length:
            return 0.0

        routing_key = self._resolve_routing_key(item) if self._resolve_routing_key else None
        rule_fn = self._rules.get(routing_key) if routing_key is not None else None

        fast_score = (
            rule_fn(item)
            if rule_fn is not None
            else (self._default_heuristic(item) if self._default_heuristic else None)
        )
        if fast_score is not None:
            return self._clamp_score(fast_score)

        semantic_score = await self._semantic_scorer(item)
        return self._clamp_score(semantic_score)

    @staticmethod
    def _clamp_score(score: float) -> float:
        return max(0.0, min(1.0, float(score)))
