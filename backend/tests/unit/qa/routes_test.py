from unittest.mock import MagicMock

from askpolis.qa.models import Answer, AnswerContent, Question
from askpolis.qa.routes import get_answer


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
