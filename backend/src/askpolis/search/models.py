import datetime
from typing import Any, Optional

import uuid_utils.compat as uuid
from pgvector.sqlalchemy import SparseVector, Vector
from pgvector.sqlalchemy.sparsevec import SPARSEVEC
from pydantic import BaseModel
from sqlalchemy import UUID as DB_UUID
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from askpolis.core import Base, Document, Page
from askpolis.logging import get_logger

logger = get_logger(__name__)


def convert_to_sparse_vector(lexical_weights: dict[str, float]) -> SparseVector:
    """Convert BGE-M3 lexical weights to PGVector SparseVector."""

    validated = []
    max_dim = 250002

    for token_id, weight in lexical_weights.items():
        idx = int(token_id) + 1  # Critical: BGE-M3 uses 0-based indices
        if 1 <= idx <= max_dim:
            validated.append((idx, weight))
        else:
            logger.warning(f"Token index is out of bounds: 1 <= {idx} <= {max_dim}")

    sorted_entries = sorted(validated, key=lambda x: x[0])
    entries = [f"{k}:{v:.9f}" for k, v in sorted_entries]
    return SparseVector.from_text(f"{{{','.join(entries)}}}/{max_dim}")


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
    name = mapped_column(String, nullable=False)
    version = mapped_column(String, nullable=False)
    description = mapped_column(String, nullable=False)
    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))


class Embeddings(Base):
    __tablename__ = "embeddings"

    def __init__(
        self,
        collection: EmbeddingsCollection,
        document: Document,
        page: Page,
        chunk: str,
        embedding: list[float],
        sparse_embedding: dict[str, float],
        chunk_metadata: dict[str, Any],
        **kw: Any,
    ) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.collection_id = collection.id
        self.document_id = document.id
        self.page_id = page.id
        self.chunk = chunk
        self.embedding = embedding
        self.sparse_embedding = convert_to_sparse_vector(sparse_embedding)
        self.chunk_metadata = chunk_metadata
        self.created_at = datetime.datetime.now(datetime.UTC)

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    collection_id: Mapped[uuid.UUID] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("embeddings_collections.id"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    page_id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), ForeignKey("pages.id"), nullable=False)
    chunk: Mapped[str] = mapped_column(String, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)
    sparse_embedding: Mapped[SparseVector] = mapped_column(SPARSEVEC(250002), nullable=False)
    chunk_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))


class SearchResult(BaseModel):
    matching_text: str
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    page_id: uuid.UUID
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
