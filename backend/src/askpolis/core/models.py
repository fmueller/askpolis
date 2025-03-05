import datetime
from typing import Any, Optional

import uuid_utils.compat as uuid
from langchain_core.documents import Document as LangchainDocument
from pydantic import BaseModel
from sqlalchemy import UUID as DB_UUID
from sqlalchemy import Column, Date, DateTime, ForeignKey, LargeBinary, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class Page(BaseModel):
    page_number: int
    content: str
    metadata: dict[str, Any]


class Document(BaseModel):
    pages: list[Page]
    path: str

    def to_langchain_documents(self) -> list[LangchainDocument]:
        return [LangchainDocument(page_content=page.content, metadata=page.metadata) for page in self.pages]


class Parliament(Base):
    __tablename__ = "parliaments"

    def __init__(self, name: str, short_name: str, **kw: Any) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.name = name
        self.short_name = short_name
        self.updated_at = datetime.datetime.now(datetime.UTC)

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))


class Party(Base):
    __tablename__ = "parties"

    def __init__(self, name: str, short_name: str, **kw: Any) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.name = name
        self.short_name = short_name
        self.updated_at = datetime.datetime.now(datetime.UTC)

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))


class ParliamentPeriod(Base):
    __tablename__ = "parliament_periods"

    def __init__(
        self,
        parliament: Parliament,
        label: str,
        period_type: str,
        start_date: datetime.date,
        end_date: datetime.date,
        election_date: Optional[datetime.date] = None,
        **kw: Any,
    ) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.parliament_id = parliament.id
        self.label = label
        self.period_type = period_type
        self.start_date = start_date
        self.end_date = end_date
        self.election_date = election_date
        self.updated_at = datetime.datetime.now(datetime.UTC)

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    parliament_id: Mapped[uuid.UUID] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("parliaments.id"), nullable=False
    )
    label = Column(String, nullable=False)
    period_type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    election_date = Column(Date, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

    def __repr__(self) -> str:
        return (
            f"<ParliamentPeriod(id={self.id}, parliament_id={self.parliament_id}, label={self.label}, "
            f"period_type={self.period_type}, start_date={self.start_date}, end_date={self.end_date}, "
            f"election_date={self.election_date}, updated_at={self.updated_at})>"
        )


class ElectionProgram(Base):
    __tablename__ = "election_programs"

    def __init__(
        self, parliament_period: ParliamentPeriod, party: Party, label: str, file_name: str, file_data: bytes, **kw: Any
    ) -> None:
        super().__init__(**kw)
        self.parliament_period_id = parliament_period.id
        self.party_id = party.id
        self.label = label
        self.file_name = file_name
        self.file_data = file_data
        self.updated_at = datetime.datetime.now(datetime.UTC)

    parliament_period_id: Mapped[uuid.UUID] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("parliament_periods.id"), nullable=False
    )
    party_id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), ForeignKey("parties.id"), nullable=False)
    label = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

    __table_args__ = (PrimaryKeyConstraint("parliament_period_id", "party_id", "label"),)
