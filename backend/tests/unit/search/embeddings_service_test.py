from unittest.mock import MagicMock, Mock

import numpy as np
import pytest

from askpolis.core import Document, DocumentType, Page
from askpolis.search import EmbeddingsCollection, EmbeddingsService
from askpolis.search.models import convert_to_sparse_vector


@pytest.fixture
def mock_page_repository() -> Mock:
    return MagicMock()


@pytest.fixture
def mock_embeddings_repository() -> Mock:
    return MagicMock()


@pytest.fixture
def mock_model() -> Mock:
    return MagicMock()


@pytest.fixture
def mock_splitter() -> Mock:
    return MagicMock()


@pytest.fixture
def embeddings_service(
    mock_page_repository: Mock, mock_embeddings_repository: Mock, mock_model: Mock, mock_splitter: Mock
) -> EmbeddingsService:
    return EmbeddingsService(
        page_repository=mock_page_repository,
        embeddings_repository=mock_embeddings_repository,
        model=mock_model,
        splitter=mock_splitter,
    )


def test_embed_document(
    embeddings_service: EmbeddingsService,
    mock_page_repository: Mock,
    mock_embeddings_repository: Mock,
    mock_model: Mock,
    mock_splitter: Mock,
) -> None:
    document = Document(name="Test Document", document_type=DocumentType.ELECTION_PROGRAM)
    collection = EmbeddingsCollection(name="Test Collection", version="v1", description="Test Collection Description")
    page = Page(document_id=document.id, page_number=1, content="Test Content", page_metadata={"page": 1})
    mock_page_repository.get_by_document_id.return_value = [page]
    chunk = MagicMock()
    chunk.page_content = "Chunk content"
    chunk.metadata = {"page": 1, "chunk_id": 0}
    mock_splitter.split.return_value = [chunk]
    mock_model.encode_corpus.return_value = {
        "dense_vecs": [np.array([0.1, 0.2, 0.3])],
        "lexical_weights": [
            {
                "123": 0.123,
                "456": 0.456,
                "789": 0.789,
            }
        ],
    }

    embeddings = embeddings_service.embed_document(collection, document)

    assert len(embeddings) == 1
    assert embeddings[0].collection_id == collection.id
    assert embeddings[0].document_id == document.id
    assert embeddings[0].page_id == page.id
    assert embeddings[0].chunk == "Chunk content"
    assert embeddings[0].embedding == [0.1, 0.2, 0.3]
    assert embeddings[0].sparse_embedding == convert_to_sparse_vector(
        {
            "123": 0.123,
            "456": 0.456,
            "789": 0.789,
        }
    )
    assert embeddings[0].chunk_id == 0
    assert embeddings[0].chunk_metadata == {"page": 1, "chunk_id": 0}
    mock_embeddings_repository.save_all.assert_called_once_with(embeddings)


def test_embed_document_sets_correct_page(
    embeddings_service: EmbeddingsService,
    mock_page_repository: Mock,
    mock_embeddings_repository: Mock,
    mock_model: Mock,
    mock_splitter: Mock,
) -> None:
    document = Document(name="Test Document", document_type=DocumentType.ELECTION_PROGRAM)
    collection = EmbeddingsCollection(name="Test Collection", version="v1", description="Test Collection Description")

    page1 = Page(document_id=document.id, page_number=1, content="Test Content 1", page_metadata={"page": 1})
    page2 = Page(document_id=document.id, page_number=2, content="Test Content 2", page_metadata={"page": 2})
    mock_page_repository.get_by_document_id.return_value = [page1, page2]

    chunk1 = MagicMock()
    chunk1.page_content = "Chunk content 1"
    chunk1.metadata = {"page": 1, "chunk_id": 0}

    chunk2 = MagicMock()
    chunk2.page_content = "Chunk content 2"
    chunk2.metadata = {"page": 2, "chunk_id": 1}

    mock_splitter.split.return_value = [chunk1, chunk2]
    mock_model.encode_corpus.return_value = {
        "dense_vecs": [np.array([0.1, 0.2, 0.3]), np.array([0.4, 0.5, 0.6])],
        "lexical_weights": [
            {
                "123": 0.123,
                "456": 0.456,
                "789": 0.789,
            },
            {
                "012": 0.123,
                "8888": 0.456,
                "12122": 0.789,
            },
        ],
    }

    embeddings = embeddings_service.embed_document(collection, document)

    assert len(embeddings) == 2
    assert embeddings[0].page_id == page1.id
    assert embeddings[0].embedding == [0.1, 0.2, 0.3]
    assert embeddings[0].sparse_embedding == convert_to_sparse_vector(
        {
            "123": 0.123,
            "456": 0.456,
            "789": 0.789,
        }
    )
    assert embeddings[0].chunk_id == 0
    assert embeddings[0].chunk_metadata == {"page": 1, "chunk_id": 0}
    assert embeddings[1].page_id == page2.id
    assert embeddings[1].embedding == [0.4, 0.5, 0.6]
    assert embeddings[1].sparse_embedding == convert_to_sparse_vector(
        {
            "012": 0.123,
            "8888": 0.456,
            "12122": 0.789,
        }
    )
    assert embeddings[1].chunk_id == 1
    assert embeddings[1].chunk_metadata == {"page": 2, "chunk_id": 1}
    mock_embeddings_repository.save_all.assert_called_once_with(embeddings)
