import os

from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import CrawlerRepository
from .abgeordnetenwatch import AbgeordnetenwatchCrawler

DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql+psycopg://postgres@postgres:5432/askpolis"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@shared_task(name="crawl_bundestag_election_programs_from_abgeordnetenwatch")
def crawl_bundestag_election_programs_from_abgeordnetenwatch() -> None:
    bundestag_id = 5
    session = SessionLocal()
    try:
        crawler = AbgeordnetenwatchCrawler(CrawlerRepository(session))
        crawler.crawl_election_programs(bundestag_id)
    finally:
        session.close()
