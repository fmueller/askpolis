from unittest.mock import MagicMock, Mock

import pytest

from askpolis.core import Document, Page
from askpolis.core.models import DocumentType
from askpolis.search.embeddings_service import EmbeddingsService
from askpolis.search.models import EmbeddingsCollection


@pytest.fixture
def mock_page_repository() -> Mock:
    return MagicMock()


@pytest.fixture
def mock_embeddings_repository() -> Mock:
    return MagicMock()


@pytest.fixture
def mock_embeddings() -> Mock:
    return MagicMock()


@pytest.fixture
def mock_splitter() -> Mock:
    return MagicMock()


@pytest.fixture
def embeddings_service(
    mock_page_repository: Mock, mock_embeddings_repository: Mock, mock_embeddings: Mock, mock_splitter: Mock
) -> EmbeddingsService:
    return EmbeddingsService(
        page_repository=mock_page_repository,
        embeddings_repository=mock_embeddings_repository,
        embeddings=mock_embeddings,
        splitter=mock_splitter,
    )


def test_embed_document(
    embeddings_service: EmbeddingsService,
    mock_page_repository: Mock,
    mock_embeddings_repository: Mock,
    mock_embeddings: Mock,
    mock_splitter: Mock,
) -> None:
    document = Document(name="Test Document", document_type=DocumentType.ELECTION_PROGRAM)
    collection = EmbeddingsCollection(name="Test Collection", version="v1", description="Test Collection Description")
    page = Page(document_id=document.id, page_number=1, content="Test Content", page_metadata={"page": 1})
    mock_page_repository.get_by_document_id.return_value = [page]
    chunk = MagicMock()
    chunk.page_content = "Chunk content"
    chunk.metadata = page.page_metadata
    mock_splitter.split.return_value = [chunk]
    mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]

    embeddings = embeddings_service.embed_document(collection, document)

    assert len(embeddings) == 1
    assert embeddings[0].collection_id == collection.id
    assert embeddings[0].document_id == document.id
    assert embeddings[0].page_id == page.id
    assert embeddings[0].chunk == "Chunk content"
    assert embeddings[0].embedding.dim == [0.1, 0.2, 0.3]
    assert embeddings[0].chunk_metadata == {"page": 1}
    mock_embeddings_repository.save_all.assert_called_once_with(embeddings)
