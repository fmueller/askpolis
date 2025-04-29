from abc import ABC, abstractmethod
from typing import Optional

from askpolis.search import EmbeddingsCollectionRepository, EmbeddingsService, SearchResult
from askpolis.search.reranker_service import RerankerService


class SearchServiceBase(ABC):
    @abstractmethod
    def find_matching_texts(self, query: str, limit: int = 5, use_reranker: bool = False) -> list[SearchResult]:
        """Search for texts matching the query."""
        pass


class SearchService(SearchServiceBase):
    def __init__(
        self,
        collections_repository: EmbeddingsCollectionRepository,
        embeddings_service: EmbeddingsService,
        reranker_service: RerankerService,
    ) -> None:
        self._collections_repository = collections_repository
        self._embeddings_service = embeddings_service
        self._reranker_service = reranker_service

    def find_matching_texts(
        self, query: str, limit: int = 10, use_reranker: bool = False, indexes: Optional[list[str]] = None
    ) -> list[SearchResult]:
        if indexes is None:
            indexes = ["default"]
        if limit < 1:
            return []

        query_limit = limit * 2 if use_reranker else limit
        similar_documents = [
            result
            for index in indexes
            for result in self._embeddings_service.find_similar_documents(
                self._collections_repository.get_most_recent_by_name(index), query, query_limit
            )
        ]

        if use_reranker:
            similar_documents = self._reranker_service.rerank(query, [e for e, _ in similar_documents], limit)

        return [
            SearchResult(
                matching_text=result.chunk,
                chunk_id=result.id,
                document_id=result.document_id,
                page_id=result.page_id,
                score=score,
            )
            for result, score in similar_documents
        ]
