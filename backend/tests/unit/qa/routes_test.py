import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from askpolis.core import get_document_repository
from askpolis.main import app
from askpolis.qa.dependencies import get_qa_service
from askpolis.qa.models import Answer, AnswerContent, Question
from askpolis.qa.routes import get_answer
from askpolis.search import get_embeddings_repository


class DummyQAService:
    def __init__(self, question: Question) -> None:
        self.question = question

    def get_question(self, question_id: uuid.UUID) -> Question | None:
        if question_id == self.question.id:
            return self.question
        return None


def test_get_question_returns_answer() -> None:
    question = Question("What is the answer?")
    answer = Answer(contents=[AnswerContent("en-US", "42")], citations=[])
    answer.question_id = question.id
    question.answers.append(answer)

    app.dependency_overrides[get_qa_service] = lambda: DummyQAService(question)
    app.dependency_overrides[get_document_repository] = lambda: MagicMock()
    app.dependency_overrides[get_embeddings_repository] = lambda: MagicMock()

    client = TestClient(app)
    response = client.get(f"/v0/questions/{question.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["answer"]["answer"] == "42"
    assert data["status"] == "answered"

    app.dependency_overrides.clear()


def test_get_answer_trims_language_code() -> None:
    question = Question(content="test")
    answer = Answer(contents=[AnswerContent(language="de   ", content="hi")], citations=[])
    question.answers.append(answer)

    response = get_answer(
        question=question,
        document_repository=MagicMock(),
        embeddings_repository=MagicMock(),
    )

    assert response.language == "de"
