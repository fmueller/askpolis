from sqlalchemy.orm import Session, sessionmaker

from askpolis.core import Parliament
from askpolis.qa.models import Answer, AnswerContent, Question
from askpolis.qa.repositories import AnswerRepository, QuestionRepository


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


def test_answer_model(session_maker: sessionmaker[Session]) -> None:
    question_id = None
    answer_id = None
    with session_maker() as session:
        parliament = Parliament(name="Parliament of Canada", short_name="Canada")
        session.add(parliament)
        question = Question("a test question")
        question_id = question.id
        session.add(question)
        answer = Answer(contents=[AnswerContent("en-US", "a test answer")], citations=[])
        answer.parliament_id = parliament.id
        question.answers.append(answer)
        answer_id = answer.id
        QuestionRepository(session).save(question)

    with session_maker() as session:
        answer_from_db = AnswerRepository(session).get(answer_id)

        assert answer_from_db is not None
        assert answer_from_db.question_id == question_id
        assert len(answer_from_db.contents) == 1
        assert answer_from_db.contents[0].content == "a test answer"
