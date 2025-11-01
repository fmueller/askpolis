import os
from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

engine: Engine | None = None
DbSession: sessionmaker[Session] | None = None


def get_db() -> Generator[Session, Any, None]:
    """Yield a database session."""
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
