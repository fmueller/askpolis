import datetime
import os
from collections.abc import Generator
from typing import Annotated, Any, Optional

import uuid_utils.compat as uuid
from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
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
    SearchServiceBase,
    get_embedding_model,
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


def get_search_service(db: Annotated[Session, Depends(get_db)]) -> SearchServiceBase:
    embeddings_repository = EmbeddingsRepository(db)
    page_repository = PageRepository(db)
    splitter = MarkdownSplitter(chunk_size=2000, chunk_overlap=400)
    embeddings_service = EmbeddingsService(page_repository, embeddings_repository, get_embedding_model(), splitter)
    reranker_service = RerankerService()
    return SearchService(EmbeddingsCollectionRepository(db), embeddings_service, reranker_service)


class HealthResponse(BaseModel):
    healthy: bool


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class AnswerResponse(BaseModel):
    question: str
    answer: str
    search_results: list[SearchResult]


class QuestionResponse(BaseModel):
    id: uuid.UUID
    text: str
    status: str
    created_at: str
    answer_url: str | None = None
    answer: AnswerResponse | None = None


class CreateQuestionRequest(BaseModel):
    question: str = Field()


@app.get("/")
def read_root() -> HealthResponse:
    return HealthResponse(healthy=True)


@app.get("/v0/tasks/embeddings")
def trigger_embeddings_ingestion() -> JSONResponse:
    celery_app.send_task("ingest_embeddings_for_one_document")
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_202_ACCEPTED)


@app.get("/v0/tasks/tests/embeddings")
def trigger_embeddings_test() -> JSONResponse:
    celery_app.send_task("test_embeddings")
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_202_ACCEPTED)


@app.get("/v0/search")
def search(
    search_service: Annotated[SearchService, Depends(get_search_service)],
    query: str,
    limit: int = 5,
    reranking: bool = False,
    index: Annotated[list[str] | None, Query()] = None,
) -> SearchResponse:
    if index is None:
        index = ["default"]
    if limit < 1:
        limit = 5
    return SearchResponse(query=query, results=search_service.find_matching_texts(query, limit, reranking, index))


@app.get("/v0/answers")
def get_answers(search_service: Annotated[SearchService, Depends(get_search_service)], question: str) -> AnswerResponse:
    logger.info_with_attrs("Querying...", {"question": question})
    results = search_service.find_matching_texts(question, limit=5, use_reranker=True)

    logger.info("Invoking LLM chain...")
    content = "\n\n".join([r.matching_text for r in results])
    answer = agent.run_sync(user_prompt=f"Query: {question}\n\nContent:\n\n{content}")

    return AnswerResponse(question=question, answer=answer.data, search_results=results)


@app.post("/v0/questions", status_code=status.HTTP_201_CREATED, response_model=QuestionResponse)
def create_question(request: Request, payload: CreateQuestionRequest) -> JSONResponse:
    question_id = uuid.uuid7()
    question = QuestionResponse(
        id=question_id,
        text=payload.question,
        status="pending",
        answer_url=str(request.url_for("get_answer", question_id=question_id)),
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
    )
    return JSONResponse(
        content=jsonable_encoder(question),
        status_code=status.HTTP_201_CREATED,
        headers={"Location": str(request.url_for("get_question", question_id=question.id))},
    )


@app.get("/v0/questions/{question_id}")
def get_question(question_id: uuid.UUID) -> QuestionResponse:
    return QuestionResponse(
        id=question_id, text="", status="pending", created_at=datetime.datetime.now(datetime.UTC).isoformat()
    )


@app.get("/v0/questions/{question_id}/answer")
def get_answer(question_id: uuid.UUID) -> AnswerResponse:
    return AnswerResponse(question="", answer="", search_results=[])
