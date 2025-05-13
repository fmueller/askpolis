import datetime
from typing import Any, Optional

import uuid_utils.compat as uuid
from sqlalchemy import CHAR, CheckConstraint, Column, DateTime, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy import UUID as DB_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from askpolis.core import Base, Document, Parliament, ParliamentPeriod, Party


class AnswerContent(Base):
    __tablename__ = "answer_contents"

    def __init__(self, language: str, content: str, **kw: Any) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.language = language
        self.content = content
        self.created_at = datetime.datetime.now(datetime.UTC)
        self.updated_at = self.created_at

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    answer_id: Mapped[uuid.UUID] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(CHAR(5), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    translated_from: Mapped[Optional[uuid.UUID]] = mapped_column(DB_UUID(as_uuid=True), nullable=True)
    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (UniqueConstraint("answer_id", "language", name="uq_answer_contents_answer_id_lang"),)

    def __repr__(self) -> str:
        return (
            f"<AnswerContent(id={self.id!r}, language={self.language!r}, answer_id={self.answer_id!r}, "
            f"translated_from={self.translated_from!r})>"
        )


class Answer(Base):
    __tablename__ = "answers"

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.created_at = datetime.datetime.now(datetime.UTC)
        self.updated_at = self.created_at

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    question_id: Mapped[uuid.UUID] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    parliament_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("parliaments.id", ondelete="CASCADE"), nullable=True
    )
    parliament_period_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("parliament_periods.id", ondelete="CASCADE"), nullable=True
    )
    party_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("parties.id", ondelete="CASCADE"), nullable=True
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True
    )
    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (
        UniqueConstraint(
            "question_id",
            "parliament_id",
            "parliament_period_id",
            "party_id",
            "document_id",
            name="uq_answers_dims",
        ),
        CheckConstraint(
            "(parliament_id IS NOT NULL OR parliament_period_id IS NOT NULL "
            "OR party_id IS NOT NULL OR document_id IS NOT NULL)",
            name="ck_answers_at_least_one_dimension",
        ),
    )

    contents: Mapped[list[AnswerContent]] = relationship("AnswerContent", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        dims = (
            self.parliament_id,
            self.parliament_period_id,
            self.party_id,
            self.document_id,
        )
        return f"<Answer(id={self.id!r}, question_id={self.question_id!r}, dims={dims!r})>"


question_parliament = Table(
    "question_parliament",
    Base.metadata,
    Column("question_id", DB_UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("parliament_id", DB_UUID(as_uuid=True), ForeignKey("parliaments.id", ondelete="CASCADE"), primary_key=True),
)

question_parliament_period = Table(
    "question_parliament_period",
    Base.metadata,
    Column("question_id", DB_UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "parliament_period_id",
        DB_UUID(as_uuid=True),
        ForeignKey("parliament_periods.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

question_party = Table(
    "question_party",
    Base.metadata,
    Column("question_id", DB_UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("party_id", DB_UUID(as_uuid=True), ForeignKey("parties.id", ondelete="CASCADE"), primary_key=True),
)

question_document = Table(
    "question_document",
    Base.metadata,
    Column("question_id", DB_UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", DB_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
)


class Question(Base):
    __tablename__ = "questions"

    def __init__(self, content: str, **kw: Any) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.content = content
        self.created_at = datetime.datetime.now(datetime.UTC)
        self.updated_at = self.created_at

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    content = mapped_column(String, nullable=False)
    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

    answers: Mapped[list[Answer]] = relationship(
        "Answer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    parliaments: Mapped[list[Parliament]] = relationship("Parliament", secondary=question_parliament)
    parliament_periods: Mapped[list[ParliamentPeriod]] = relationship(
        "ParliamentPeriod", secondary=question_parliament_period
    )
    parties: Mapped[list[Party]] = relationship("Party", secondary=question_party)
    documents: Mapped[list[Document]] = relationship("Document", secondary=question_document)

    def __repr__(self) -> str:
        return f"<Question(id={self.id!r}, content={self.content!r}), created_at={self.created_at.isoformat()!r}>"
