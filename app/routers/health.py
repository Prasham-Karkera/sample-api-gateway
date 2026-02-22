from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health")


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get(
    "/live",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns 200 if the API Gateway process is running.",
    operation_id="health_live",
)
async def liveness() -> HealthResponse:
    from app.config import settings
    return HealthResponse(status="ok", service="api-gateway", version=settings.APP_VERSION)


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Readiness probe",
    description="Returns 200 if the API Gateway can handle traffic (all config loaded).",
    operation_id="health_ready",
)
async def readiness() -> HealthResponse:
    from app.config import settings
    return HealthResponse(status="ok", service="api-gateway", version=settings.APP_VERSION)


@router.get("/test", tags=["Testing"])
async def test_endpoint() -> dict[str, str]:
    """Sample endpoint for manual testing and validation."""
    return {"message": "API Gateway is reachable and responsive!"}
