import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from askpolis.core import Document
from askpolis.logging import get_logger

from .models import Embeddings, EmbeddingsCollection, convert_to_sparse_vector

logger = get_logger(__name__)


class EmbeddingsCollectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[EmbeddingsCollection]:
        return self.db.query(EmbeddingsCollection).all()

    def get_most_recent_by_name(self, name: str) -> EmbeddingsCollection | None:
        return (
            self.db.query(EmbeddingsCollection)
            .filter(EmbeddingsCollection.name == name)
            .order_by(EmbeddingsCollection.created_at.desc())
            .first()
        )

    def save(self, collection: EmbeddingsCollection) -> None:
        self.db.add(collection)
        self.db.commit()


class EmbeddingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, embeddings_id: uuid.UUID) -> Embeddings | None:
        return self.db.query(Embeddings).filter(Embeddings.id == embeddings_id).first()

    def get_all_by_document(self, document: Document) -> list[Embeddings]:
        return self.db.query(Embeddings).filter(Embeddings.document_id == document.id).all()

    def get_all_similar_to(
        self, collection: EmbeddingsCollection, query_vector: list[float] | dict[str, float], limit: int = 10
    ) -> list[tuple[Embeddings, float]]:
        if limit <= 0:
            return []

        if isinstance(query_vector, list):
            results = self.db.execute(
                select(Embeddings, 1.0 - Embeddings.embedding.cosine_distance(query_vector).label("score"))
                .filter(Embeddings.collection_id == collection.id)
                .order_by(Embeddings.embedding.cosine_distance(query_vector))
                .limit(limit)
            ).all()
        elif isinstance(query_vector, dict):
            sparse_vector = convert_to_sparse_vector(query_vector)
            results = self.db.execute(
                select(Embeddings, 1.0 - Embeddings.sparse_embedding.cosine_distance(sparse_vector).label("score"))
                .filter(Embeddings.collection_id == collection.id)
                .order_by(Embeddings.sparse_embedding.cosine_distance(sparse_vector))
                .limit(limit)
            ).all()
        else:
            raise ValueError("Unsupported query_vector type")

        return [(embeddings, score) for embeddings, score in results]

    def get_documents_without_embeddings(self) -> list[Document]:
        return self.db.query(Document).outerjoin(Embeddings).filter(Embeddings.id.is_(None)).all()

    def save_all(self, embeddings: list[Embeddings]) -> None:
        self.db.add_all(embeddings)
        self.db.commit()
