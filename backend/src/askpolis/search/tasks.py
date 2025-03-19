import os
import random

from celery import shared_task
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from askpolis.core import MarkdownSplitter, PageRepository
from askpolis.logging import get_logger
from askpolis.search import EmbeddingsCollection, EmbeddingsService
from askpolis.search.repositories import EmbeddingsCollectionRepository, EmbeddingsRepository

logger = get_logger(__name__)

engine = create_engine(os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres@postgres:5432/askpolis-db")
SessionLocal = sessionmaker(bind=engine)

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"trust_remote_code": True},
    encode_kwargs={"normalize_embeddings": True},
)

splitter = MarkdownSplitter(chunk_size=2000, chunk_overlap=400)


@shared_task(name="ingest_embeddings_for_one_document")
def ingest_embeddings_for_one_document() -> None:
    session = SessionLocal()
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
            return

        embeddings_service = EmbeddingsService(PageRepository(session), embeddings_repository, embeddings, splitter)
        document = documents[random.randint(0, len(documents) - 1)]
        logger.info_with_attrs("Ingesting embeddings for document...", {"document_id": document.id})

        computed_embeddings = embeddings_service.embed_document(collection, document)
        logger.info_with_attrs(
            "Computed embeddings for document", {"document_id": document.id, "embeddings": len(computed_embeddings)}
        )
    finally:
        session.close()
