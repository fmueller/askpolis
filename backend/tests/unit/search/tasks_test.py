"""Tests for search Celery tasks."""

from typing import Any, Iterator

from askpolis.core.models import Document, DocumentType
from askpolis.search import tasks as search_tasks
from askpolis.search.models import EmbeddingsCollection


class DummySession:
    def close(self) -> None:  # pragma: no cover - simple stub
        pass


def fake_get_db() -> Iterator[DummySession]:
    yield DummySession()


def test_test_embeddings_returns_result(monkeypatch: Any) -> None:
    class DummyCollectionRepo:
        def __init__(self, session: DummySession) -> None:
            pass

        def get_most_recent_by_name(self, name: str) -> EmbeddingsCollection:
            return EmbeddingsCollection(name=name, version="v0", description="d")

        def save(self, obj: Any) -> None:  # pragma: no cover - stub
            pass

    class DummyEmbeddingsRepo:
        def __init__(self, session: DummySession) -> None:
            pass

    class DummyDocumentRepo:
        def __init__(self, session: DummySession) -> None:
            pass

        def save(self, doc: Document) -> None:  # pragma: no cover - stub
            pass

        def add_pages(self, doc: Document, pages: Any) -> None:  # pragma: no cover - stub
            pass

    class DummyService:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def embed_document(self, collection: EmbeddingsCollection, document: Document) -> list[int]:
            return [1, 2, 3]

    monkeypatch.setattr(search_tasks, "get_db", fake_get_db)
    monkeypatch.setattr(search_tasks, "EmbeddingsCollectionRepository", DummyCollectionRepo)
    monkeypatch.setattr(search_tasks, "EmbeddingsRepository", DummyEmbeddingsRepo)
    monkeypatch.setattr(search_tasks, "DocumentRepository", DummyDocumentRepo)
    monkeypatch.setattr(search_tasks, "EmbeddingsService", DummyService)
    monkeypatch.setattr(search_tasks, "get_embedding_model", lambda: None)

    result = search_tasks.test_embeddings()

    assert result["status"] == "success"
    assert "embeddings" in result["data"]
    assert result["entity_id"] is not None


def test_ingest_embeddings_for_one_document_returns_result(monkeypatch: Any) -> None:
    class DummyCollectionRepo:
        def __init__(self, session: DummySession) -> None:
            pass

        def get_most_recent_by_name(self, name: str) -> EmbeddingsCollection:
            return EmbeddingsCollection(name=name, version="v0", description="d")

        def save(self, obj: Any) -> None:  # pragma: no cover - stub
            pass

    class DummyEmbeddingsRepo:
        def __init__(self, session: DummySession) -> None:
            pass

        def get_documents_without_embeddings(self) -> list[Document]:
            return [Document("doc", DocumentType.ELECTION_PROGRAM)]

    class DummyDocumentRepo:
        def __init__(self, session: DummySession) -> None:
            pass

    class DummyService:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def embed_document(self, collection: EmbeddingsCollection, document: Document) -> list[int]:
            return [1, 2]

    monkeypatch.setattr(search_tasks, "get_db", fake_get_db)
    monkeypatch.setattr(search_tasks, "EmbeddingsCollectionRepository", DummyCollectionRepo)
    monkeypatch.setattr(search_tasks, "EmbeddingsRepository", DummyEmbeddingsRepo)
    monkeypatch.setattr(search_tasks, "DocumentRepository", DummyDocumentRepo)
    monkeypatch.setattr(search_tasks, "EmbeddingsService", DummyService)
    monkeypatch.setattr(search_tasks, "get_embedding_model", lambda: None)

    result = search_tasks.ingest_embeddings_for_one_document()

    assert result["status"] == "success"
    assert "embeddings" in result["data"]
    assert result["entity_id"] is not None
