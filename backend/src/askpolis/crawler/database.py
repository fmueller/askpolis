import datetime
import uuid
from typing import Any, Optional

from sqlalchemy import UUID, Column, DateTime, LargeBinary, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class CrawlingResult(Base):
    __tablename__ = "crawling_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crawler = Column(String, nullable=False)
    entity = Column(String, nullable=True)
    source = Column(String, nullable=False)
    text_data = Column(String, nullable=True)
    json_data: Optional[list[dict[str, Any]]] = Column(JSONB, nullable=True)
    file_data = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

    def __repr__(self) -> str:
        return (
            f"<CrawlingResult(id={self.id}, crawler={self.crawler}, entity={self.entity}, "
            f"source={self.source}, created_at={self.created_at})>"
        )


class CrawlerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, crawling_result: CrawlingResult) -> None:
        self.session.add(crawling_result)
        self.session.commit()

    def get_by_id(self, id: uuid.UUID) -> Optional[CrawlingResult]:
        return self.session.query(CrawlingResult).filter_by(id=id).first()

    def get_by_crawler_and_entity(self, crawler: str, entity: str) -> Optional[CrawlingResult]:
        return (
            self.session.query(CrawlingResult)
            .filter_by(crawler=crawler, entity=entity)
            .order_by(CrawlingResult.created_at.desc())
            .first()
        )

    def get_all(self) -> list[CrawlingResult]:
        return self.session.query(CrawlingResult).all()

    def update(self, crawling_result: CrawlingResult) -> None:
        self.session.merge(crawling_result)
        self.session.commit()

    def delete(self, id: uuid.UUID) -> None:
        crawling_result = self.get_by_id(id)
        if crawling_result:
            self.session.delete(crawling_result)
            self.session.commit()
