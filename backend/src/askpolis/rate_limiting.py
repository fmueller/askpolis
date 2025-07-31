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
EXCLUDED_PATHS = {"/", "/openapi.json", "/healthz", "/readyz"}


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
        env_limit = os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE")
        if env_limit:
            try:
                env_value = int(env_limit)
                if env_value >= 1:
                    limit = env_value
            except ValueError:
                pass
        self.limit = limit
        self.period = period

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
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

    def _get_client_ip(self, request: Request) -> str:
        """Determine the client IP from headers or connection info."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        forwarded = request.headers.get("forwarded")
        if forwarded:
            forwarded_value = forwarded.split(",")[0].strip()
            for part in forwarded_value.split(";"):
                clean = part.strip()
                if clean.lower().startswith("for="):
                    return clean.split("=", 1)[1].strip('"')
        return request.client.host if request.client else "unknown"
