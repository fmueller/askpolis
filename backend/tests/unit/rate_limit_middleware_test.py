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

    return app


def test_rate_limit_blocks_after_five_requests() -> None:
    client = TestClient(create_app())
    for _ in range(5):
        resp = client.get("/")
        assert resp.status_code == 200
    resp = client.get("/")
    assert resp.status_code == 429
