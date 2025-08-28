"""Tests for data_fetcher Celery tasks."""

from collections.abc import Iterator
from typing import Any

from askpolis.data_fetcher import tasks as df_tasks


class DummySession:
    def close(self) -> None:  # pragma: no cover - simple stub
        pass


def fake_get_db() -> Iterator[DummySession]:
    yield DummySession()


def test_fetch_bundestag_from_abgeordnetenwatch_returns_result(monkeypatch: Any) -> None:
    class DummyDataFetcher:
        def __init__(self, repo: Any) -> None:
            pass

        def fetch_election_programs(self, parliament_id: int) -> None:  # pragma: no cover - stub
            pass

    monkeypatch.setattr(df_tasks, "get_db", fake_get_db)
    monkeypatch.setattr(df_tasks, "AbgeordnetenwatchDataFetcher", DummyDataFetcher)

    result = df_tasks.fetch_bundestag_from_abgeordnetenwatch()

    assert result["status"] == "success"
    assert result["entity_id"] == "5"
    assert result["data"]["action"] == "fetch_election_programs"


def test_cleanup_outdated_data_returns_result(monkeypatch: Any) -> None:
    class DummyRepository:
        def __init__(self, session: DummySession) -> None:
            pass

        def delete_outdated_data(self) -> None:  # pragma: no cover - stub
            pass

    monkeypatch.setattr(df_tasks, "get_db", fake_get_db)
    monkeypatch.setattr(df_tasks, "FetchedDataRepository", DummyRepository)

    result = df_tasks.cleanup_outdated_data()

    assert result["status"] == "success"
    assert result["data"]["action"] == "cleanup_outdated_data"
