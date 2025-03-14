from typing import cast

import numpy as np
from sqlalchemy.orm import Session, sessionmaker

from askpolis.core import Document, DocumentType, Page
from askpolis.core.database import DocumentRepository
from askpolis.search import Embeddings, EmbeddingsCollection
from askpolis.search.database import EmbeddingsCollectionRepository, EmbeddingsRepository


def test_embeddings_data_model(session_maker: sessionmaker[Session]) -> None:
    with session_maker() as session:
        collection = EmbeddingsCollection(name="test", version="v1", description="test collection")
        EmbeddingsCollectionRepository(session).save(collection)

        document = Document(name="Test Document", document_type=DocumentType.ELECTION_PROGRAM)
        page = Page(document_id=document.id, page_number=1, content="Test Content", page_metadata={"page": 1})
        session.add(document)
        session.add(page)

        random_vector: list[float] = cast(list[float], np.random.rand(1024).astype(np.float32).tolist())
        embeddings = Embeddings(
            collection=collection,
            document=document,
            page=page,
            chunk="chunk",
            embedding=random_vector,
            chunk_metadata={"key": "value"},
        )
        EmbeddingsRepository(session).save_all([embeddings])

    with session_maker() as session:
        document = DocumentRepository(session).get_by_name("Test Document")
        embeddings_of_doc = EmbeddingsRepository(session).get_all_by_document(document)

        assert len(embeddings_of_doc) == 1
        np.testing.assert_array_equal(embeddings_of_doc[0].embedding, random_vector)
