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
    assert embeddings[0].embedding == [0.1, 0.2, 0.3]
    assert embeddings[0].chunk_metadata == {"page": 1}
    mock_embeddings_repository.save_all.assert_called_once_with(embeddings)


def test_embed_document_sets_correct_page(
    embeddings_service: EmbeddingsService,
    mock_page_repository: Mock,
    mock_embeddings_repository: Mock,
    mock_embeddings: Mock,
    mock_splitter: Mock,
) -> None:
    document = Document(name="Test Document", document_type=DocumentType.ELECTION_PROGRAM)
    collection = EmbeddingsCollection(name="Test Collection", version="v1", description="Test Collection Description")

    page1 = Page(document_id=document.id, page_number=1, content="Test Content 1", page_metadata={"page": 1})
    page2 = Page(document_id=document.id, page_number=2, content="Test Content 2", page_metadata={"page": 2})
    mock_page_repository.get_by_document_id.return_value = [page1, page2]

    chunk1 = MagicMock()
    chunk1.page_content = "Chunk content 1"
    chunk1.metadata = page1.page_metadata

    chunk2 = MagicMock()
    chunk2.page_content = "Chunk content 2"
    chunk2.metadata = page2.page_metadata

    mock_splitter.split.return_value = [chunk1, chunk2]
    mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    embeddings = embeddings_service.embed_document(collection, document)

    assert len(embeddings) == 2
    assert embeddings[0].page_id == page1.id
    assert embeddings[1].page_id == page2.id
    mock_embeddings_repository.save_all.assert_called_once_with(embeddings)
