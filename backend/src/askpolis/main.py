import os
from collections.abc import Generator
from typing import Annotated, Any, Optional

from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse
from FlagEmbedding import BGEM3FlagModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

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

engine: Optional[Engine] = None
DbSession: Optional[sessionmaker[Session]] = None

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
    use_fp16=False,
    cache_dir=os.getenv("HF_HUB_CACHE"),
    passage_max_length=8192,
    query_max_length=8192,
    trust_remote_code=True,
    normalize_embeddings=True,
)


def get_db() -> Generator[Session, Any, None]:
    global engine, DbSession
    if not engine:
        try:
            engine = create_engine(
                os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres@postgres:5432/askpolis-db"
            )
        except Exception as e:
            raise Exception("Error while connecting to database") from e

    if not DbSession:
        DbSession = sessionmaker(bind=engine)

    db = DbSession()
    try:
        yield db
    finally:
        db.close()


def get_search_service(db: Annotated[Session, Depends(get_db)]) -> SearchService:
    default_collection = EmbeddingsCollectionRepository(db).get_most_recent_by_name("default")
    if default_collection is None:
        raise ValueError("No default embeddings collection!")
    embeddings_repository = EmbeddingsRepository(db)
    page_repository = PageRepository(db)
    embeddings_service = EmbeddingsService(page_repository, embeddings_repository, model, splitter)
    return SearchService(default_collection, embeddings_service, reranker_service)


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
def search(
    search_service: Annotated[SearchService, Depends(get_search_service)],
    query: str,
    limit: int = 5,
    reranking: bool = False,
) -> SearchResponse:
    if limit < 1:
        limit = 5
    return SearchResponse(query=query, results=search_service.find_matching_texts(query, limit, reranking))


@app.get("/v0/answers")
def get_answers(search_service: Annotated[SearchService, Depends(get_search_service)], question: str) -> AnswerResponse:
    logger.info_with_attrs("Querying...", {"question": question})
    results = search_service.find_matching_texts(question, limit=5, use_reranker=True)

    context = "\n\n".join(["<chunk>\n" + r.matching_text + "\n</chunk>" for r in results])
    chain = prompt | chat_model
    logger.info("Invoking LLM chain...")
    answer = chain.invoke({"documents": context, "question": question})

    return AnswerResponse(question=question, answer=answer.pretty_repr(), search_results=results)
