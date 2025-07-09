import uuid_utils.compat as uuid
from fastapi.testclient import TestClient

from askpolis.core import (
    Document,
    DocumentType,
    Page,
    get_document_repository,
    get_page_repository,
)
from askpolis.main import app
from askpolis.search.dependencies import get_search_service
from askpolis.search.models import SearchResult
from askpolis.search.search_service import SearchServiceBase


def setup_client(doc: Document, page: Page) -> TestClient:
    class DocRepo:
        def get(self, doc_id: uuid.UUID) -> Document | None:
            return doc if doc_id == doc.id else None

    class PageRepo:
        def get(self, page_id: uuid.UUID) -> Page | None:
            return page if page_id == page.id else None

    class DummySearch(SearchServiceBase):
        def find_matching_texts(
            self, query: str, limit: int = 5, use_reranker: bool = False, indexes: list[str] | None = None
        ) -> list[SearchResult]:
            return [
                SearchResult(
                    matching_text="text",
                    chunk_id=uuid.uuid7(),
                    document_id=doc.id,
                    page_id=page.id,
                    score=1.0,
                )
            ]

    app.dependency_overrides[get_document_repository] = lambda: DocRepo()
    app.dependency_overrides[get_page_repository] = lambda: PageRepo()
    app.dependency_overrides[get_search_service] = lambda: DummySearch()

    return TestClient(app)


def teardown_client() -> None:
    app.dependency_overrides.clear()


def test_document_and_page_endpoints_and_search_urls() -> None:
    document = Document(name="Doc", document_type=DocumentType.ELECTION_PROGRAM)
    page = Page(document_id=document.id, page_number=1, content="content")
    client = setup_client(document, page)

    resp = client.get(f"/v0/documents/{document.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(document.id)

    resp = client.get(f"/v0/documents/{document.id}/pages/{page.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(page.id)

    resp = client.get("/v0/search", params={"query": "foo"})
    assert resp.status_code == 200
    data = resp.json()
    result = data["results"][0]
    assert result["document_url"].endswith(f"/v0/documents/{document.id}")
    assert result["page_url"].endswith(f"/v0/documents/{document.id}/pages/{page.id}")

    teardown_client()
