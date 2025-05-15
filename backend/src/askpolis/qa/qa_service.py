import uuid
from typing import Optional

from askpolis.core.repositories import ParliamentRepository
from askpolis.qa.models import Question
from askpolis.qa.repositories import QuestionRepository


class QAService:
    def __init__(self, question_repository: QuestionRepository, parliament_repository: ParliamentRepository) -> None:
        self._question_repository = question_repository
        self._parliament_repository = parliament_repository

    def get_question(self, question_id: uuid.UUID) -> Optional[Question]:
        return self._question_repository.get(question_id)

    def add_question(self, user_question: str) -> Question:
        # for now, this is ok - later this will come from the tenant configuration and the api
        bundestag = self._parliament_repository.get_by_name("Bundestag")
        if bundestag is None:
            raise Exception("Parliament 'Bundestag' not found")
        question = Question(content=user_question)
        question.parliaments.append(bundestag)
        self._question_repository.save(question)
        return question
