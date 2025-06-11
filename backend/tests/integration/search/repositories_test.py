from typing import cast

import numpy as np
from sqlalchemy.orm import Session

from askpolis.core import Document, DocumentRepository, DocumentType, Page
from askpolis.search import Embeddings, EmbeddingsCollection, EmbeddingsCollectionRepository, EmbeddingsRepository


def test_embeddings_data_model(db_session: Session) -> None:
    collection = EmbeddingsCollection(name="test", version="v1", description="test collection")
    EmbeddingsCollectionRepository(db_session).save(collection)

    document = Document(name="Test Document", document_type=DocumentType.ELECTION_PROGRAM)
    page = Page(document_id=document.id, page_number=1, content="Test Content", page_metadata={"page": 1})
    db_session.add(document)
    db_session.add(page)

    random_vector = cast(list[float], np.random.rand(1024).astype(np.float32).tolist())
    embeddings = Embeddings(
        collection=collection,
        document=document,
        page=page,
        chunk="chunk",
        chunk_id=0,
        embedding=random_vector,
        sparse_embedding={"1": 0.123, "11": 0.456, "123": 0.789},
        chunk_metadata={"key": "value"},
    )
    EmbeddingsRepository(db_session).save_all([embeddings])

    document_from_db = DocumentRepository(db_session).get_by_name("Test Document")
    assert document_from_db is not None
    embeddings_of_doc = EmbeddingsRepository(db_session).get_all_by_document(document_from_db)

    assert len(embeddings_of_doc) == 1
    np.testing.assert_array_equal(embeddings_of_doc[0].embedding, random_vector)


def test_get_all_similar_to(db_session: Session) -> None:
    collection = EmbeddingsCollection(name="test", version="v1", description="test collection")
    EmbeddingsCollectionRepository(db_session).save(collection)

    document = Document(name="Test Document", document_type=DocumentType.ELECTION_PROGRAM)
    page = Page(document_id=document.id, page_number=1, content="Test Content", page_metadata={"page": 1})
    db_session.add(document)
    db_session.add(page)

    random_vector = cast(list[float], np.random.rand(1024).astype(np.float32).tolist())
    embeddings = Embeddings(
        collection=collection,
        document=document,
        page=page,
        chunk="chunk",
        chunk_id=0,
        embedding=random_vector,
        sparse_embedding={"1": 0.123, "11": 0.456, "123": 0.789},
        chunk_metadata={"key": "value"},
    )
    EmbeddingsRepository(db_session).save_all([embeddings])

    collection_from_db = EmbeddingsCollectionRepository(db_session).get_most_recent_by_name("test")
    assert collection_from_db is not None

    similar_docs = EmbeddingsRepository(db_session).get_all_similar_to(collection_from_db, random_vector)
    assert len(similar_docs) == 1

    np.testing.assert_array_equal(similar_docs[0][0].embedding, random_vector)
