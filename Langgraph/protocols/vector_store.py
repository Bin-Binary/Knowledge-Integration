from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from schemas.base import ImmutableSchema

class VectorDocument(ImmutableSchema):
    """通用向量入库单元"""
    id: str
    text: str
    vector: List[float]
    payload: Dict[str, Any] = {}

class VectorSearchHit(ImmutableSchema):
    """通用向量检索命中结果"""
    id: str
    score: float
    payload: Dict[str, Any]

@runtime_checkable
class EmbeddingProviderProtocol(Protocol):
    """文本向量化协议"""
    @property
    def dimension(self) -> int: ...

    def embed_text(self, text: str) -> List[float]: ...

    def embed_batch(self, texts: List[str]) -> List[List[float]]: ...

@runtime_checkable
class VectorStoreProtocol(Protocol):
    """通用向量存储与前置过滤检索协议"""
    def ensure_collection(self, collection_name: str, dimension: int) -> None: ...

    def upsert(self, collection_name: str, documents: List[VectorDocument]) -> None: ...

    def delete_by_filter(self, collection_name: str, filters: Dict[str, Any]) -> None: ...

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[VectorSearchHit]: ...
