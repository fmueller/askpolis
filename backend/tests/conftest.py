import os

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    for item in items:
        test_path = os.path.abspath(item.location[0]).replace("\\", "/")

        if "tests/unit" in test_path:
            item.add_marker(pytest.mark.unit)
        elif "tests/integration" in test_path:
            item.add_marker(pytest.mark.integration)
        elif "tests/end2end" in test_path:
            item.add_marker(pytest.mark.e2e)
