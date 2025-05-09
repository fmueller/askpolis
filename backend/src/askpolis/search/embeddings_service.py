import os
import uuid
from typing import Any, cast, TypedDict

import numpy.typing as npt
import numpy as np
from FlagEmbedding import BGEM3FlagModel
from FlagEmbedding.inference.embedder.encoder_only.m3 import M3Embedder

from askpolis.core import Document, MarkdownSplitter, Page, PageRepository
from askpolis.logging import get_logger
from askpolis.search.models import Embeddings, EmbeddingsCollection
from askpolis.search.repositories import EmbeddingsRepository

logger = get_logger(__name__)


def _rrf_merge(
    dense_results: list[tuple[Embeddings, float]], sparse_results: list[tuple[Embeddings, float]], k: int = 60
) -> list[tuple[Embeddings, float]]:
    combined_scores: dict[uuid.UUID, float] = {}

    for rank, (embedding, _) in enumerate(dense_results):
        combined_scores[embedding.id] = combined_scores.get(embedding.id, 0) + 1 / (k + rank + 1)
    for rank, (embedding, _) in enumerate(sparse_results):
        combined_scores[embedding.id] = combined_scores.get(embedding.id, 0) + 1 / (k + rank + 1)

    unique_embeddings = {embedding.id: embedding for embedding, _ in dense_results + sparse_results}
    merged_results = [(unique_embeddings[embedding_id], score) for embedding_id, score in combined_scores.items()]
    merged_results.sort(key=lambda x: x[1], reverse=True)
    return merged_results


def _get_page(pages: list[Page], chunk_metadata: dict[str, Any]) -> Page:
    if len(pages) == 0:
        raise ValueError("No pages provided")

    filtered_page = next(
        (page for page in pages if cast(dict[str, Any], page.page_metadata)["page"] == chunk_metadata["page"]), None
    )
    if filtered_page is None:
        logger.warning_with_attrs("Page not found", {"chunk_metadata": chunk_metadata})
        return pages[0]
    return filtered_page


class Encoded(TypedDict, total=False):
    dense_vecs: npt.NDArray[np.float32]
    lexical_weights: dict[str, float]


class EncodedCorpus(TypedDict, total=False):
    dense_vecs: list[npt.NDArray[np.float32]]
    lexical_weights: list[dict[str, float]]


class FakeModel:
    def __init__(self) -> None:
        pass

    def encode(self, text: str, return_dense: bool = True, return_sparse: bool = True) -> Encoded:
        """
        Encodes a single string and returns a dict with fake dense and sparse representations.
        """
        result: Encoded = {}
        if return_dense:
            result["dense_vecs"] = np.array([0.1 * (i + 1) for i in range(1024)])
        if return_sparse:
            result["lexical_weights"] = {"0": 1.0}
        return result

    def encode_corpus(self, texts: list[str], return_dense: bool = True, return_sparse: bool = True) -> EncodedCorpus:
        """
        Encodes a corpus of texts and returns a dict with lists of fake dense and sparse representations.
        """
        result: EncodedCorpus = {}
        if return_dense:
            # For each text in the corpus, return a dummy vector.
            # Here we simply vary the vector slightly based on the index.
            result["dense_vecs"] = [np.array([0.1 * (i + 1)] * 1024) for i, _ in enumerate(texts)]
        if return_sparse:
            # For each text, we return a dummy dictionary.
            result["lexical_weights"] = [{"0": float(len(text))} for text in texts]
        return result


def get_embedding_model() -> FakeModel | M3Embedder:
    if os.getenv("DISABLE_INFERENCE") == "true":
        return FakeModel()

    return BGEM3FlagModel(
        "BAAI/bge-m3",
        devices="cpu",
        use_fp16=False,
        cache_dir=os.getenv("HF_HUB_CACHE"),
        passage_max_length=8192,
        query_max_length=8192,
        trust_remote_code=True,
        normalize_embeddings=True,
    )


class EmbeddingsService:
    def __init__(
        self,
        page_repository: PageRepository,
        embeddings_repository: EmbeddingsRepository,
        model: FakeModel | M3Embedder,
        splitter: MarkdownSplitter,
    ):
        self._page_repository = page_repository
        self._embeddings_repository = embeddings_repository
        self._splitter = splitter
        self._model = model

    def find_similar_documents(
        self, collection: EmbeddingsCollection | None, query: str, limit: int = 10
    ) -> list[tuple[Embeddings, float]]:
        if limit < 1 or collection is None:
            return []

        logger.info_with_attrs("Searching for similar documents...", {"collection": collection.name, "limit": limit})
        query_embedding = self._model.encode(query, return_dense=True, return_sparse=True)

        dense_query_embedding = cast(list[float], query_embedding["dense_vecs"].tolist())
        sparse_query_embedding = cast(dict[str, float], query_embedding["lexical_weights"])

        dense_results = self._embeddings_repository.get_all_similar_to(collection, dense_query_embedding, limit * 2)
        sparse_results = self._embeddings_repository.get_all_similar_to(collection, sparse_query_embedding, limit * 2)

        return _rrf_merge(dense_results, sparse_results)[:limit]

    def embed_document(self, collection: EmbeddingsCollection, document: Document) -> list[Embeddings]:
        pages = self._page_repository.get_by_document_id(document.id)
        if len(pages) == 0:
            logger.warning_with_attrs("No pages found for document", {"document_id": document.id})
            return []

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
