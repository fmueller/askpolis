import os
import uuid
from typing import Optional

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from askpolis.core import MarkdownSplitter, PageRepository, ParliamentRepository
from askpolis.logging import get_logger
from askpolis.qa.agents import AnswerAgent
from askpolis.qa.models import Question
from askpolis.qa.qa_service import QAService
from askpolis.qa.repositories import QuestionRepository
from askpolis.search import (
    EmbeddingsCollectionRepository,
    EmbeddingsRepository,
    EmbeddingsService,
    RerankerService,
    SearchService,
    SearchServiceBase,
    get_embedding_model,
)

logger = get_logger(__name__)

engine = create_engine(os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres@postgres:5432/askpolis-db")
DbSession = sessionmaker(bind=engine)


def get_search_service(db: Session) -> SearchServiceBase:
    embeddings_repository = EmbeddingsRepository(db)
    page_repository = PageRepository(db)
    splitter = MarkdownSplitter(chunk_size=2000, chunk_overlap=400)
    embeddings_service = EmbeddingsService(page_repository, embeddings_repository, get_embedding_model(), splitter)
    reranker_service = RerankerService()
    return SearchService(EmbeddingsCollectionRepository(db), embeddings_service, reranker_service)


def get_qa_service(db: Session) -> QAService:
    question_repository = QuestionRepository(db)
    parliament_repository = ParliamentRepository(db)
    return QAService(
        question_repository, parliament_repository, CeleryQuestionScheduler(), AnswerAgent(get_search_service(db))
    )


@shared_task(name="answer_question_task")
def answer_question_task(question_id: str) -> Optional[Question]:
    with DbSession() as session:
        qid = uuid.UUID(question_id)
        return get_qa_service(session).answer_question(qid)


@shared_task(name="answer_stale_questions_task")
def answer_stale_questions_task() -> None:
    with DbSession() as session:
        question_repository = QuestionRepository(session)
        stale_questions = question_repository.get_stale_questions()
        logger.info(f"Scheduling {len(stale_questions)} stale questions...")
        for question in stale_questions:
            answer_question_task.delay(str(question.id))
        logger.info(f"Scheduled {len(stale_questions)} stale questions")


class CeleryQuestionScheduler:
    """
    Infrastructure implementation: delegates to the Celery task.
    """

    def schedule_answer_question(self, question_id: uuid.UUID) -> None:
        answer_question_task.delay(str(question_id))
