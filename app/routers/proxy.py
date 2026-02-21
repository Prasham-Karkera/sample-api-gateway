from __future__ import annotations

import structlog
import httpx
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()

# Route table: path prefix → downstream base URL
ROUTE_TABLE: dict[str, str] = {
    "/v1/users": settings.USER_SERVICE_URL,
    "/v1/auth": settings.USER_SERVICE_URL,
    "/v1/orders": settings.ORDER_SERVICE_URL,
    "/v1/items": settings.INVENTORY_SERVICE_URL,
    "/v1/stock": settings.INVENTORY_SERVICE_URL,
    "/v1/events": settings.NOTIFICATION_SERVICE_URL,
}


def _resolve_upstream(path: str) -> str | None:
    """Find the upstream URL for a given request path."""
    for prefix, upstream in ROUTE_TABLE.items():
        if path.startswith(prefix):
            return upstream
    return None


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    summary="Proxy request to upstream microservice",
    description=(
        "Forwards the authenticated request to the appropriate downstream service "
        "based on the URL path prefix."
    ),
    operation_id="proxy_request",
    include_in_schema=False,
)
async def proxy_request(path: str, request: Request) -> Response:
    full_path = f"/{path}"
    upstream_base = _resolve_upstream(full_path)

    if not upstream_base:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ROUTE_NOT_FOUND",
                    "message": f"No upstream service registered for path: {full_path}",
                }
            },
        )

    upstream_url = f"{upstream_base}{full_path}"
    if request.url.query:
        upstream_url += f"?{request.url.query}"

    # Forward request body
    body = await request.body()

    # Build forwarded headers (strip hop-by-hop, inject user context)
    forward_headers = dict(request.headers)
    forward_headers.pop("host", None)
    forward_headers.pop("content-length", None)

    # Inject validated user context so downstream services can trust it
    if hasattr(request.state, "user_id") and request.state.user_id:
        forward_headers["X-FleetBite-User-ID"] = str(request.state.user_id)
        forward_headers["X-FleetBite-User-Roles"] = ",".join(
            request.state.user_roles or []
        )

    logger.info(
        "proxying_request",
        method=request.method,
        path=full_path,
        upstream=upstream_url,
        user_id=getattr(request.state, "user_id", None),
    )

    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            upstream_response = await client.request(
                method=request.method,
                url=upstream_url,
                headers=forward_headers,
                content=body,
            )
    except httpx.TimeoutException:
        logger.error("upstream_timeout", upstream=upstream_url)
        return JSONResponse(
            status_code=504,
            content={
                "error": {
                    "code": "UPSTREAM_TIMEOUT",
                    "message": f"Upstream service timed out after {settings.HTTP_TIMEOUT}s.",
                }
            },
        )
    except httpx.ConnectError:
        logger.error("upstream_unavailable", upstream=upstream_url)
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Upstream service is currently unavailable.",
                }
            },
        )

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=dict(upstream_response.headers),
        media_type=upstream_response.headers.get("content-type"),
    )
