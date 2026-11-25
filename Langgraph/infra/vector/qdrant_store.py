from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, FieldCondition, Filter, MatchAny, MatchValue, PointStruct, Range, VectorParams
)
from protocols.vector_store import VectorDocument, VectorSearchHit, VectorStoreProtocol

class QdrantVectorStore(VectorStoreProtocol):
    """Qdrant 向量数据库适配器（支持本地文件模式与远程服务模式）"""

    def __init__(self, path: Optional[str] = "./data/qdrant_db", url: Optional[str] = None, api_key: Optional[str] = None):
        # 优先使用远程 URL，未配置则降级为本地持久化目录，方便开发起步
        if url:
            self._client = QdrantClient(url=url, api_key=api_key)
        else:
            self._client = QdrantClient(path=path)

    def ensure_collection(self, collection_name: str, dimension: int) -> None:
        if not self._client.collection_exists(collection_name):
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

    def _build_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[Filter]:
        """将领域层传入的通用条件字典翻译为 Qdrant 原生 Filter"""
        if not filters:
            return None
        conditions = []
        for key, val in filters.items():
            if isinstance(val, list):
                conditions.append(FieldCondition(key=key, match=MatchAny(any=val)))
            elif isinstance(val, dict):
                # 支持范围过滤，例如 {"degree": {"$gte": 0.8}}
                conditions.append(
                    FieldCondition(
                        key=key,
                        range=Range(
                            gte=val.get("$gte"),
                            lte=val.get("$lte"),
                            gt=val.get("$gt"),
                            lt=val.get("$lt"),
                        ),
                    )
                )
            else:
                conditions.append(FieldCondition(key=key, match=MatchValue(value=val)))
        return Filter(must=conditions) if conditions else None

    def upsert(self, collection_name: str, documents: List[VectorDocument]) -> None:
        if not documents:
            return
        points = [
            PointStruct(id=doc.id, vector=doc.vector, payload={"_text": doc.text, **doc.payload})
            for doc in documents
        ]
        self._client.upsert(collection_name=collection_name, points=points)

    def delete_by_filter(self, collection_name: str, filters: Dict[str, Any]) -> None:
        q_filter = self._build_filter(filters)
        if q_filter:
            self._client.delete(collection_name=collection_name, points_selector=q_filter)

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[VectorSearchHit]:
        hits = self._client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=self._build_filter(filters),
            limit=top_k,
        ).points
        return [
            VectorSearchHit(id=str(h.id), score=h.score, payload=h.payload or {})
            for h in hits
        ]
