# /protocols/evaluation.py
from typing import Protocol, TypeVar, runtime_checkable

# 定义逆变泛型参数，允许评估任何类型的输入对象（Information、Message、str 等）
ItemT_contra = TypeVar("ItemT_contra", contravariant=True)

@runtime_checkable
class QualityEvaluatorProtocol(Protocol[ItemT_contra]):
    """通用信息/数据质量评估协议（高度泛化，支持多业务域复用）。

    可用于：
        1. 域内知识库【组织】环节（3.1 评估过滤 Information 切片）。
        2. 上下文滑动窗口压缩前的历史消息价值评估（Message）。
        3. RAG 召回文档的重排序过滤（Document）。
    """

    async def evaluate(self, item: ItemT_contra) -> float:
        """评估单个数据单元的信息密度或质量分值，返回 [0.0, 1.0] 标量。"""
        ...
