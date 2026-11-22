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
    def generate_info_id(
        uri: SourceURI,
        slice_identity: Optional[str] = None,
        fallback_content: str = "",
    ) -> str:
        """基于【稳定逻辑位置 + 切片局部身份指纹】生成确定性且全局唯一的 info_id（格式：info_<16位hex>）。

        设计权衡：
            1. 剔除易变的 revision 与纯行号，保障增量更新时原地覆盖、不产生僵尸切片。
            2. 引入 slice_identity（如 AST 符号名 'func:login'、章节路径 'sec:1.2' 或滑窗序号 'chunk:0'），
               彻底解决单个大文件切出多条 Information 时 info_id 撞车覆盖的问题。
        """
        # 1. 提取文档级稳定逻辑根路径
        if uri.scheme == SourceScheme.REPO:
            stable_base = f"repo:{uri.location}#{uri.subpath or ''}"
        else:
            stable_base = f"{uri.scheme.value}:{uri.location}"
        # 2. 叠加非纯行号的语义锚点（如 uri 自带的 func:xxx 或 page=12）
        if uri.anchor and not uri.anchor.startswith("L"):
            stable_base = f"{stable_base}#{uri.anchor}"
        # 3. 叠加切片级局部身份指纹（解决一源多切片唯一性）
        if slice_identity:
            stable_base = f"{stable_base}@{slice_identity.strip()}"
        elif fallback_content:
            # 兜底策略：若子类既未提供语义锚点也未传 slice_identity，截取前 128 字符作为局部指纹防止撞车
            stable_base = f"{stable_base}@fallback:{fallback_content[:128]}"
        # 升级为 16 位 hex（64-bit 空间），降低在海量切片下碰撞概率
        digest = hashlib.sha256(stable_base.encode("utf-8")).hexdigest()[:16]
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

        # 按 info_id合并（Upsert）：避免多源同内容重叠，保留原有顺序，本轮新采集的同ID切片自动覆盖旧切片
        merged_infos_map: Dict[str, Information] = {
            info.info_id: info for info in (*envelope.raw_infos, *collected_infos)
        }
        return envelope.model_copy(
            update={
                "source_locators": [],
                "raw_infos": list(merged_infos_map.values()),
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
