# /components/routing/router.py
import logging
from typing import Optional

from protocols import RouterProtocol
from schemas import (
    IntentResult,
    RouteDecision,
    FallbackPlan,
    RouteContext,
    RouteCatalog,
)
from infra import log_execution, emit_component_status
from infra.exceptions import LowConfidenceIntentError

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
            emit_component_status(
                f"[意图路由]未识别到明确意图，路由至默认兜底节点...\n",
            )
            return RouteDecision(
                target_node=default_node,
                params={
                    "target_domain": "execution",
                    "skip_knowledge": True,
                },
                confidence=0.0,
                reason="未识别到明确意图，路由至默认兜底节点",
                fallback_plan=FallbackPlan(
                    trigger="none",
                    fallback_node=default_node,
                ),
            )

        intent_name = intent.intent
        confidence = intent.confidence
        spec = self._catalog.routes.get(intent_name)

        # 2. 兜底分支 B：意图未命中配置路由表
        if spec is None:
            logger.warning("[CatalogRouter] Unmapped intent '%s', falling back to %s", intent_name, default_node)
            emit_component_status(
                f"[意图路由]意图 [{intent_name}] 未配置专属路由，降级至默认节点...\n",
            )
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
                    trigger="node_unavailable",
                    fallback_node=default_node,
                ),
            )

        effective_fallback = spec.fallback_node or default_node

        # 3. 守卫分支 C：置信度低于阈值，直接抛出业务异常交由恢复责任链反问澄清
        if confidence < self._catalog.min_confidence_threshold:
            logger.info(
                "[CatalogRouter] Low confidence (%.2f < %.2f) for '%s', raising LowConfidenceIntentError.",
                confidence,
                self._catalog.min_confidence_threshold,
                intent_name,
            )
            emit_component_status(
                f"[意图路由]意图 [{intent_name}] 置信度 ({confidence:.2f}) 低于阈值，请求用户澄清...\n"
            )
            raise LowConfidenceIntentError(intent=intent_name, confidence=confidence)

        # 4. 正常匹配分支
        logger.debug(
            "[CatalogRouter] Dispatched intent '%s' -> domain='%s', target_node='%s'",
            intent_name,
            spec.target_domain,
            spec.target_node,
        )
        emit_component_status(
            f"[意图路由]路由命中, 转发中...\n",
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
                trigger="none",
                fallback_node=effective_fallback,
            ),
        )
