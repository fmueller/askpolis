import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from askpolis.rate_limiting import RateLimitMiddleware, RedisLike


class DummyRedis(RedisLike):
    def __init__(self) -> None:
        self.data: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.data[key] = self.data.get(key, 0) + 1
        return self.data[key]

    async def expire(self, key: str, ttl: int) -> None:  # noqa: D401 - simple dummy
        self.data.setdefault(key, 0)
        return None


def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, redis_client=DummyRedis(), limit=5, period=60)

    @app.get("/")
    def read_root() -> dict[str, str]:
        return {"hello": "world"}

    @app.get("/foo")
    def foo() -> dict[str, str]:
        return {"foo": "bar"}

    @app.get("/healthz")
    def health() -> dict[str, bool]:
        return {"healthy": True}

    @app.get("/readyz")
    def ready() -> dict[str, bool]:
        return {"healthy": True}

    return app


def test_rate_limit_blocks_after_five_requests() -> None:
    client = TestClient(create_app())
    for _ in range(5):
        resp = client.get("/foo")
        assert resp.status_code == 200
    resp = client.get("/foo")
    assert resp.status_code == 429


def test_rate_limit_uses_forwarded_header() -> None:
    client = TestClient(create_app())
    headers = {"X-Forwarded-For": "1.2.3.4"}
    for _ in range(5):
        resp = client.get("/foo", headers=headers)
        assert resp.status_code == 200
    resp = client.get("/foo", headers=headers)
    assert resp.status_code == 429


def test_root_not_rate_limited() -> None:
    client = TestClient(create_app())
    for _ in range(10):
        resp = client.get("/")
        assert resp.status_code == 200


def test_health_probes_not_rate_limited() -> None:
    client = TestClient(create_app())
    for _ in range(10):
        resp = client.get("/healthz")
        assert resp.status_code == 200
    for _ in range(10):
        resp = client.get("/readyz")
        assert resp.status_code == 200


def test_docs_not_rate_limited() -> None:
    client = TestClient(create_app())
    for _ in range(10):
        resp = client.get("/")
        assert resp.status_code == 200
    for _ in range(10):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200


def test_env_var_overrides_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "2")
    client = TestClient(create_app())
    for _ in range(2):
        resp = client.get("/foo")
        assert resp.status_code == 200
    resp = client.get("/foo")
    assert resp.status_code == 429
