from sqlalchemy.orm import Session, sessionmaker

from askpolis.data_fetcher import FetchedData, FetchedDataRepository
from askpolis.data_fetcher.database import DataFetcherType


def test_data_fetcher_data_model(session_maker: sessionmaker[Session]) -> None:
    with session_maker() as session:
        fetched_data = FetchedData.create_parliament_periods(
            DataFetcherType.ABGEORDNETENWATCH,
            parliament_id=123,
            source="https://www.abgeordnetenwatch.de/bundestag/abstimmungen/5",
            text_data="Some text data",
            json_data=[{"id": 1, "name": "Bundestag"}],
        )
        fetched_data.data_fetcher = "Abgeordnetenwatch"
        session.add(fetched_data)
        session.commit()

    with session_maker() as session:
        from_database = FetchedDataRepository(session).get_by_data_fetcher_and_entity(
            "Abgeordnetenwatch", "parliament_periods.123"
        )
        assert from_database is not None
        assert from_database.text_data == "Some text data"
        assert from_database.json_data == [{"id": 1, "name": "Bundestag"}]
        assert from_database.source == "https://www.abgeordnetenwatch.de/bundestag/abstimmungen/5"
        assert from_database.data_fetcher == "Abgeordnetenwatch"
        assert from_database.entity == "parliament_periods.123"


def test_uuid_generation(session_maker: sessionmaker[Session]) -> None:
    with session_maker() as session:
        session.add(_generate_random_parliament_period(1))
        session.add(_generate_random_parliament_period(2))
        session.add(_generate_random_parliament_period(3))
        session.commit()

    with session_maker() as session:
        assert len(FetchedDataRepository(session).get_all()) == 3


def _generate_random_parliament_period(parliament_id: int) -> FetchedData:
    random_data = FetchedData.create_parliament_periods(
        DataFetcherType.ABGEORDNETENWATCH,
        parliament_id=parliament_id,
        source="https://www.abgeordnetenwatch.de/bundestag/abstimmungen/5",
        json_data=[{"id": parliament_id, "name": "Bundestag"}],
    )
    random_data.data_fetcher = "Abgeordnetenwatch"
    return random_data
