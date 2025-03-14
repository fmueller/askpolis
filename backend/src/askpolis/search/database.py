from typing import Optional

from sqlalchemy.orm import Session

from askpolis.core import Document
from askpolis.search.models import Embeddings, EmbeddingsCollection


class EmbeddingsCollectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[EmbeddingsCollection]:
        return self.db.query(EmbeddingsCollection).all()

    def get_most_recent_by_name(self, name: str) -> Optional[EmbeddingsCollection]:
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

    def get_all_by_document(self, document: Document) -> list[Embeddings]:
        return self.db.query(Embeddings).filter(Embeddings.document_id == document.id).all()

    def save_all(self, embeddings: list[Embeddings]) -> None:
        self.db.add_all(embeddings)
        self.db.commit()
