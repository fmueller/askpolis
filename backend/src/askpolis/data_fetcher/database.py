import datetime
from typing import Any, Optional

import uuid_utils.compat as uuid
from sqlalchemy import UUID, Column, DateTime, LargeBinary, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class FetchedData(Base):
    __tablename__ = "fetched_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid7)
    data_fetcher = Column(String, nullable=False)
    entity = Column(String, nullable=True)
    source = Column(String, nullable=False)
    text_data = Column(String, nullable=True)
    json_data: Optional[list[dict[str, Any]]] = Column(JSONB, nullable=True)
    file_data = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

    def __repr__(self) -> str:
        return (
            f"<FetchedData(id={self.id}, data_fetcher={self.data_fetcher}, entity={self.entity}, "
            f"source={self.source}, created_at={self.created_at})>"
        )


class FetchedDataRepository:
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
