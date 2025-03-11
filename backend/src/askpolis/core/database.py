import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from askpolis.core import Document, ElectionProgram, Page, Parliament, ParliamentPeriod, Party


class PageRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, page_id: uuid.UUID) -> Optional[Page]:
        return self.db.query(Page).filter(Page.id == page_id).first()

    def get_by_document_id(self, document_id: uuid.UUID) -> list[Page]:
        return self.db.query(Page).filter(Page.document_id == document_id).all()

    def save_all(self, pages: list[Page]) -> None:
        self.db.add_all(pages)
        self.db.commit()


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Document]:
        return self.db.query(Document).all()

    def get(self, document_id: uuid.UUID) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_by_name(self, name: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.name == name).first()

    def save(self, document: Document) -> None:
        self.db.add(document)
        self.db.commit()


class ParliamentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Parliament]:
        return self.db.query(Parliament).all()

    def get_by_name(self, name: str) -> Optional[Parliament]:
        return self.db.query(Parliament).filter(Parliament.name == name).first()

    def save(self, parliament: Parliament) -> None:
        self.db.add(parliament)
        self.db.commit()


class PartyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Party]:
        return self.db.query(Party).all()

    def get_by_name(self, name: str) -> Optional[Party]:
        return self.db.query(Party).filter(Party.name == name).first()

    def save(self, party: Party) -> None:
        self.db.add(party)
        self.db.commit()


class ParliamentPeriodRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, parliament: Parliament) -> list[ParliamentPeriod]:
        return self.db.query(ParliamentPeriod).filter(ParliamentPeriod.parliament_id == parliament.id).all()

    def get_by_type_and_date_period(
        self, parliament: Parliament, period_type: str, start_date: date, end_date: date
    ) -> Optional[ParliamentPeriod]:
        return (
            self.db.query(ParliamentPeriod)
            .filter(
                ParliamentPeriod.parliament_id == parliament.id,
                ParliamentPeriod.period_type == period_type,
                ParliamentPeriod.start_date == start_date,
                ParliamentPeriod.end_date == end_date,
            )
            .first()
        )

    def save(self, parliament_period: ParliamentPeriod) -> None:
        self.db.add(parliament_period)
        self.db.commit()


class ElectionProgramRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(
        self, party: Party, parliament_period: ParliamentPeriod, label: str = "default"
    ) -> Optional[ElectionProgram]:
        return (
            self.db.query(ElectionProgram)
            .filter(
                ElectionProgram.party_id == party.id,
                ElectionProgram.parliament_period_id == parliament_period.id,
                ElectionProgram.label == label,
            )
            .first()
        )

    def save(self, election_program: ElectionProgram) -> None:
        self.db.add(election_program)
        self.db.commit()
