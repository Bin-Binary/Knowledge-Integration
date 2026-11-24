# /components/routing/router.py
import logging
from typing import Optional

from protocols import RouterProtocol
from schemas import (
    IntentResult,
    RouteDecision,
    FallbackPlan,
    FallbackTrigger,
    RouteContext,
    RouteCatalog,
)
from infra import log_execution

logger = logging.getLogger(__name__)


class CatalogRouter(RouterProtocol):
    """基于 RouteCatalog 配置的确定性路由调度器"""

    def __init__(self, catalog: RouteCatalog) -> None:
        self._catalog = catalog

    @log_execution("CatalogRouter.dispatch")
    async def dispatch(
        self, context: RouteContext, intent: Optional[IntentResult]
    ) -> RouteDecision:
        _ = context
        default_node = self._catalog.default_fallback_node

        # 1. 兜底分支 A：上游意图识别返回空
        if intent is None:
            logger.info("[CatalogRouter] Missing intent, routing to default fallback: %s", default_node)
            return RouteDecision(
                target_node=default_node,
                params={
                    "target_domain": "execution",
                    "skip_knowledge": True,
                },
                confidence=0.0,
                reason="未识别到明确意图，路由至默认兜底节点",
                fallback_plan=FallbackPlan(
                    trigger=FallbackTrigger.NONE,
                    fallback_node=default_node,
                ),
            )

        intent_name = intent.intent
        confidence = intent.confidence
        spec = self._catalog.routes.get(intent_name)

        # 2. 兜底分支 B：意图未命中配置路由表
        if spec is None:
            logger.warning("[CatalogRouter] Unmapped intent '%s', falling back to %s", intent_name, default_node)
            return RouteDecision(
                target_node=default_node,
                params={
                    "target_domain": "execution",
                    "intent": intent_name,
                    "skip_knowledge": True,                    
                    **intent.slots,
                },
                confidence=confidence,
                reason=f"意图 [{intent_name}] 未配置专属路由，降级至默认节点",
                fallback_plan=FallbackPlan(
                    trigger=FallbackTrigger.NODE_UNAVAILABLE,
                    fallback_node=default_node,
                ),
            )

        effective_fallback = spec.fallback_node or default_node

        # 3. 守卫分支 C：置信度低于阈值，触发降级分流
        if confidence < self._catalog.min_confidence_threshold:
            logger.info(
                "[CatalogRouter] Low confidence (%.2f < %.2f) for '%s', routing to fallback '%s'",
                confidence,
                self._catalog.min_confidence_threshold,
                intent_name,
                effective_fallback,
            )
            return RouteDecision(
                target_node=effective_fallback,
                params={
                    "target_domain": "execution",
                    "original_intent": intent_name,
                    "original_target": spec.target_node,
                    "skip_knowledge": True,
                    **intent.slots,
                },
                confidence=confidence,
                reason=f"意图 [{intent_name}] 置信度 ({confidence:.2f}) 低于阈值，触发降级分流",
                fallback_plan=FallbackPlan(
                    trigger=FallbackTrigger.LOW_CONFIDENCE,
                    fallback_node=effective_fallback,
                    clarification_prompt="抱歉，我不太确定您的具体需求，能否请您再补充说明一下？",
                ),
            )

        # 4. 正常匹配分支
        logger.debug(
            "[CatalogRouter] Dispatched intent '%s' -> domain='%s', target_node='%s'",
            intent_name,
            spec.target_domain,
            spec.target_node,
        )
        return RouteDecision(
            target_node=spec.target_node,
            params={
                "target_domain": spec.target_domain,
                "skip_knowledge": spec.skip_knowledge,
                "intent": intent_name,
                **intent.slots,
            },
            confidence=confidence,
            reason=f"命中路由规则: {intent_name} -> {spec.target_node}",
            fallback_plan=FallbackPlan(
                trigger=FallbackTrigger.NONE,
                fallback_node=effective_fallback,
            ),
        )
