import uuid
from typing import Protocol


class QuestionScheduler(Protocol):
    def schedule_answer_question(self, question_id: uuid.UUID) -> None: ...
