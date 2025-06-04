import datetime
import uuid
from typing import Optional

from sqlalchemy import not_
from sqlalchemy.orm import Session

from .models import Answer, Question


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
        two_hours_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=2)
        return self.db.query(Question).filter(not_(Question.answers.any()), Question.created_at <= two_hours_ago).all()


class AnswerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, answer_id: uuid.UUID) -> Optional[Answer]:
        return self.db.query(Answer).filter(Answer.id == answer_id).first()

    def save(self, answer: Answer) -> None:
        self.db.add(answer)
        self.db.commit()
