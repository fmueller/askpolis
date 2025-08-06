from typing import Any

from celery import shared_task

from askpolis.data_fetcher import FetchedDataRepository
from askpolis.data_fetcher.abgeordnetenwatch import AbgeordnetenwatchDataFetcher
from askpolis.db import get_db
from askpolis.task_utils import build_task_result


@shared_task(name="fetch_bundestag_from_abgeordnetenwatch")
def fetch_bundestag_from_abgeordnetenwatch() -> dict[str, Any]:
    bundestag_id = 5
    session = next(get_db())
    try:
        data_fetcher = AbgeordnetenwatchDataFetcher(FetchedDataRepository(session))
        data_fetcher.fetch_election_programs(bundestag_id)
        return build_task_result("success", str(bundestag_id), {"action": "fetch_election_programs"})
    finally:
        session.close()


@shared_task(name="cleanup_outdated_data")
def cleanup_outdated_data() -> dict[str, Any]:
    session = next(get_db())
    try:
        FetchedDataRepository(session).delete_outdated_data()
        return build_task_result("success", None, {"action": "cleanup_outdated_data"})
    finally:
        session.close()
