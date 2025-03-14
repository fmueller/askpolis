import datetime
from typing import Any

import uuid_utils.compat as uuid
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel
from sqlalchemy import UUID as DB_UUID
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from askpolis.core import Document, Page

Base = declarative_base()


class EmbeddingsCollection(Base):
    __tablename__ = "embeddings_collections"

    def __init__(self, name: str, version: str, description: str, **kw: Any) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.name = name
        self.version = version
        self.description = description
        self.created_at = datetime.datetime.now(datetime.UTC)

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))


class Embeddings(Base):
    __tablename__ = "embeddings"

    def __init__(
        self,
        collection: EmbeddingsCollection,
        document: Document,
        page: Page,
        chunk: str,
        embedding: list[float],
        chunk_metadata: dict[str, Any],
        **kw: Any,
    ) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.collection_id = collection.id
        self.document_id = document.id
        self.page_id = page.id
        self.chunk = chunk
        self.embedding = Vector(embedding)
        self.chunk_metadata = chunk_metadata
        self.created_at = datetime.datetime.now(datetime.UTC)

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    collection_id: Mapped[uuid.UUID] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("embeddings_collections.id"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    page_id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False)
    chunk = Column(String, nullable=False)
    embedding: Mapped[Vector] = Column(Vector(1024), nullable=False)
    chunk_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))


class SearchResult(BaseModel):
    matching_text: str
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    page_number: int
    metadata: dict[str, Any]
    score: float
