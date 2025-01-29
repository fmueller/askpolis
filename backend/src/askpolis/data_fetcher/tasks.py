import os

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from askpolis.data_fetcher import FetchedDataRepository
from askpolis.data_fetcher.abgeordnetenwatch import AbgeordnetenwatchDataFetcher

engine = create_engine(os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres@postgres:5432/askpolis-db")
SessionLocal = sessionmaker(bind=engine)


@shared_task(name="fetch_bundestag_from_abgeordnetenwatch")
def fetch_bundestag_from_abgeordnetenwatch() -> None:
    bundestag_id = 5
    session = SessionLocal()
    try:
        data_fetcher = AbgeordnetenwatchDataFetcher(FetchedDataRepository(session))
        data_fetcher.fetch_election_programs(bundestag_id)
    finally:
        session.close()
