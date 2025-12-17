import uuid

from askpolis.core import ParliamentRepository, Tenant
from askpolis.logging import get_logger

from .agents import AnswerAgent
from .models import Question
from .repositories import QuestionRepository
from .schedulers import QuestionScheduler

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

    def get_question(self, tenant: Tenant, question_id: uuid.UUID) -> Question | None:
        return self._question_repository.get_for_tenant(tenant.id, question_id)

    def add_question(self, tenant: Tenant, user_question: str) -> Question:
        if len(tenant.supported_parliaments) == 0:
            raise Exception(f"Tenant '{tenant.name}' has no supported parliaments")

        parliament_id = tenant.supported_parliaments[0]
        parliament = self._parliament_repository.get(parliament_id)
        if parliament is None:
            raise Exception(f"Parliament with ID '{parliament_id}' not found")

        question = Question(tenant, user_question)
        question.parliaments.append(parliament)
        self._question_repository.save(question)
        self._question_scheduler.schedule_answer_question(question.id)
        return question

    def answer_question(self, tenant: Tenant, question_id: uuid.UUID) -> Question | None:
        question = self._question_repository.get_for_tenant(tenant.id, question_id)
        if question is None:
            logger.warning_with_attrs(
                "Question not found",
                {"question_id": question_id, "tenant_id": tenant.id},
            )
            return None

        if len(tenant.supported_parliaments) == 0:
            raise Exception(f"Tenant '{tenant.name}' has no supported parliaments")

        target_parliament_id = tenant.supported_parliaments[0]
        bundestag = self._parliament_repository.get(target_parliament_id)
        if bundestag is None:
            raise Exception(f"Parliament with ID '{target_parliament_id}' not found")

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
