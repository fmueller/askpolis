from FlagEmbedding import FlagReranker

from askpolis.logging import get_logger
from askpolis.search import Embeddings

logger = get_logger(__name__)


class RerankerService:
    def __init__(self) -> None:
        self._reranker = FlagReranker("BAAI/bge-reranker-v2-m3")

    def rerank(self, query: str, embeddings: list[Embeddings], limit: int = 10) -> list[tuple[Embeddings, float]]:
        if len(embeddings) == 0:
            return []

        if len(embeddings) > limit:
            limit = len(embeddings)

        logger.info("Reranking...")
        reranked_scores = self._reranker.compute_score([(query, doc.chunk) for doc in embeddings], normalize=True)
        return [(doc, float(score)) for score, doc in sorted(zip(reranked_scores, embeddings), reverse=True)][:limit]
