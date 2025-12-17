"""Tests for QA Celery tasks."""

import uuid
from collections.abc import Iterator
from typing import Any

from askpolis.core import Tenant


TENANT_ID = uuid.uuid4()

from askpolis.qa import dependencies as qa_dependencies
from askpolis.qa import tasks as qa_tasks


class DummyAnswerContent:
    def __init__(self, content: str) -> None:
        self.content = content


class DummyAnswer:
    def __init__(self, contents: list[DummyAnswerContent]) -> None:
        self.contents = contents


class DummyQuestion:
    def __init__(self, qid: uuid.UUID, tenant_id: uuid.UUID, answers: list[DummyAnswer]) -> None:
        self.id = qid
        self.tenant_id = tenant_id
        self.answers = answers


class DummyQAService:
    def __init__(self, question: DummyQuestion) -> None:
        self._question = question

    def answer_question(self, tenant: Tenant, qid: uuid.UUID) -> DummyQuestion:
        assert qid == self._question.id
        assert tenant.id == self._question.tenant_id
        return self._question


class DummyTenantRepository:
    def __init__(self, _) -> None:  # pragma: no cover - simple stub
        self._tenant = Tenant(id=TENANT_ID, name="demo", supported_parliaments=[uuid.uuid4()])

    def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        return self._tenant if tenant_id == self._tenant.id else None


class DummySession:
    def close(self) -> None:  # pragma: no cover - simple stub
        pass


class DummyQuestionRepository:
    def __init__(self, session: DummySession, question: DummyQuestion) -> None:
        self._question = question

    def get(self, question_id: uuid.UUID) -> DummyQuestion | None:
        return self._question if question_id == self._question.id else None


def fake_get_db() -> Iterator[DummySession]:
    yield DummySession()


def test_answer_question_task_returns_result(monkeypatch: Any) -> None:
    qid = uuid.uuid4()
    question = DummyQuestion(qid, TENANT_ID, [DummyAnswer([DummyAnswerContent("hi")])])
    monkeypatch.setattr(qa_tasks, "get_db", fake_get_db)
    monkeypatch.setattr(qa_dependencies, "get_qa_service", lambda session: DummyQAService(question))
    monkeypatch.setattr(qa_tasks, "TenantRepository", DummyTenantRepository)
    monkeypatch.setattr(qa_tasks, "QuestionRepository", lambda session: DummyQuestionRepository(session, question))

    result = qa_tasks.answer_question_task(str(qid))

    assert result["status"] == "answered"
    assert result["entity_id"] == str(qid)
    assert result["data"]["answers"] == ["hi"]


def test_answer_stale_questions_task_returns_ids(monkeypatch: Any) -> None:
    qids = [uuid.uuid4(), uuid.uuid4()]

    class DummyQuestionRepository:
        def __init__(self, session: DummySession) -> None:
            pass

        def get_stale_questions(self) -> list[DummyQuestion]:
            return [DummyQuestion(qids[0], TENANT_ID, []), DummyQuestion(qids[1], TENANT_ID, [])]

    scheduled: list[str] = []

    def fake_delay(qid: str) -> None:  # pragma: no cover - simple stub
        scheduled.append(qid)

    monkeypatch.setattr(qa_tasks, "get_db", fake_get_db)
    monkeypatch.setattr(qa_tasks, "QuestionRepository", DummyQuestionRepository)
    monkeypatch.setattr(qa_tasks.answer_question_task, "delay", fake_delay)

    result = qa_tasks.answer_stale_questions_task()

    assert result["status"] == "scheduled"
    assert result["data"]["question_ids"] == [str(q) for q in qids]
    assert scheduled == [str(q) for q in qids]
