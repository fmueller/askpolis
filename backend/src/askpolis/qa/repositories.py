import uuid
from typing import Optional

from sqlalchemy.orm import Session

from askpolis.qa.models import Question


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
