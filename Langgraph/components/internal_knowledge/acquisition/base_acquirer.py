# /components/internal_knowledge/acquisition/base_acquirer.py
import hashlib
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, List, Optional, Tuple, Type

from schemas.internal_knowledge.source_uri import SourceScheme, SourceURI
from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope
from protocols.internal_knowledge import KnowledgeAcquisitionProtocol, GapRoutingProtocol

class BaseKnowledgeAcquirer(ABC, KnowledgeAcquisitionProtocol):
    """2. 【采集】环节抽象基类（实现 KnowledgeAcquisitionProtocol）。"""

    _registry: ClassVar[Dict[SourceScheme, Type["BaseKnowledgeAcquirer"]]] = {}

    def __init__(self, gap_router: Optional[GapRoutingProtocol] = None):
        """通过构造函数组合持有独立的缺口路由算子"""
        self.gap_router = gap_router

    @classmethod
    def register(cls, scheme: SourceScheme):
        """类装饰器：将具体协议的采集器注册到路由表中"""
        def wrapper(sub_cls: Type["BaseKnowledgeAcquirer"]) -> Type["BaseKnowledgeAcquirer"]:
            cls._registry[scheme] = sub_cls
            return sub_cls
        return wrapper

    @staticmethod
    def generate_info_id(uri: SourceURI, fallback_content: str = "") -> str:
        """基于稳定逻辑位置生成确定性 info_id（格式：info_<12位hex>）"""
        if uri.scheme == SourceScheme.REPO:
            stable_base = f"repo:{uri.location}#{uri.subpath or ''}"
        else:
            stable_base = f"{uri.scheme.value}:{uri.location}"

        if uri.anchor and not uri.anchor.startswith("L"):
            stable_base = f"{stable_base}#{uri.anchor}"
        elif not uri.anchor and fallback_content:
            stable_base = f"{stable_base}#{fallback_content[:64]}"

        digest = hashlib.sha256(stable_base.encode("utf-8")).hexdigest()[:12]
        return f"info_{digest}"

    @staticmethod
    def parse_line_range(anchor: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
        """通用行号锚点解析器：将 'L42-L68'、'L42-68' 或 'L42' 解析为 (start_line, end_line)"""
        if not anchor or not anchor.startswith("L"):
            return None, None
        parts = anchor[1:].split("-", 1)
        try:
            start = int(parts[0])
            end = int(parts[1].lstrip("L")) if len(parts) > 1 else start
            return start, end
        except ValueError:
            return None, None

    async def acquire(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """统一异步采集入口：解析目标定位符 -> 按协议路由采集 -> 不可变更新PipelineEnvelope"""
        target_uris = await self._resolve_target_uris(envelope)

        collected_infos: List[Information] = []
        handlers_cache: Dict[SourceScheme, BaseKnowledgeAcquirer] = {}

        for uri in target_uris:
            if uri.scheme not in handlers_cache:
                handler_cls = self._registry.get(uri.scheme)
                if not handler_cls:
                    raise NotImplementedError(
                        f"采集路由失败：尚未注册支持 '{uri.scheme.value}' 协议的采集器"
                    )
                handlers_cache[uri.scheme] = handler_cls(gap_router=self.gap_router)

            slices = await handlers_cache[uri.scheme]._fetch_and_slice(uri, envelope)
            collected_infos.extend(slices)

        return envelope.model_copy(
            update={
                "source_locators": [],
                "raw_infos": [*envelope.raw_infos, *collected_infos],
            }
        )

    async def _resolve_target_uris(self, envelope: PipelineEnvelope) -> List[SourceURI]:
        """确定本轮需要采集的强类型 SourceURI 列表"""
        if envelope.source_locators:
            return list(envelope.source_locators)

        resolution = envelope.problem_resolution
        if resolution and resolution.remaining_gap:
            if not self.gap_router:
                raise RuntimeError(
                    "PipelineEnvelope处于缺口驱动模式（存在 remaining_gap），但采集器未注入 GapRoutingProtocol 实例"
                )
            routed_uris = await self.gap_router.route(
                gap_description=resolution.remaining_gap,
                problem_context=resolution.problem,
            )
            if routed_uris:
                return routed_uris

        raise ValueError(
            "采集终止：PipelineEnvelope中既无预设 source_locators，也未能从 remaining_gap 路由出有效数据源"
        )

    @abstractmethod
    async def _fetch_and_slice(self, uri: SourceURI, envelope: PipelineEnvelope) -> List[Information]:
        """子类必须实现的底层异步采集逻辑：针对单个强类型 SourceURI 执行 I/O 读取与符号切片。"""
        ...
