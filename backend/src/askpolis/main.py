import os
from collections.abc import Generator
from typing import Annotated, Any, Optional

import uuid_utils.compat as uuid
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
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
from askpolis.core import DocumentRepository, MarkdownSplitter, PageRepository, ParliamentRepository
from askpolis.logging import configure_logging, get_logger
from askpolis.qa.qa_service import QAService
from askpolis.qa.repositories import QuestionRepository
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


def get_qa_service(db: Annotated[Session, Depends(get_db)]) -> QAService:
    question_repository = QuestionRepository(db)
    parliament_repository = ParliamentRepository(db)
    return QAService(question_repository, parliament_repository)


def get_document_repository(db: Annotated[Session, Depends(get_db)]) -> DocumentRepository:
    return DocumentRepository(db)


def get_embeddings_repository(db: Annotated[Session, Depends(get_db)]) -> EmbeddingsRepository:
    return EmbeddingsRepository(db)


class HealthResponse(BaseModel):
    healthy: bool


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class LegacyAnswerResponse(BaseModel):
    question: str
    answer: str
    search_results: list[SearchResult]


class CitationResponse(BaseModel):
    title: str
    content: str


class AnswerResponse(BaseModel):
    answer: str | None = None
    language: str | None = None
    status: str
    citations: list[CitationResponse] = []
    created_at: str | None = None
    updated_at: str | None = None


class QuestionResponse(BaseModel):
    id: uuid.UUID
    content: str
    status: str
    created_at: str
    updated_at: str
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
def get_answers(
    search_service: Annotated[SearchService, Depends(get_search_service)], question: str
) -> LegacyAnswerResponse:
    logger.info_with_attrs("Querying...", {"question": question})
    results = search_service.find_matching_texts(question, limit=5, use_reranker=True)

    logger.info("Invoking LLM chain...")
    content = "\n\n".join([r.matching_text for r in results])
    answer = agent.run_sync(user_prompt=f"Query: {question}\n\nContent:\n\n{content}")

    return LegacyAnswerResponse(question=question, answer=answer.output, search_results=results)


@app.post("/v0/questions", status_code=status.HTTP_201_CREATED, response_model=QuestionResponse)
def create_question(
    request: Request, payload: CreateQuestionRequest, qa_service: Annotated[QAService, Depends(get_qa_service)]
) -> JSONResponse:
    question = qa_service.add_question(payload.question)
    return JSONResponse(
        content=jsonable_encoder(
            QuestionResponse(
                id=question.id,
                content=payload.question,
                status="pending",
                answer_url=str(request.url_for("get_answer", question_id=question.id)),
                created_at=question.created_at.isoformat(),
                updated_at=question.updated_at.isoformat(),
            )
        ),
        status_code=status.HTTP_201_CREATED,
        headers={"Location": str(request.url_for("get_question", question_id=question.id))},
    )


@app.get(
    path="/v0/questions/{question_id}",
    response_model=QuestionResponse,
    responses={404: {"description": "Question not found"}},
)
def get_question(
    request: Request, question_id: uuid.UUID, qa_service: Annotated[QAService, Depends(get_qa_service)]
) -> QuestionResponse:
    question = qa_service.get_question(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return QuestionResponse(
        id=question.id,
        content=question.content,
        status="pending" if len(question.answers) == 0 else "answered",
        answer_url=str(request.url_for("get_answer", question_id=question.id)),
        created_at=question.created_at.isoformat(),
        updated_at=question.updated_at.isoformat(),
    )


@app.get(
    path="/v0/questions/{question_id}/answer",
    response_model=AnswerResponse,
    responses={
        404: {"description": "Question not found"},
        500: {"description": "Answer without content pieces should not exist"},
    },
)
def get_answer(
    question_id: uuid.UUID,
    qa_service: Annotated[QAService, Depends(get_qa_service)],
    document_repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    embeddings_repository: Annotated[EmbeddingsRepository, Depends(get_embeddings_repository)],
) -> AnswerResponse:
    question = qa_service.get_question(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    if len(question.answers) == 0:
        return AnswerResponse(
            status="in_progress",
            citations=[],
        )

    answer = question.answers[0]
    if len(answer.contents) == 0:
        raise HTTPException(status_code=500, detail="Answer without content pieces should not exist")

    citation_responses: list[CitationResponse] = []
    for cit in answer.citations:
        doc = document_repository.get(cit.document_id)
        emb = embeddings_repository.get(cit.embeddings_id)

        title = doc.name if doc and doc.name else "Unknown"
        content = emb.chunk if emb and emb.chunk else "Unknown"

        citation_responses.append(
            CitationResponse(
                title=title,
                content=content,
            )
        )

    return AnswerResponse(
        answer=answer.contents[0].content,
        language=answer.contents[0].language,
        status="completed",
        citations=citation_responses,
        created_at=answer.created_at.isoformat(),
        updated_at=answer.updated_at.isoformat(),
    )
