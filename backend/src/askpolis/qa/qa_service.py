import uuid
from typing import Optional

from askpolis.core.repositories import ParliamentRepository
from askpolis.logging import get_logger
from askpolis.qa.agents import AnswerAgent
from askpolis.qa.models import Question
from askpolis.qa.repositories import QuestionRepository
from askpolis.qa.schedulers import QuestionScheduler

logger = get_logger(__name__)


class QAService:
    def __init__(
        self,
        question_repository: QuestionRepository,
        parliament_repository: ParliamentRepository,
        question_scheduler: QuestionScheduler,
        answer_agent: AnswerAgent,
    ) -> None:
        self._question_repository = question_repository
        self._parliament_repository = parliament_repository
        self._question_scheduler = question_scheduler
        self._answer_agent = answer_agent

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
        self._question_scheduler.schedule_answer_question(question.id)
        return question

    def answer_question(self, question_id: uuid.UUID) -> Optional[Question]:
        question = self._question_repository.get(question_id)
        if question is None:
            logger.warning_with_attrs("Question not found", {"question_id": question_id})
            return None

        # for now, this is ok - later this will come from the tenant configuration and the api
        bundestag = self._parliament_repository.get_by_name("Bundestag")
        if bundestag is None:
            raise Exception("Parliament 'Bundestag' not found")

        # currently, we only support parliament dimension for questions, needs to be extended later
        if any(a.parliament_id == bundestag.id for a in question.answers):
            logger.info_with_attrs("Question already answered", {"question_id": question_id})
            return question

        answer = self._answer_agent.answer(question)
        if answer is not None:
            answer.parliament_id = bundestag.id
            question.answers.append(answer)
            self._question_repository.save(question)

        return question
