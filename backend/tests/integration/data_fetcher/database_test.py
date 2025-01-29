from sqlalchemy.orm import Session, sessionmaker

from askpolis.data_fetcher import FetchedData, FetchedDataRepository


def test_data_fetcher_data_model(session_maker: sessionmaker[Session]) -> None:
    with session_maker() as session:
        fetched_data = FetchedData(
            data_fetcher="Abgeordnetenwatch",
            entity="Bundestag",
            source="https://www.abgeordnetenwatch.de/bundestag/abstimmungen/5",
            text_data="Some text data",
        )
        session.add(fetched_data)
        session.commit()

    with session_maker() as session:
        from_database = FetchedDataRepository(session).get_by_data_fetcher_and_entity("Abgeordnetenwatch", "Bundestag")
        assert from_database is not None
        assert from_database.text_data == "Some text data"
        assert from_database.source == "https://www.abgeordnetenwatch.de/bundestag/abstimmungen/5"
        assert from_database.data_fetcher == "Abgeordnetenwatch"
        assert from_database.entity == "Bundestag"
