import datetime
import enum
from typing import Any, Optional

import uuid_utils.compat as uuid
from sqlalchemy import UUID, Boolean, Column, DateTime, LargeBinary, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from askpolis.logging import get_logger

Base = declarative_base()


class EntityType(str, enum.Enum):
    PARTY = "party"
    PARLIAMENT = "parliament"
    PARLIAMENT_PERIOD = "parliament-period"
    ELECTION_PROGRAM = "election-program"

    @classmethod
    def values(cls) -> list[str]:
        return [e.value for e in cls]


class DataFetcherType(str, enum.Enum):
    ABGEORDNETENWATCH = "abgeordnetenwatch"

    @classmethod
    def values(cls) -> list[str]:
        return [e.value for e in cls]


class FetchedData(Base):
    __tablename__ = "fetched_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=lambda: uuid.uuid7())
    data_fetcher = Column(String, nullable=False)
    data_fetcher_type = Column(
        postgresql.ENUM(*DataFetcherType.values(), name="datafetchertype", create_type=False), nullable=False
    )
    source = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.UTC))
    entity = Column(String, nullable=True)
    entity_type = Column(postgresql.ENUM(*EntityType.values(), name="entitytypetype", create_type=False), nullable=True)
    is_list = Column(Boolean, nullable=False, default=False)
    text_data = Column(String, nullable=True)
    json_data: Optional[list[dict[str, Any]]] = Column(JSONB, nullable=True)
    file_data = Column(LargeBinary, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<FetchedData(id={self.id}, data_fetcher_type={self.data_fetcher_type}, data_fetcher={self.data_fetcher}, "
            f"entity_type={self.entity_type}, is_list={self.is_list}, entity={self.entity}, "
            f"source={self.source}, created_at={self.created_at})>"
        )

    @classmethod
    def create_parliaments(
        cls,
        data_fetcher_type: DataFetcherType,
        source: str,
        text_data: Optional[str] = None,
        json_data: Optional[list[dict[str, Any]]] = None,
        file_data: Optional[bytes] = None,
    ) -> "FetchedData":
        return FetchedData(
            data_fetcher_type=data_fetcher_type,
            entity_type=EntityType.PARLIAMENT,
            entity=cls.get_entity_for_list_of_parliaments(),
            is_list=True,
            source=source,
            text_data=text_data,
            json_data=json_data,
            file_data=file_data,
        )

    @classmethod
    def create_parliament_periods(
        cls,
        data_fetcher_type: DataFetcherType,
        parliament_id: int,
        source: str,
        text_data: Optional[str] = None,
        json_data: Optional[list[dict[str, Any]]] = None,
        file_data: Optional[bytes] = None,
    ) -> "FetchedData":
        return FetchedData(
            data_fetcher_type=data_fetcher_type,
            entity_type=EntityType.PARLIAMENT_PERIOD,
            entity=cls.get_entity_for_list_of_parliament_periods(parliament_id),
            is_list=True,
            source=source,
            text_data=text_data,
            json_data=json_data,
            file_data=file_data,
        )

    @classmethod
    def create_election_programs(
        cls,
        data_fetcher_type: DataFetcherType,
        parliament_period_id: int,
        source: str,
        text_data: Optional[str] = None,
        json_data: Optional[list[dict[str, Any]]] = None,
        file_data: Optional[bytes] = None,
    ) -> "FetchedData":
        return FetchedData(
            data_fetcher_type=data_fetcher_type,
            entity_type=EntityType.ELECTION_PROGRAM,
            entity=cls.get_entity_for_list_of_election_programs(parliament_period_id),
            is_list=True,
            source=source,
            text_data=text_data,
            json_data=json_data,
            file_data=file_data,
        )

    @classmethod
    def create_election_program(
        cls,
        data_fetcher_type: DataFetcherType,
        party_id: int,
        parliament_period_id: int,
        label: str,
        source: str,
        text_data: Optional[str] = None,
        json_data: Optional[list[dict[str, Any]]] = None,
        file_data: Optional[bytes] = None,
    ) -> "FetchedData":
        return FetchedData(
            data_fetcher_type=data_fetcher_type,
            entity_type=EntityType.ELECTION_PROGRAM,
            entity=cls.get_entity_for_election_program(party_id, parliament_period_id, label),
            source=source,
            text_data=text_data,
            json_data=json_data,
            file_data=file_data,
        )

    @classmethod
    def get_entity_for_list_of_parliaments(cls) -> str:
        return "parliaments"

    @classmethod
    def get_entity_for_list_of_parliament_periods(cls, parliament_id: int) -> str:
        return f"parliament_periods.{parliament_id}"

    @classmethod
    def get_entity_for_list_of_election_programs(cls, parliament_period_id: int) -> str:
        return f"election_programs.{parliament_period_id}"

    @classmethod
    def get_entity_for_election_program(cls, party_id: int, parliament_period_id: int, label: str = "default") -> str:
        return f"party.{party_id}.parliament_period.{parliament_period_id}.label.{label}"


class FetchedDataRepository:
    _logger = get_logger(__name__)

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, fetched_data: FetchedData) -> None:
        self.session.add(fetched_data)
        self.session.commit()

    def get_all(self) -> list[FetchedData]:
        return self.session.query(FetchedData).all()

    def get_by_data_fetcher_and_entity(self, data_fetcher: str, entity: str) -> Optional[FetchedData]:
        return (
            self.session.query(FetchedData)
            .filter_by(data_fetcher=data_fetcher, entity=entity)
            .order_by(FetchedData.created_at.desc())
            .first()
        )

    def delete_outdated_data(self) -> list[tuple[DataFetcherType, int]]:
        deleted_rows: list[tuple[DataFetcherType, int]] = []
        for data_fetcher_type in DataFetcherType:
            self._logger.info_with_attrs(
                "Deleting outdated data for data fetcher:", {"data_fetcher": data_fetcher_type}
            )
            deleted_rows.append(self._delete_outdated_data_for_data_fetcher(data_fetcher_type))
        return deleted_rows

    def _delete_outdated_data_for_data_fetcher(self, data_fetcher_type: DataFetcherType) -> tuple[DataFetcherType, int]:
        last_fetched_data = (
            self.session.query(FetchedData)
            .filter_by(data_fetcher_type=data_fetcher_type)
            .order_by(FetchedData.created_at.desc())
            .first()
        )

        if last_fetched_data is None:
            self._logger.info_with_attrs("No data to delete for data fetcher:", {"data_fetcher": data_fetcher_type})
            return data_fetcher_type, 0

        rows = (
            self.session.query(FetchedData)
            .filter(
                FetchedData.data_fetcher_type == data_fetcher_type,
                FetchedData.data_fetcher != last_fetched_data.data_fetcher,
            )
            .delete(synchronize_session=False)
        )
        self._logger.info_with_attrs(
            "Deleted rows for data fetcher:", {"data_fetcher": data_fetcher_type, "rows": rows}
        )
        self.session.commit()
        return data_fetcher_type, rows
