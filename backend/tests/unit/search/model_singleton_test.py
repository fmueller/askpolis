import pytest

from askpolis.search.embeddings_service import get_embedding_model
from askpolis.search.reranker_service import get_reranker_service


def test_get_embedding_model_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISABLE_INFERENCE", "true")
    get_embedding_model.cache_clear()
    model1 = get_embedding_model()
    model2 = get_embedding_model()
    assert model1 is model2


def test_get_reranker_service_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISABLE_INFERENCE", "true")
    get_reranker_service.cache_clear()
    service1 = get_reranker_service()
    service2 = get_reranker_service()
    assert service1 is service2
