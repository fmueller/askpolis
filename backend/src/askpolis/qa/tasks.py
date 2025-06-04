import os
import uuid
from typing import Optional

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from askpolis.logging import get_logger

from .models import Question
from .repositories import QuestionRepository

logger = get_logger(__name__)

engine = create_engine(os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres@postgres:5432/askpolis-db")
DbSession = sessionmaker(bind=engine)


@shared_task(name="answer_question_task")
def answer_question_task(question_id: str) -> Optional[Question]:
    from .dependencies import get_qa_service

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
