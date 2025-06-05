import logging
from typing import Any

import pytest

from askpolis.data_fetcher.models import DataFetcherType, EntityType, FetchedData


@pytest.mark.parametrize(
    "is_list,json_data,expected_json,warn",
    [
        (True, [{"a": 1}], [{"a": 1}], False),
        (True, {"a": 1}, [{"a": 1}], True),
        (False, {"a": 1}, {"a": 1}, False),
        (False, [{"a": 1}, {"a": 2}], {"a": 1}, True),
        (False, [], None, True),
        (True, [], [], False),
        (True, None, None, False),
        (False, None, None, False),
    ],
)
def test_json_with_data_field_converts_and_warns(
    is_list: bool,
    json_data: list[dict[str, Any]] | None,
    expected_json: list[dict[str, Any]] | dict[str, Any] | None,
    warn: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    fetched_data = FetchedData(
        data_fetcher="fetcher",
        data_fetcher_type=DataFetcherType.ABGEORDNETENWATCH,
        source="src",
        entity="entity",
        entity_type=EntityType.PARTY,
        is_list=is_list,
        json_data=json_data,
    )
    result = fetched_data.json_with_data_field

    assert result == {"data": expected_json}

    if warn:
        assert any("json_data expected" in record.getMessage() for record in caplog.records)
    else:
        assert not caplog.records
