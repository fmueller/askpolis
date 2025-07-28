from __future__ import annotations

import os
from collections.abc import Awaitable
from typing import Any, Callable, Protocol, cast

import redis.asyncio as redis_asyncio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from starlette.types import ASGIApp

# paths that are not rate limited
EXCLUDED_PATHS = {"/", "/healthz", "/readyz"}


class RedisLike(Protocol):
    async def incr(self, key: str) -> int: ...

    async def expire(self, key: str, ttl: int) -> Any: ...


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple IP-based rate limiting middleware."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        redis_client: RedisLike | None = None,
        limit: int = 5,
        period: int = 60,
    ) -> None:
        super().__init__(app)
        if redis_client is None:
            url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis_client = cast(RedisLike, cast(Any, redis_asyncio).from_url(url))
        self.redis = redis_client
        self.limit = limit
        self.period = period

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate-limit:{client_ip}"
        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, self.period)
            if count > self.limit:
                return Response(status_code=HTTP_429_TOO_MANY_REQUESTS)
        except Exception:
            # fail open on Redis errors
            pass
        return await call_next(request)
