import requests


def test_root_endpoint_returns_ok(api_url: str) -> None:
    response = requests.get(api_url)
    assert response.status_code == 200
