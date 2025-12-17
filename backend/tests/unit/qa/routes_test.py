import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from askpolis.core import Tenant, get_document_repository, get_tenant
from askpolis.main import app
from askpolis.qa.dependencies import get_question_repository
from askpolis.qa.models import Answer, AnswerContent, Question
from askpolis.search import get_embeddings_repository


class DummyQuestionRepository:
    def __init__(self, question: Question) -> None:
        self.question = question

    def get(self, question_id: uuid.UUID) -> Question | None:
        if question_id == self.question.id:
            return self.question
        return None

    def get_for_tenant(self, tenant_id: uuid.UUID, question_id: uuid.UUID) -> Question | None:
        if tenant_id != self.question.tenant_id:
            return None
        return self.get(question_id)


def test_get_question_returns_answer() -> None:
    tenant = Tenant(id=uuid.uuid4(), name="demo", supported_parliaments=[uuid.uuid4()])
    question = Question(tenant, "What is the answer?")
    answer = Answer(contents=[AnswerContent("en-US", "42")], citations=[])
    answer.question_id = question.id
    question.answers.append(answer)

    app.dependency_overrides[get_question_repository] = lambda: DummyQuestionRepository(question)
    app.dependency_overrides[get_document_repository] = lambda: MagicMock()
    app.dependency_overrides[get_embeddings_repository] = lambda: MagicMock()
    app.dependency_overrides[get_tenant] = lambda: tenant

    client = TestClient(app)
    response = client.get(f"/v0/questions/{question.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["answer"]["answer"] == "42"
    assert data["status"] == "answered"

    app.dependency_overrides.clear()


def test_get_answer_trims_language_code() -> None:
    tenant = Tenant(id=uuid.uuid4(), name="demo", supported_parliaments=[uuid.uuid4()])
    question = Question(tenant=tenant, content="test")
    answer = Answer(contents=[AnswerContent(language="de   ", content="hi")], citations=[])
    answer.question_id = question.id
    question.answers.append(answer)

    app.dependency_overrides[get_question_repository] = lambda: DummyQuestionRepository(question)
    app.dependency_overrides[get_document_repository] = lambda: MagicMock()
    app.dependency_overrides[get_embeddings_repository] = lambda: MagicMock()
    app.dependency_overrides[get_tenant] = lambda: tenant

    client = TestClient(app)
    response = client.get(f"/v0/questions/{question.id}/answer")
    assert response.status_code == 200

    data = response.json()
    # language must have been stripped
    assert data["language"] == "de"

    app.dependency_overrides.clear()


def test_question_for_other_tenant_is_not_accessible() -> None:
    tenant = Tenant(id=uuid.uuid4(), name="demo", supported_parliaments=[uuid.uuid4()])
    other_tenant = Tenant(id=uuid.uuid4(), name="other", supported_parliaments=[uuid.uuid4()])
    question = Question(tenant=tenant, content="hidden")

    app.dependency_overrides[get_question_repository] = lambda: DummyQuestionRepository(question)
    app.dependency_overrides[get_document_repository] = lambda: MagicMock()
    app.dependency_overrides[get_embeddings_repository] = lambda: MagicMock()
    app.dependency_overrides[get_tenant] = lambda: other_tenant

    client = TestClient(app)
    response = client.get(f"/v0/questions/{question.id}")
    assert response.status_code == 404

    app.dependency_overrides.clear()
