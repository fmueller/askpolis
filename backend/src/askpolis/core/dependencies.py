import os
from collections.abc import Generator
from typing import Annotated, Any, Optional

from fastapi import Depends
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .repositories import DocumentRepository, ParliamentRepository

engine: Optional[Engine] = None
DbSession: Optional[sessionmaker[Session]] = None


def get_db() -> Generator[Session, Any, None]:
    global engine, DbSession
    if not engine:
        try:
            engine = create_engine(
                os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres@postgres:5432/askpolis-db"
            )
        except Exception as e:
            raise Exception("Error while connecting to database") from e

    if not DbSession:
        DbSession = sessionmaker(bind=engine)

    db = DbSession()
    try:
        yield db
    finally:
        db.close()


def get_document_repository(db: Annotated[Session, Depends(get_db)]) -> DocumentRepository:
    return DocumentRepository(db)


def get_parliament_repository(db: Annotated[Session, Depends(get_db)]) -> ParliamentRepository:
    return ParliamentRepository(db)
