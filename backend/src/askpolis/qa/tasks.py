import uuid
from typing import Optional

from celery import shared_task
from askpolis.db import get_db

from askpolis.logging import get_logger

from .models import Question
from .repositories import QuestionRepository

logger = get_logger(__name__)


@shared_task(name="answer_question_task")
def answer_question_task(question_id: str) -> Optional[Question]:
    from .dependencies import get_qa_service

    session = next(get_db())
    try:
        qid = uuid.UUID(question_id)
        return get_qa_service(session).answer_question(qid)
    finally:
        session.close()


@shared_task(name="answer_stale_questions_task")
def answer_stale_questions_task() -> None:
    session = next(get_db())
    try:
        question_repository = QuestionRepository(session)
        stale_questions = question_repository.get_stale_questions()
        logger.info(f"Scheduling {len(stale_questions)} stale questions...")
        for question in stale_questions:
            answer_question_task.delay(str(question.id))
        logger.info(f"Scheduled {len(stale_questions)} stale questions")
    finally:
        session.close()


class CeleryQuestionScheduler:
    """
    Infrastructure implementation: delegates to the Celery task.
    """

    def schedule_answer_question(self, question_id: uuid.UUID) -> None:
        answer_question_task.delay(str(question_id))
