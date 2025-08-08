import datetime
import random
from typing import Any

from celery import shared_task

from askpolis.core import Document, DocumentRepository, DocumentType, MarkdownSplitter, Page
from askpolis.db import get_db
from askpolis.logging import get_logger
from askpolis.task_utils import build_task_result

from .embeddings_service import EmbeddingsService, get_embedding_model
from .models import EmbeddingsCollection
from .repositories import EmbeddingsCollectionRepository, EmbeddingsRepository

logger = get_logger(__name__)


@shared_task(name="test_embeddings")
def test_embeddings() -> dict[str, Any]:
    session = next(get_db())
    try:
        collections_repository = EmbeddingsCollectionRepository(session)
        collection = collections_repository.get_most_recent_by_name("test")
        if collection is None:
            logger.info("Creating test embeddings collection...")
            collection = EmbeddingsCollection(name="test", version="v0", description="Test collection")
            collections_repository.save(collection)

        embeddings_repository = EmbeddingsRepository(session)
        splitter = MarkdownSplitter(chunk_size=20, chunk_overlap=0)
        embeddings_service = EmbeddingsService(
            DocumentRepository(session), embeddings_repository, get_embedding_model(), splitter
        )

        document_repository = DocumentRepository(session)
        document = Document(
            name=f"Test Document{datetime.datetime.now(datetime.UTC).isoformat()}",
            document_type=DocumentType.ELECTION_PROGRAM,
        )
        document_repository.save(document)
        document_repository.add_pages(
            document,
            [
                Page(
                    document_id=document.id,
                    page_number=i,
                    content=f"Page {i}",
                    raw_content=f"Page Raw {i}",
                    page_metadata={"page": i},
                )
                for i in range(10)
            ],
        )
        logger.info_with_attrs("Ingesting embeddings for test document...", {"document_id": document.id})
        computed_embeddings = embeddings_service.embed_document(collection, document)
        logger.info_with_attrs(
            "Computed embeddings for test document",
            {"document_id": document.id, "embeddings": len(computed_embeddings)},
        )
        return build_task_result("success", str(document.id), {"embeddings": len(computed_embeddings)})
    finally:
        session.close()


@shared_task(name="ingest_embeddings_for_one_document")
def ingest_embeddings_for_one_document() -> dict[str, Any]:
    # TODO change to parameters of the installation, overridable in tenant configuration
    splitter = MarkdownSplitter(chunk_size=500, chunk_overlap=100)

    session = next(get_db())
    try:
        collections_repository = EmbeddingsCollectionRepository(session)
        collection = collections_repository.get_most_recent_by_name("default")
        if collection is None:
            logger.info("Creating default embeddings collection...")
            collection = EmbeddingsCollection(name="default", version="v0", description="Default collection")
            collections_repository.save(collection)

        embeddings_repository = EmbeddingsRepository(session)
        documents = embeddings_repository.get_documents_without_embeddings()
        if len(documents) == 0:
            logger.info("No documents without embeddings found")
            return build_task_result("no_documents", None, {"documents": 0})

        embeddings_service = EmbeddingsService(
            DocumentRepository(session), embeddings_repository, get_embedding_model(), splitter
        )
        document = documents[random.randint(0, len(documents) - 1)]
        logger.info_with_attrs("Ingesting embeddings for document...", {"document_id": document.id})

        computed_embeddings = embeddings_service.embed_document(collection, document)
        logger.info_with_attrs(
            "Computed embeddings for document", {"document_id": document.id, "embeddings": len(computed_embeddings)}
        )
        return build_task_result("success", str(document.id), {"embeddings": len(computed_embeddings)})
    finally:
        session.close()
