from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from askpolis.core import ParliamentRepository, get_db
from askpolis.search import SearchServiceBase, get_search_service

from .agents import AnswerAgent
from .qa_service import QAService
from .repositories import QuestionRepository
from .tasks import CeleryQuestionScheduler


def get_qa_service(
    db: Annotated[Session, Depends(get_db)],
    search_service: Annotated[SearchServiceBase, Depends(get_search_service)],
) -> QAService:
    question_repository = QuestionRepository(db)
    parliament_repository = ParliamentRepository(db)
    return QAService(question_repository, parliament_repository, CeleryQuestionScheduler(), AnswerAgent(search_service))
