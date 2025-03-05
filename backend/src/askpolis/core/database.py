from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from askpolis.core import Parliament, ParliamentPeriod


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
