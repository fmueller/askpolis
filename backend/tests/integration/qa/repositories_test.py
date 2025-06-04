import datetime

from sqlalchemy.orm import Session

from askpolis.core import Parliament
from askpolis.qa.models import Answer, AnswerContent, Question
from askpolis.qa.repositories import AnswerRepository, QuestionRepository


def test_question_model(db_session: Session) -> None:
    question = Question("a test question")
    question_id = question.id
    QuestionRepository(db_session).save(question)

    question_from_db = QuestionRepository(db_session).get(question_id)
    assert question_from_db is not None
    assert question_from_db.content == "a test question"

    assert len(QuestionRepository(db_session).get_all()) == 1


def test_answer_model(db_session: Session) -> None:
    parliament = Parliament(name="Parliament of Canada", short_name="Canada")
    db_session.add(parliament)

    question = Question("a test question")
    question_id = question.id

    answer = Answer(contents=[AnswerContent("en-US", "a test answer")], citations=[])
    answer.parliament_id = parliament.id
    question.answers.append(answer)
    answer_id = answer.id

    QuestionRepository(db_session).save(question)
    answer_from_db = AnswerRepository(db_session).get(answer_id)

    assert answer_from_db is not None
    assert answer_from_db.question_id == question_id
    assert len(answer_from_db.contents) == 1
    assert answer_from_db.contents[0].content == "a test answer"


def test_get_stale_questions(db_session: Session) -> None:
    parliament = Parliament(name="Parliament of Canada", short_name="Canada")
    db_session.add(parliament)

    now = datetime.datetime.now(datetime.UTC)
    three_hours_ago = now - datetime.timedelta(hours=3)
    one_hour_ago = now - datetime.timedelta(hours=1)

    question_repository = QuestionRepository(db_session)

    # Question 1: Old question without answer (should be returned)
    q1 = Question("old question without answer")
    q1.created_at = three_hours_ago
    q1.updated_at = three_hours_ago
    question_repository.save(q1)

    # Question 2: Old question with answer (should not be returned)
    q2 = Question("old question with answer")
    q2.created_at = three_hours_ago
    q2.updated_at = three_hours_ago
    a2 = Answer(contents=[AnswerContent("en-US", "an answer")], citations=[])
    a2.parliament_id = parliament.id
    q2.answers.append(a2)
    question_repository.save(q2)

    # Question 3: Recent question without answer (should not be returned)
    q3 = Question("recent question without answer")
    q3.created_at = one_hour_ago
    q3.updated_at = one_hour_ago
    question_repository.save(q3)

    # Question 4: Recent question with answer (should not be returned)
    q4 = Question("recent question with answer")
    q4.created_at = one_hour_ago
    q4.updated_at = one_hour_ago
    a4 = Answer(contents=[AnswerContent("en-US", "an answer")], citations=[])
    a4.parliament_id = parliament.id
    q4.answers.append(a4)
    question_repository.save(q4)

    stale_questions = question_repository.get_stale_questions()
    assert len(stale_questions) == 1
    assert stale_questions[0].id == q1.id
    assert stale_questions[0].content == "old question without answer"
