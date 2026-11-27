# /components/internal_knowledge/acquisition/composite_acquirer.py
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple, runtime_checkable

from components.internal_knowledge.schemas.information import Information
from components.internal_knowledge.schemas.pipeline_envelope import PipelineEnvelope
from components.internal_knowledge.schemas.source_uri import SourceScheme, SourceURI
from components.internal_knowledge.protocols import GapRoutingProtocol, KnowledgeAcquisitionProtocol
from infra import emit_component_status, KnowledgePipelineError
from infra.exceptions import KnowledgePipelineError

logger = logging.getLogger(__name__)

# 复合路由键类型：(协议枚举, 文件后缀如 '.sh' 或通配符 '*')
CompositeRouteKey = Tuple[SourceScheme, str]


@runtime_checkable
class SourceHandlerProtocol(Protocol):
    """单个采集源处理器的最小行为契约（零基类继承，实现即用）"""

    async def fetch_and_slice(
        self, uri: SourceURI, envelope: PipelineEnvelope
    ) -> List[Information]:
        """针对单个强类型 SourceURI 执行 I/O 读取与切片，返回原子 Information 列表"""
        ...


class CompositeKnowledgeAcquirer(KnowledgeAcquisitionProtocol):
    """
    组合式知识采集调度器（实现 KnowledgeAcquisitionProtocol）：
    - 实例级复合路由表：支持 (SourceScheme, suffix) 精确匹配与 (SourceScheme, "*") 通配符兜底；
    - 组合缺口路由器（GapRoutingProtocol）：当未显式指定 source_locators 时自动触发缺口路由定位；
    - 并发控制与异常隔离：支持信号量限流与单源超时控制；原生模型/网络异常直接向上透传给恢复节点。
    """

    def __init__(
        self,
        gap_router: Optional[GapRoutingProtocol] = None,
        handlers: Optional[Dict[CompositeRouteKey, SourceHandlerProtocol]] = None,
        max_concurrency: int = 5,
        handler_timeout_seconds: Optional[float] = None,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency 必须 >= 1")
        if handler_timeout_seconds is not None and handler_timeout_seconds <= 0:
            raise ValueError("handler_timeout_seconds 必须 > 0")

        self._gap_router = gap_router
        self._handlers: Dict[CompositeRouteKey, SourceHandlerProtocol] = dict(handlers or {})
        self._max_concurrency = max_concurrency
        self._handler_timeout_seconds = handler_timeout_seconds

    def register(
        self,
        scheme: SourceScheme,
        handler: SourceHandlerProtocol,
        suffix: str = "*",
    ) -> "CompositeKnowledgeAcquirer":
        """链式注册采集处理器（suffix 默认为 '*' 表示该协议下的通用兜底处理器）"""
        norm_suffix = suffix.lower() if suffix.startswith(".") or suffix == "*" else f".{suffix.lower()}"
        self._handlers[(scheme, norm_suffix)] = handler
        return self

    def _resolve_handler(self, uri: SourceURI) -> Optional[SourceHandlerProtocol]:
        """两级路由查找：(scheme, 精确扩展名) -> (scheme, '*') 通用兜底"""
        target_str = uri.subpath or uri.location or ""
        ext = Path(target_str).suffix.lower()
        if ext:
            exact_handler = self._handlers.get((uri.scheme, ext))
            if exact_handler is not None:
                return exact_handler
        return self._handlers.get((uri.scheme, "*"))

    async def acquire(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """统一异步采集入口：解析目标定位符 -> 并发复合键路由切片 -> 不可变更新 PipelineEnvelope"""
        pipeline_start = time.perf_counter()
        target_uris = await self._resolve_target_uris(envelope)
        total = len(target_uris)

        logger.info(
            "[CompositeAcquirer] 开始知识采集 (trace_id=%s, target_count=%d, concurrency=%d)",
            envelope.trace_id,
            total,
            self._max_concurrency,
        )
        emit_component_status(f"【采集阶段】开始处理 {total} 个数据源...\n")

        semaphore = asyncio.Semaphore(self._max_concurrency)

        async def _fetch_one(
            idx: int, uri: SourceURI
        ) -> Tuple[List[Information], Optional[str]]:
            handler = self._resolve_handler(uri)
            display_target = uri.subpath or uri.location
            if handler is None:
                reason = f"暂不支持 '{uri.scheme.value}' 协议的数据源（{display_target}）"
                logger.warning("[CompositeAcquirer] %s (trace_id=%s)", reason, envelope.trace_id)
                return [], reason

            async with semaphore:
                t0 = time.perf_counter()
                emit_component_status(
                    f"【采集阶段】 ({idx}/{total}) 正在采集与切片 [{uri.scheme.value}]: {display_target}...\n"
                )
                try:
                    coro = handler.fetch_and_slice(uri, envelope)
                    if self._handler_timeout_seconds is not None:
                        slices = await asyncio.wait_for(coro, timeout=self._handler_timeout_seconds)
                    else:
                        slices = await coro

                    logger.debug(
                        "[CompositeAcquirer] 单源采集完成 (trace_id=%s, target=%s): 切片数=%d, 耗时=%.2fs",
                        envelope.trace_id,
                        display_target,
                        len(slices),
                        time.perf_counter() - t0,
                    )
                    emit_component_status(f"【采集阶段】提取出 {len(slices)} 条原子知识切片。\n")
                    return slices, None
                except asyncio.TimeoutError:
                    reason = f"采集数据源 '{display_target}' 超时（>{self._handler_timeout_seconds}s）"
                    logger.warning("[CompositeAcquirer] %s (trace_id=%s)", reason, envelope.trace_id)
                    return [], reason
                except Exception as exc:
                    reason = f"采集数据源 '{display_target}' 失败: {exc}"
                    logger.warning("[CompositeAcquirer] %s (trace_id=%s)", reason, envelope.trace_id)
                    return [], reason

        results = await asyncio.gather(
            *(_fetch_one(idx, uri) for idx, uri in enumerate(target_uris, start=1))
        )

        collected_infos: List[Information] = []
        failed_reasons: List[str] = []
        for slices, err in results:
            collected_infos.extend(slices)
            if err:
                failed_reasons.append(err)

        # 若所有数据源均失败且未获得任何切片，抛出可解释的业务异常交由恢复责任链引导用户
        if not collected_infos and failed_reasons:
            summary_msg = "；".join(failed_reasons)
            emit_component_status(f"【采集阶段】采集未成功：{summary_msg}\n")
            raise KnowledgePipelineError(
                message=f"知识采集失败：{summary_msg}",
                stage="acquisition",
                metadata={"trace_id": envelope.trace_id, "failed_reasons": failed_reasons},
            )

        # 全部数据源均未报错但未提取出任何有效文本（如全为空文件或纯二进制文件）
        if not collected_infos and not envelope.raw_infos:
            msg = "目标数据源中未提取到任何有效文本切片（可能为空文件、纯二进制文件或长度不足）。"
            logger.info("[CompositeAcquirer] %s (trace_id=%s)", msg, envelope.trace_id)
            emit_component_status(f"【采集阶段】{msg}\n")
            raise KnowledgePipelineError(
                message=msg,
                stage="acquisition",
                user_friendly_hint=msg,
                metadata={"trace_id": envelope.trace_id, "target_count": total},
            )

        merged_infos_map: Dict[str, Information] = {
            info.info_id: info for info in (*envelope.raw_infos, *collected_infos)
        }
        elapsed = time.perf_counter() - pipeline_start
        logger.info(
            "[CompositeAcquirer] 采集阶段闭环完成 (trace_id=%s): 耗时=%.2fs, 成功源=%d/%d, 新增切片=%d, 累计切片=%d",
            envelope.trace_id,
            elapsed,
            total - len(failed_reasons),
            total,
            len(collected_infos),
            len(merged_infos_map),
        )
        emit_component_status(
            f"【采集阶段】本轮累计获得 {len(collected_infos)} 条新切片（当前共 {len(merged_infos_map)} 条）。\n"
        )
        return envelope.model_copy(
            update={
                "source_locators": [],
                "raw_infos": list(merged_infos_map.values()),
            }
        )

    async def _resolve_target_uris(self, envelope: PipelineEnvelope) -> List[SourceURI]:
        """确定本轮需要采集的强类型 SourceURI 列表（原生模型/网络异常直接向上透传）"""
        if envelope.source_locators:
            return list(envelope.source_locators)

        resolution = envelope.problem_resolution
        if not (resolution and resolution.remaining_gap):
            msg = "知识采集失败：未指定待采集的数据源路径，且当前问题无明确的知识缺口描述。"
            logger.warning("[CompositeAcquirer] %s (trace_id=%s)", msg, envelope.trace_id)
            raise KnowledgePipelineError(message=msg, stage="gap_routing")

        if self._gap_router is None:
            msg = "知识采集失败：系统未配置缺口数据源路由器，无法自动检索待学习文件。"
            logger.warning("[CompositeAcquirer] %s (trace_id=%s)", msg, envelope.trace_id)
            raise KnowledgePipelineError(message=msg, stage="gap_routing")

        t0 = time.perf_counter()
        # 不在此处捕获原生模型/网络异常，直接透传给 DEFAULT_EXCEPTION_SPECS 对应的恢复节点
        routed_uris = await self._gap_router.route(
            gap_description=resolution.remaining_gap,
            problem_context=resolution.problem,
        )
        logger.info(
            "[CompositeAcquirer] 缺口路由完成 (trace_id=%s): 耗时=%.2fs, 命中数据源=%d",
            envelope.trace_id,
            time.perf_counter() - t0,
            len(routed_uris),
        )

        if not routed_uris:
            msg = f"未能在当前工作区找到与「{resolution.remaining_gap}」匹配的文档或代码文件，请直接指定文件路径。"
            emit_component_status(f"【采集阶段】{msg}\n")
            logger.warning(
                "[CompositeAcquirer] 缺口路由返回空列表 (trace_id=%s, gap='%s')",
                envelope.trace_id,
                resolution.remaining_gap,
            )
            raise KnowledgePipelineError(
                message=msg,
                stage="gap_routing",
                metadata={"trace_id": envelope.trace_id, "remaining_gap": resolution.remaining_gap},
            )

        return routed_uris
