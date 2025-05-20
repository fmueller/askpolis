import uuid
from typing import Optional

from sqlalchemy import not_
from sqlalchemy.orm import Session

from askpolis.qa.models import Answer, Question


class QuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Question]:
        return self.db.query(Question).all()

    def get(self, question_id: uuid.UUID) -> Optional[Question]:
        return self.db.query(Question).filter(Question.id == question_id).first()

    def save(self, question: Question) -> None:
        self.db.add(question)
        self.db.commit()

    def get_stale_questions(self) -> list[Question]:
        return self.db.query(Question).filter(not_(Question.answers.any())).all()


class AnswerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, answer_id: uuid.UUID) -> Optional[Answer]:
        return self.db.query(Answer).filter(Answer.id == answer_id).first()

    def save(self, answer: Answer) -> None:
        self.db.add(answer)
        self.db.commit()
