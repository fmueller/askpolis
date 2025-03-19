from unittest.mock import MagicMock

from askpolis.data_fetcher import FetchedDataRepository
from askpolis.data_fetcher.abgeordnetenwatch import AbgeordnetenwatchClient, AbgeordnetenwatchDataFetcher


def test_fetch_election_programs_returns_early_when_parliament_id_not_found() -> None:
    mock_client = MagicMock(spec=AbgeordnetenwatchClient)
    mock_repository = MagicMock(spec=FetchedDataRepository)
    data_fetcher = AbgeordnetenwatchDataFetcher(repository=mock_repository, client=mock_client)

    mock_repository.get_by_data_fetcher_and_entity.return_value = MagicMock(
        json_data=[{"id": 1, "name": "Parliament 1"}, {"id": 2, "name": "Parliament 2"}]
    )

    data_fetcher.fetch_election_programs(parliament_id=3)

    mock_client.get_all_parliaments.assert_not_called()
    mock_repository.save.assert_not_called()
