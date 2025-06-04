from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from askpolis.core import ParliamentRepository, get_db
from askpolis.search import EmbeddingsRepository, get_search_service

from .agents import AnswerAgent
from .qa_service import QAService
from .repositories import QuestionRepository
from .tasks import CeleryQuestionScheduler


def get_qa_service(
    db: Annotated[Session, Depends(get_db)],
) -> QAService:
    question_repository = QuestionRepository(db)
    parliament_repository = ParliamentRepository(db)
    embeddings_repository = EmbeddingsRepository(db)
    return QAService(
        question_repository,
        parliament_repository,
        CeleryQuestionScheduler(),
        AnswerAgent(get_search_service(db, embeddings_repository)),
    )
