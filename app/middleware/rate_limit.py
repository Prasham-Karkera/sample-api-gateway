from __future__ import annotations

import time
from collections import defaultdict
from typing import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = structlog.get_logger(__name__)

# Simple in-memory rate limiter (use Redis in production)
_request_counts: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter keyed by client IP."""

    def __init__(self, app: object, requests_per_minute: int = 120) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60.0

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        # Evict old entries
        _request_counts[client_ip] = [
            t for t in _request_counts[client_ip] if t > window_start
        ]

        if len(_request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                count=len(_request_counts[client_ip]),
                limit=self.requests_per_minute,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Too many requests. Limit: {self.requests_per_minute} req/min.",
                        "docs_url": "https://docs.fleetbite.internal/errors/RATE_LIMIT_EXCEEDED",
                    }
                },
            )

        _request_counts[client_ip].append(now)
        return await call_next(request)
