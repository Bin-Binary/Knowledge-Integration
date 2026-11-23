# /components/internal_knowledge/acquisition/base_gap_router.py
from abc import ABC, abstractmethod
from typing import List
from schemas.internal_knowledge import SourceURI
from protocols import GapRoutingProtocol

class BaseGapRouter(ABC, GapRoutingProtocol):
    """2.1 【采集前置子协议】缺口路由算子抽象基类（实现 GapRoutingProtocol）。

    核心职能：
        1. 前置空值拦截与上下文规整。
        2. 委托子类执行路由推理（如 LLM 意图识别、目录索引匹配、知识图谱邻域探测）。
        3. 对子类产出的 SourceURI 列表进行去重保序（防止同轮重复采集同一数据源）。
    """

    async def route(self, gap_description: str, problem_context: str) -> List[SourceURI]:
        """统一路由入口：前置校验 -> 异步推理定位 -> 结果去重"""
        clean_gap = (gap_description or "").strip()
        if not clean_gap:
            return []

        raw_uris = await self._infer_target_uris(
            gap_description=clean_gap,
            problem_context=(problem_context or "").strip(),
        )

        # 按规范化 URI 字符串去重，保留推理优先级顺序
        deduped_uris: List[SourceURI] = []
        seen: set[str] = set()
        for uri in raw_uris:
            key = uri.model_dump_json()
            if key not in seen:
                seen.add(key)
                deduped_uris.append(uri)

        return deduped_uris

    @abstractmethod
    async def _infer_target_uris(
        self, gap_description: str, problem_context: str
    ) -> List[SourceURI]:
        """子类必须实现的核心路由逻辑：将自然语言缺口映射为强类型 SourceURI 列表。"""
        ...
