import datetime
import enum
from typing import Any, Optional

import uuid_utils.compat as uuid
from langchain_core.documents import Document as LangchainDocument
from pydantic import BaseModel, Field
from sqlalchemy import UUID as DB_UUID
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, LargeBinary, PrimaryKeyConstraint, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class Page(Base):
    __tablename__ = "pages"

    def __init__(
        self,
        document_id: uuid.UUID,
        page_number: int,
        content: str,
        page_metadata: Optional[dict[str, Any]] = None,
        **kw: Any,
    ) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.document_id = document_id
        self.page_number = page_number
        self.content = content
        self.page_metadata = page_metadata
        self.updated_at = datetime.datetime.now(datetime.UTC)

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    page_number: int = Column(Integer, nullable=False)
    content: str = Column(String, nullable=False)
    page_metadata = Column(JSONB, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))

    def to_langchain_document(self) -> LangchainDocument:
        return LangchainDocument(page_content=self.content, metadata=self.page_metadata)


class DocumentType(str, enum.Enum):
    ELECTION_PROGRAM = "election-program"

    @classmethod
    def values(cls) -> list[str]:
        return [e.value for e in cls]


class Document(Base):
    __tablename__ = "documents"

    def __init__(
        self,
        name: str,
        document_type: DocumentType,
        reference_id_1: Optional[uuid.UUID] = None,
        reference_id_2: Optional[uuid.UUID] = None,
        **kw: Any,
    ) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid7()
        self.name = name
        self.document_type = document_type
        self.reference_id_1 = reference_id_1
        self.reference_id_2 = reference_id_2
        self.updated_at = datetime.datetime.now(datetime.UTC)

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    document_type = Column(
        postgresql.ENUM(*DocumentType.values(), name="documenttypetype", create_type=False), nullable=False
    )
    reference_id_1: Mapped[Optional[uuid.UUID]] = mapped_column(DB_UUID(as_uuid=True), nullable=True)
    reference_id_2: Mapped[Optional[uuid.UUID]] = mapped_column(DB_UUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))


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


class ParliamentResponse(BaseModel):
    id: uuid.UUID
    name: str
    short_name: str


class CreateParliamentRequest(BaseModel):
    name: str = Field()
    short_name: str = Field()
