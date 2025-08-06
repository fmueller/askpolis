from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from askpolis.core import DocumentRepository, MarkdownSplitter
from askpolis.db import get_db

from .embeddings_service import EmbeddingsService, get_embedding_model
from .repositories import EmbeddingsCollectionRepository, EmbeddingsRepository
from .reranker_service import get_reranker_service
from .search_service import SearchService, SearchServiceBase


def get_embeddings_repository(db: Annotated[Session, Depends(get_db)]) -> EmbeddingsRepository:
    return EmbeddingsRepository(db)


def get_search_service(
    db: Annotated[Session, Depends(get_db)],
    embeddings_repository: Annotated[EmbeddingsRepository, Depends(get_embeddings_repository)],
) -> SearchServiceBase:
    document_repository = DocumentRepository(db)
    splitter = MarkdownSplitter(chunk_size=2000, chunk_overlap=400)
    embeddings_service = EmbeddingsService(document_repository, embeddings_repository, get_embedding_model(), splitter)
    reranker_service = get_reranker_service()
    return SearchService(EmbeddingsCollectionRepository(db), embeddings_service, reranker_service)
