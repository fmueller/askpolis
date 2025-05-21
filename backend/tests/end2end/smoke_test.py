import time

import pytest
import requests
from starlette import status

from askpolis.main import AnswerResponse, SearchResponse


def test_root_endpoint_returns_ok(api_url: str) -> None:
    response = requests.get(api_url)
    assert response.status_code == status.HTTP_200_OK


def test_embed_document_and_search_for_it(api_url: str) -> None:
    response = requests.get(f"{api_url}/v0/tasks/tests/embeddings")
    assert response.status_code == status.HTTP_202_ACCEPTED

    for _ in range(30):
        try:
            response = requests.get(f"{api_url}/v0/search?query=test&limit=1&index=test", timeout=1)
            if response.status_code == status.HTTP_200_OK:
                search_response = SearchResponse.model_validate(response.json())
                if len(search_response.results) == 0:
                    time.sleep(1)
                    continue

                assert search_response.query == "test"
                assert len(search_response.results) == 1
                break
        except requests.RequestException:
            time.sleep(1)
    else:
        pytest.fail("The search did not respond within the expected time.")


def test_search_on_default_index_returns_empty_results(api_url: str) -> None:
    for _ in range(5):
        try:
            response = requests.get(f"{api_url}/v0/search?query=test", timeout=1)
            if response.status_code == status.HTTP_200_OK:
                search_response = SearchResponse.model_validate(response.json())
                assert search_response.query == "test"
                assert len(search_response.results) == 0
                break
        except requests.RequestException:
            time.sleep(1)
    else:
        pytest.fail("The search did not respond within the expected time.")


def test_question_answering_works(api_url: str) -> None:
    parliament_response = requests.post(
        f"{api_url}/v0/parliaments", json={"name": "Bundestag", "short_name": "Bundestag"}
    )
    assert parliament_response.status_code == status.HTTP_201_CREATED

    response = requests.post(
        f"{api_url}/v0/questions",
        json={
            "question": "What is the answer?",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    question_id = response.json()["id"]

    # ping the answer endpoint and exit when status is showing "completed"
    for _ in range(60):
        try:
            response = requests.get(f"{api_url}/v0/questions/{question_id}/answer", timeout=2)
            if response.status_code == status.HTTP_200_OK:
                answer_response = AnswerResponse.model_validate(response.json())
                if answer_response.status == "completed":
                    break
                time.sleep(1)
        except requests.RequestException:
            time.sleep(1)
    else:
        pytest.fail("The answer was not generated within the expected time.")
