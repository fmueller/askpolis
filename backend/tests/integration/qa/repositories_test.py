from sqlalchemy.orm import Session, sessionmaker

from askpolis.qa.models import Question
from askpolis.qa.repositories import QuestionRepository


def test_question_model(session_maker: sessionmaker[Session]) -> None:
    question_id = None
    with session_maker() as session:
        question = Question("a test question")
        question_id = question.id
        QuestionRepository(session).save(question)

    with session_maker() as session:
        question_from_db = QuestionRepository(session).get(question_id)
        assert question_from_db is not None
        assert question_from_db.content == "a test question"

        assert len(QuestionRepository(session).get_all()) == 1
