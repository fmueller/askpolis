from typing import Any, cast

from FlagEmbedding import BGEM3FlagModel

from askpolis.core import Document, MarkdownSplitter, Page, PageRepository
from askpolis.logging import get_logger
from askpolis.search.models import Embeddings, EmbeddingsCollection
from askpolis.search.repositories import EmbeddingsRepository

logger = get_logger(__name__)


def _get_page(pages: list[Page], chunk_metadata: dict[str, Any]) -> Page:
    filtered_page = next(
        (page for page in pages if cast(dict[str, Any], page.page_metadata)["page"] == chunk_metadata["page"]), None
    )
    if filtered_page is None:
        logger.warning_with_attrs("Page not found", {"chunk_metadata": chunk_metadata})
        return pages[0]
    return filtered_page


class EmbeddingsService:
    def __init__(
        self,
        page_repository: PageRepository,
        embeddings_repository: EmbeddingsRepository,
        model: BGEM3FlagModel,
        splitter: MarkdownSplitter,
    ):
        self._page_repository = page_repository
        self._embeddings_repository = embeddings_repository
        self._splitter = splitter
        self._model = model

    def find_similar_documents(
        self, collection: EmbeddingsCollection, query: str, limit: int = 10
    ) -> list[tuple[Embeddings, float]]:
        logger.info_with_attrs("Searching for similar documents...", {"collection": collection.name, "limit": limit})
        query_embedding = self._model.encode(query, return_dense=True, return_sparse=True)
        dense_query_embedding = cast(list[float], query_embedding["dense_vecs"].tolist())
        return self._embeddings_repository.get_all_similar_to(collection, dense_query_embedding, limit)

    def embed_document(self, collection: EmbeddingsCollection, document: Document) -> list[Embeddings]:
        pages = self._page_repository.get_by_document_id(document.id)
        logger.info_with_attrs("Embedding document...", {"document_id": document.id, "pages": len(pages)})
        chunks = self._splitter.split([page.to_langchain_document() for page in pages])
        logger.info_with_attrs(
            "Split document into chunks, start computing embeddings...",
            {"document_id": document.id, "chunks": len(chunks)},
        )
        computed_embeddings = self._model.encode_corpus(
            [chunk.page_content for chunk in chunks], return_dense=True, return_sparse=True
        )
        embeddings = [
            Embeddings(
                collection=collection,
                document=document,
                page=_get_page(pages, chunk.metadata),
                chunk=chunk.page_content,
                embedding=cast(list[float], dense_vector.tolist()),
                sparse_embedding=cast(dict[str, float], lexical_weights),
                chunk_metadata=chunk.metadata,
            )
            for chunk, dense_vector, lexical_weights in zip(
                chunks, computed_embeddings["dense_vecs"], computed_embeddings["lexical_weights"]
            )
        ]
        self._embeddings_repository.save_all(embeddings)
        logger.info_with_attrs(
            "Saved embeddings for document", {"document_id": document.id, "embeddings": len(embeddings)}
        )
        return embeddings
