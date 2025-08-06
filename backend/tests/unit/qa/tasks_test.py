"""Tests for QA Celery tasks."""

import uuid
from collections.abc import Iterator
from typing import Any

from askpolis.qa import dependencies as qa_dependencies
from askpolis.qa import tasks as qa_tasks


class DummyAnswerContent:
    def __init__(self, content: str) -> None:
        self.content = content


class DummyAnswer:
    def __init__(self, contents: list[DummyAnswerContent]) -> None:
        self.contents = contents


class DummyQuestion:
    def __init__(self, qid: uuid.UUID, answers: list[DummyAnswer]) -> None:
        self.id = qid
        self.answers = answers


class DummyQAService:
    def __init__(self, question: DummyQuestion) -> None:
        self._question = question

    def answer_question(self, qid: uuid.UUID) -> DummyQuestion:
        assert qid == self._question.id
        return self._question


class DummySession:
    def close(self) -> None:  # pragma: no cover - simple stub
        pass


def fake_get_db() -> Iterator[DummySession]:
    yield DummySession()


def test_answer_question_task_returns_result(monkeypatch: Any) -> None:
    qid = uuid.uuid4()
    question = DummyQuestion(qid, [DummyAnswer([DummyAnswerContent("hi")])])
    monkeypatch.setattr(qa_tasks, "get_db", fake_get_db)
    monkeypatch.setattr(qa_dependencies, "get_qa_service", lambda session: DummyQAService(question))

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
            return [DummyQuestion(qids[0], []), DummyQuestion(qids[1], [])]

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
