import os
from collections.abc import Generator
from typing import Annotated, Any, Optional

from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse
from FlagEmbedding import BGEM3FlagModel
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
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

ollama_model = OpenAIModel(
    model_name="llama3.1",
    provider=OpenAIProvider(base_url=os.getenv("OLLAMA_URL") or "http://localhost:11434/v1", api_key="ollama"),
)

agent = Agent(
    ollama_model,
    model_settings=ModelSettings(
        max_tokens=512,
        temperature=0.7,
        top_p=0.9,
    ),
    system_prompt="""
    Answer the query by using ONLY the provided content below.
    Respond with NO_ANSWER if the content is not relevant for answering the query.
    Do NOT add additional information.
    Be concise and respond succinctly using Markdown.
    """,
)

embedding_model = BGEM3FlagModel(
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
    splitter = MarkdownSplitter(chunk_size=2000, chunk_overlap=400)
    embeddings_service = EmbeddingsService(page_repository, embeddings_repository, embedding_model, splitter)
    reranker_service = RerankerService()
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

    logger.info("Invoking LLM chain...")
    content = "\n\n".join([r.matching_text for r in results])
    answer = agent.run_sync(user_prompt=f"Query: {question}\n\nContent:\n\n{content}")

    return AnswerResponse(question=question, answer=answer.data, search_results=results)
