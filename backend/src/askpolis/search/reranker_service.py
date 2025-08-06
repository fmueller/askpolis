import os
from functools import lru_cache

from FlagEmbedding import FlagReranker

from askpolis.logging import get_logger

from .models import Embeddings

logger = get_logger(__name__)


class RerankerService:
    def __init__(self) -> None:
        if os.getenv("DISABLE_INFERENCE") == "true":
            self._reranker = None
        else:
            self._reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=False)

    def rerank(self, query: str, embeddings: list[Embeddings], limit: int = 10) -> list[tuple[Embeddings, float]]:
        if len(embeddings) == 0:
            return []

        if limit > len(embeddings):
            limit = len(embeddings)

        if self._reranker is None:
            logger.warning("No reranker model configured, will return embeddings as is with score of 1.0")
            return [(e, 1.0) for e in embeddings]

        logger.info("Reranking...")
        reranked_scores = self._reranker.compute_score([(query, doc.chunk) for doc in embeddings], normalize=True)
        return [(doc, float(score)) for score, doc in sorted(zip(reranked_scores, embeddings), reverse=True)][:limit]


@lru_cache(maxsize=1)
def get_reranker_service() -> RerankerService:
    return RerankerService()
