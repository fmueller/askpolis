from celery import shared_task
from askpolis.db import get_db

from askpolis.data_fetcher import FetchedDataRepository
from askpolis.data_fetcher.abgeordnetenwatch import AbgeordnetenwatchDataFetcher



@shared_task(name="fetch_bundestag_from_abgeordnetenwatch")
def fetch_bundestag_from_abgeordnetenwatch() -> None:
    bundestag_id = 5
    session = next(get_db())
    try:
        data_fetcher = AbgeordnetenwatchDataFetcher(FetchedDataRepository(session))
        data_fetcher.fetch_election_programs(bundestag_id)
    finally:
        session.close()


@shared_task(name="cleanup_outdated_data")
def cleanup_outdated_data() -> None:
    session = next(get_db())
    try:
        FetchedDataRepository(session).delete_outdated_data()
    finally:
        session.close()
