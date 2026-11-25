from typing import List
from sentence_transformers import SentenceTransformer
from protocols.vector_store import EmbeddingProviderProtocol

class LocalSentenceEmbedder(EmbeddingProviderProtocol):
    """基于开源 sentence-transformers 的本地向量化实现"""

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5", device: str = "cpu"):
        self._model = SentenceTransformer(model_name, device=device)
        self._dim = self._model.get_sentence_embedding_dimension()

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return self._model.encode(texts, normalize_embeddings=True).tolist()
