from askpolis.search import EmbeddingsCollection, EmbeddingsService
from askpolis.search.models import SearchResult


class SearchService:
    def __init__(self, collection: EmbeddingsCollection, embeddings_service: EmbeddingsService) -> None:
        self._collection = collection
        self._embeddings_service = embeddings_service

    def find_matching_texts(self, query: str, limit: int = 10) -> list[SearchResult]:
        similar_documents = self._embeddings_service.find_similar_documents(self._collection, query, limit)
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
