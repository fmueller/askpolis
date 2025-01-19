from typing import Any

import requests

from ..database import CrawlingResult


class AbgeordnetenwatchClient:
    def __init__(self) -> None:
        self.base_url = "https://www.abgeordnetenwatch.de/api/v2"

    def get_all_parliament_periods(self, parliament: int) -> CrawlingResult:
        url = f"{self.base_url}/parliament-periods"
        response = _get_request(
            url, {"parliament": parliament, "sort_by": "id", "sort_direction": "desc", "range_end": 100}
        )
        return CrawlingResult(entity=f"parliament-periods-{parliament}", source=url, json_data=response["data"])

    def get_all_election_programs(self, parliament_period: int) -> CrawlingResult:
        url = f"{self.base_url}/election-program"
        response = _get_request(
            url, {"parliament_period": parliament_period, "sort_by": "id", "sort_direction": "desc", "range_end": 100}
        )
        return CrawlingResult(entity=f"election-programs-{parliament_period}", source=url, json_data=response["data"])

    def get_election_program(self, entity: str, url: str) -> CrawlingResult:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to get election program from {url}")
        return CrawlingResult(entity=entity, source=url, file_data=response.content)


def _get_request(url: str, params: Any | None = None) -> Any:
    response = requests.get(url, headers={"Accept": "application/json"}, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to get data from {url}")
    return response.json()
