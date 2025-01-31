import datetime
from typing import Any, Optional

import uuid_utils.compat as uuid
from sqlalchemy import UUID as DB_UUID
from sqlalchemy import Column, Date, DateTime, ForeignKey, LargeBinary, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class Parliament(Base):
    __tablename__ = "parliaments"

    def __init__(self, name: str, short_name: str, **kw: Any) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid5(uuid.NAMESPACE_OID, f"parliament-{name}{short_name}")
        self.name = name
        self.short_name = short_name

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)


class Party(Base):
    __tablename__ = "parties"

    def __init__(self, name: str, short_name: str, **kw: Any) -> None:
        super().__init__(**kw)
        self.id = uuid.uuid5(uuid.NAMESPACE_OID, f"party-{name}{short_name}")
        self.name = name
        self.short_name = short_name

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    short_name = Column(String, nullable=False)


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
        self.id = uuid.uuid5(
            uuid.NAMESPACE_OID,
            f"parliament-period-{parliament.id}{label}{period_type}{start_date}{end_date}{election_date}",
        )
        self.parliament_id = parliament.id
        self.label = label
        self.period_type = period_type
        self.start_date = start_date
        self.end_date = end_date
        self.election_date = election_date

    id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), primary_key=True)
    parliament_id: Mapped[uuid.UUID] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("parliaments.id"), nullable=False
    )
    label = Column(String, nullable=False)
    period_type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    election_date = Column(Date, nullable=True)


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

    parliament_period_id: Mapped[uuid.UUID] = mapped_column(
        DB_UUID(as_uuid=True), ForeignKey("parliament_periods.id"), nullable=False
    )
    party_id: Mapped[uuid.UUID] = mapped_column(DB_UUID(as_uuid=True), ForeignKey("parties.id"), nullable=False)
    label = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

    __table_args__ = (PrimaryKeyConstraint("parliament_period_id", "party_id", "label"),)
