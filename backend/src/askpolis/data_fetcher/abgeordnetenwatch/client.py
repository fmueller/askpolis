from typing import Any

import requests

from askpolis.data_fetcher.database import DataFetcherType, FetchedData


class AbgeordnetenwatchClient:
    def __init__(self) -> None:
        self.base_url = "https://www.abgeordnetenwatch.de/api/v2"

    def get_all_parliaments(self) -> FetchedData:
        url = f"{self.base_url}/parliaments"
        response = _get_request(url, {"sort_by": "id", "sort_direction": "desc", "range_end": 100})
        return FetchedData.create_parliaments(
            data_fetcher_type=DataFetcherType.ABGEORDNETENWATCH,
            source=url,
            json_data=response["data"],
        )

    def get_all_parliament_periods(self, parliament_id: int) -> FetchedData:
        url = f"{self.base_url}/parliament-periods"
        response = _get_request(
            url, {"parliament": parliament_id, "sort_by": "id", "sort_direction": "desc", "range_end": 100}
        )
        return FetchedData.create_parliament_periods(
            data_fetcher_type=DataFetcherType.ABGEORDNETENWATCH,
            parliament_id=parliament_id,
            source=url,
            json_data=response["data"],
        )

    def get_all_election_programs(self, parliament_period_id: int) -> FetchedData:
        url = f"{self.base_url}/election-program"
        response = _get_request(
            url,
            {"parliament_period": parliament_period_id, "sort_by": "id", "sort_direction": "desc", "range_end": 100},
        )
        return FetchedData.create_election_programs(
            data_fetcher_type=DataFetcherType.ABGEORDNETENWATCH,
            parliament_period_id=parliament_period_id,
            source=url,
            json_data=response["data"],
        )

    def get_election_program(self, party_id: int, parliament_period_id: int, url: str) -> FetchedData:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to get election program from {url}")
        return FetchedData.create_election_program(
            data_fetcher_type=DataFetcherType.ABGEORDNETENWATCH,
            party_id=party_id,
            parliament_period_id=parliament_period_id,
            label="default",
            source=url,
            file_data=response.content,
        )


def _get_request(url: str, params: Any | None = None) -> Any:
    response = requests.get(url, headers={"Accept": "application/json"}, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to get data from {url}")
    return response.json()
