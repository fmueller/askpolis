import datetime
from typing import Any, Optional

import uuid_utils.compat as uuid
from pydantic import BaseModel, Field
from sqlalchemy import CHAR, CheckConstraint, Column, DateTime, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy import UUID as DB_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from askpolis.core import Base, Document, Parliament, ParliamentPeriod, Party
from askpolis.search import SearchResult


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
    updated_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (UniqueConstraint("answer_id", "language", name="uq_answer_contents_answer_id_lang"),)

    def __repr__(self) -> str:
        return (
            f"<AnswerContent(id={self.id!r}, language={self.language!r}, answer_id={self.answer_id!r}, "
            f"translated_from={self.translated_from!r})>"
        )


class Citation(Base):
    __tablename__ = "citations"

    def __init__(self, search_result: SearchResult, **kw: Any) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.embeddings_id = search_result.chunk_id
        self.document_id = search_result.document_id
        self.page_id = search_result.page_id
        self.created_at = datetime.datetime.now(datetime.UTC)

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    answer_id: Mapped[uuid.UUID] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), nullable=False
    )
    embeddings_id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), ForeignKey("embeddings.id"), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    page_id: Mapped[Optional[uuid.UUID]] = mapped_column(DB_UUID(as_uuid=True), ForeignKey("pages.id"), nullable=True)
    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (
        UniqueConstraint(
            "answer_id",
            "embeddings_id",
            "document_id",
            "page_id",
            name="uq_citations_dims",
        ),
    )


class Answer(Base):
    __tablename__ = "answers"

    def __init__(self, contents: list[AnswerContent], citations: list[Citation], **kw: Any) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.contents = contents
        self.citations = citations
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
    contents: Mapped[list[AnswerContent]] = relationship("AnswerContent", cascade="all, delete-orphan")
    citations: Mapped[list[Citation]] = relationship("Citation", cascade="all, delete-orphan")
    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))
    updated_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

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
    updated_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

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


class CitationResponse(BaseModel):
    title: str
    content: str


class AnswerResponse(BaseModel):
    answer: str | None = None
    language: str | None = None
    status: str
    citations: list[CitationResponse] = []
    created_at: str | None = None
    updated_at: str | None = None


class QuestionResponse(BaseModel):
    id: uuid.UUID
    content: str
    status: str
    created_at: str
    updated_at: str
    answer_url: str | None = None
    answer: AnswerResponse | None = None


class CreateQuestionRequest(BaseModel):
    question: str = Field()
