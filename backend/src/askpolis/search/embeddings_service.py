from langchain_core.embeddings import Embeddings as LangchainEmbeddings

from askpolis.core import Document, MarkdownSplitter
from askpolis.core.database import PageRepository
from askpolis.search.database import EmbeddingsRepository
from askpolis.search.models import Embeddings, EmbeddingsCollection


class EmbeddingsService:
    def __init__(
        self,
        page_repository: PageRepository,
        embeddings_repository: EmbeddingsRepository,
        embeddings: LangchainEmbeddings,
        splitter: MarkdownSplitter,
    ):
        self._page_repository = page_repository
        self._embeddings_repository = embeddings_repository
        self._splitter = splitter
        self._embeddings = embeddings

    def embed_document(self, collection: EmbeddingsCollection, document: Document) -> list[Embeddings]:
        pages = self._page_repository.get_by_document_id(document.id)
        chunks = self._splitter.split([page.to_langchain_document() for page in pages])
        computed_embeddings = self._embeddings.embed_documents([chunk.page_content for chunk in chunks])
        embeddings = [
            Embeddings(
                collection=collection,
                document=document,
                page=next((page for page in pages if page.page_metadata["page"] == chunk.metadata["page"]), pages[0]),
                chunk=chunk.page_content,
                embedding=embedding,
                chunk_metadata=chunk.metadata,
            )
            for chunk, embedding in zip(chunks, computed_embeddings)
        ]
        self._embeddings_repository.save_all(embeddings)
        return embeddings
