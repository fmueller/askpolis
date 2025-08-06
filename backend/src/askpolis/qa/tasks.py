import uuid
from typing import Any

from celery import shared_task

from askpolis.db import get_db
from askpolis.logging import get_logger
from askpolis.task_utils import build_task_result

from .models import Question
from .repositories import QuestionRepository

logger = get_logger(__name__)


@shared_task(name="answer_question_task")
def answer_question_task(question_id: str) -> dict[str, Any]:
    from .dependencies import get_qa_service

    session = next(get_db())
    try:
        qid = uuid.UUID(question_id)
        question: Question | None = get_qa_service(session).answer_question(qid)
        answers = [content.content for answer in question.answers for content in answer.contents] if question else []
        status = "answered" if answers else "no_answer"
        entity_id = str(question.id) if question else question_id
        return build_task_result(status, entity_id, {"answers": answers})
    finally:
        session.close()


@shared_task(name="answer_stale_questions_task")
def answer_stale_questions_task() -> dict[str, Any]:
    session = next(get_db())
    try:
        question_repository = QuestionRepository(session)
        stale_questions = question_repository.get_stale_questions()
        logger.info(f"Scheduling {len(stale_questions)} stale questions...")
        scheduled = [str(question.id) for question in stale_questions]
        for qid in scheduled:
            answer_question_task.delay(qid)
        logger.info(f"Scheduled {len(stale_questions)} stale questions")
        return build_task_result("scheduled", None, {"question_ids": scheduled})
    finally:
        session.close()


class CeleryQuestionScheduler:
    """
    Infrastructure implementation: delegates to the Celery task.
    """

    def schedule_answer_question(self, question_id: uuid.UUID) -> None:
        answer_question_task.delay(str(question_id))
