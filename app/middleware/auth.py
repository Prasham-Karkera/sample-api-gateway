from __future__ import annotations

import re
from typing import Awaitable, Callable

import jwt
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

logger = structlog.get_logger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Validates Bearer JWT on all routes except excluded paths."""

    def __init__(self, app: object, excluded_paths: list[str]) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._excluded = [re.compile(p) for p in excluded_paths]

    def _is_excluded(self, path: str) -> bool:
        return any(pattern.fullmatch(path) for pattern in self._excluded)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if self._is_excluded(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return self._unauthorized("Missing or malformed Authorization header")

        token = auth_header.removeprefix("Bearer ")
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            return self._unauthorized("Token has expired")
        except jwt.InvalidTokenError as exc:
            logger.warning("jwt_invalid", error=str(exc))
            return self._unauthorized("Invalid token")

        # Inject user context into request state for downstream use
        request.state.user_id = payload.get("sub")
        request.state.user_roles = payload.get("roles", [])

        return await call_next(request)

    @staticmethod
    def _unauthorized(detail: str) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": detail,
                    "docs_url": "https://docs.fleetbite.internal/errors/UNAUTHORIZED",
                }
            },
        )
