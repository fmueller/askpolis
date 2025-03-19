import os

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from FlagEmbedding import BGEM3FlagModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from askpolis.celery import app as celery_app
from askpolis.core import MarkdownSplitter, PageRepository
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

model = BGEM3FlagModel(
    "BAAI/bge-m3",
    devices="cpu",
    cache_dir=os.getenv("HF_HUB_CACHE"),
    passage_max_length=8192,
    query_max_length=8192,
    trust_remote_code=True,
    normalize_embeddings=True,
)


class HealthResponse(BaseModel):
    healthy: bool


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class AnswerResponse(BaseModel):
    question: str
    answer: str
    search_results: list[SearchResult]


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
        embeddings_service = EmbeddingsService(page_repository, embeddings_repository, model, splitter)
        search_service = SearchService(default_collection, embeddings_service, reranker_service)
        return SearchResponse(query=query, results=search_service.find_matching_texts(query, limit, reranking))


@app.get("/v0/answers")
def get_answers(question: str) -> AnswerResponse:
    with SessionLocal() as session:
        default_collection = EmbeddingsCollectionRepository(session).get_most_recent_by_name("default")
        if default_collection is None:
            return AnswerResponse(question=question, answer="No default embeddings collection!", search_results=[])

        embeddings_repository = EmbeddingsRepository(session)
        page_repository = PageRepository(session)
        embeddings_service = EmbeddingsService(page_repository, embeddings_repository, model, splitter)
        search_service = SearchService(default_collection, embeddings_service, reranker_service)
        logger.info_with_attrs("Querying...", {"question": question})
        results = search_service.find_matching_texts(question, limit=5, use_reranker=True)

        context = "\n\n".join(["<chunk>\n" + r.matching_text + "\n</chunk>" for r in results])
        chain = prompt | chat_model
        logger.info("Invoking LLM chain...")
        answer = chain.invoke({"documents": context, "question": question})

        return AnswerResponse(question=question, answer=answer.pretty_repr(), search_results=results)
