from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.middleware.auth import JWTAuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import health, proxy

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("api_gateway_starting", version=settings.APP_VERSION, env=settings.ENV)
    yield
    logger.info("api_gateway_shutdown")


app = FastAPI(
    title="FleetBite API Gateway",
    description=(
        "Central entry point for all FleetBite microservices. "
        "Handles JWT authentication, rate limiting, and request routing."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
    lifespan=lifespan,
)

# --- Middleware (order matters: outermost added last) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_RPM)
app.add_middleware(JWTAuthMiddleware, excluded_paths=settings.AUTH_EXCLUDED_PATHS)

# --- Prometheus metrics ---
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# --- Routers ---
app.include_router(health.router, tags=["Health"])
app.include_router(proxy.router, tags=["Proxy"])
