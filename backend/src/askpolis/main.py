import os

import requests
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from FlagEmbedding import FlagReranker
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from askpolis.celery import app as celery_app
from askpolis.core import MarkdownSplitter
from askpolis.core.database import PageRepository
from askpolis.core.pdf_reader import PdfReader
from askpolis.logging import configure_logging, get_logger
from askpolis.search import (
    EmbeddingsCollectionRepository,
    EmbeddingsRepository,
    EmbeddingsService,
    RerankerService,
    SearchResult,
    SearchService,
)

configure_logging()

logger = get_logger(__name__)
logger.info("Starting AskPolis API...")

engine = create_engine(os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres@postgres:5432/askpolis-db")
SessionLocal = sessionmaker(bind=engine)

app = FastAPI()

splitter = MarkdownSplitter(chunk_size=2000, chunk_overlap=400)
reranker_service = RerankerService()

chat_model = ChatOllama(model="llama3.1")
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
    You are AskPolis, an helpful AI agent answering user questions about politics backed by documents.
    You only use the provided document chunks to answer the question.
    You respond in Markdown and use paragraphs to structure your answer.
    You only provide the answer to the question without any additional fluff.

    Chunks:

    {documents}
    """,
        ),
        ("human", "Question: {question}"),
    ]
)

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"trust_remote_code": True},
    encode_kwargs={"normalize_embeddings": True},
)

vector_store = InMemoryVectorStore(embeddings)

reranker = FlagReranker("BAAI/bge-reranker-v2-m3")


class HealthResponse(BaseModel):
    healthy: bool


class LegacySearchResponse(BaseModel):
    query: str
    search_results: list[tuple[Document, float]]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class AnswerResponse(BaseModel):
    question: str
    answer: str
    search_results: list[tuple[Document, float]]


@app.get("/")
def read_root() -> HealthResponse:
    return HealthResponse(healthy=True)


@app.get("/v0/tasks/embeddings")
def trigger_embeddings_ingestion() -> JSONResponse:
    celery_app.send_task("ingest_embeddings_for_one_document")
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_202_ACCEPTED)


@app.get("/v0/search")
def search(query: str, limit: int = 5, reranking: bool = False) -> SearchResponse:
    if limit < 1:
        limit = 5

    with SessionLocal() as session:
        default_collection = EmbeddingsCollectionRepository(session).get_most_recent_by_name("default")
        if default_collection is None:
            return SearchResponse(query=query, results=[])

        # TODO: How does dependency injection work in FastAPI with database sessions?
        embeddings_repository = EmbeddingsRepository(session)
        page_repository = PageRepository(session)
        embeddings_service = EmbeddingsService(page_repository, embeddings_repository, embeddings, splitter)
        search_service = SearchService(default_collection, embeddings_service, reranker_service)
        return SearchResponse(query=query, results=search_service.find_matching_texts(query, limit, reranking))


@app.get("/v0/legacy-search")
def legacy_search(query: str, limit: int = 5, reranking: bool = False) -> LegacySearchResponse:
    logger.info_with_attrs("Searching...", {"query": query, "limit": limit, "reranking": reranking})
    if limit < 1:
        limit = 5

    query_size = limit
    if reranking:
        query_size *= 2

    results = vector_store.similarity_search_with_score_by_vector(embedding=embeddings.embed_query(query), k=query_size)
    if len(results) == 0:
        logger.warning_with_attrs("No results found", {"query": query})

    if reranking and len(results) > 0:
        logger.info("Reranking...")
        reranked_scores = reranker.compute_score([(query, r[0].page_content) for r in results], normalize=True)
        ranked_docs = [doc for _, doc in sorted(zip(reranked_scores, results), reverse=True)][:limit]
        return LegacySearchResponse(
            query=query,
            search_results=sorted(
                [(doc[0], score) for doc, score in zip(ranked_docs, reranked_scores)], key=lambda x: x[1], reverse=True
            ),
        )

    return LegacySearchResponse(query=query, search_results=results)


@app.get("/v0/answers")
def get_answers(question: str) -> AnswerResponse:
    logger.info_with_attrs("Querying...", {"question": question})
    results = vector_store.similarity_search_with_score_by_vector(embedding=embeddings.embed_query(question), k=5)

    if len(results) == 0:
        logger.info("Downloading PDF...")
        response = requests.get(
            "https://www.grundsatzprogramm-cdu.de/sites/www.grundsatzprogramm-cdu.de/files/downloads/240507_cdu_gsp_2024_beschluss_parteitag_final_1.pdf"
        )

        with open("temp.pdf", "wb") as f:
            f.write(response.content)

        logger.info("Read PDF to Markdown...")
        markdown_doc = PdfReader("temp.pdf").to_markdown()
        assert markdown_doc is not None
        final_chunks = MarkdownSplitter(chunk_size=2000, chunk_overlap=400).split(markdown_doc.to_langchain_documents())
        logger.info(f"Final chunks: {len(final_chunks)}")
        vector_store.add_documents(final_chunks)
        logger.info("Querying again...")
        results = vector_store.similarity_search_with_score_by_vector(embedding=embeddings.embed_query(question), k=5)

    context = "\n\n".join(["<chunk>\n" + r[0].page_content + "\n</chunk>" for r in results])
    chain = prompt | chat_model
    logger.info("Invoking LLM chain...")
    answer = chain.invoke({"documents": context, "question": question})

    return AnswerResponse(question=question, answer=answer.pretty_repr(), search_results=results)
