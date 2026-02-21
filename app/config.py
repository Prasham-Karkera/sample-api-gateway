from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GW_", env_file=".env", extra="ignore")

    # App
    APP_VERSION: str = "1.0.0"
    ENV: str = Field(default="development", description="Environment: development | staging | production")

    # JWT
    JWT_SECRET_KEY: str = Field(..., description="256-bit secret for signing/verifying JWTs")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_SECONDS: int = 3600

    # Rate limiting
    RATE_LIMIT_RPM: int = Field(default=120, description="Max requests per minute per IP")

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["*"])

    # Downstream service URLs
    USER_SERVICE_URL: str = Field(default="http://user-service:8001")
    ORDER_SERVICE_URL: str = Field(default="http://order-service:8002")
    INVENTORY_SERVICE_URL: str = Field(default="http://inventory-service:8003")
    NOTIFICATION_SERVICE_URL: str = Field(default="http://notification-service:8004")

    # Timeouts
    HTTP_TIMEOUT: float = Field(default=10.0, description="Seconds before upstream timeout")

    # Paths that bypass auth (regex patterns)
    AUTH_EXCLUDED_PATHS: list[str] = Field(
        default=[
            "/health/live",
            "/health/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/v1/auth/token",
            "/v1/users/register",
        ]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
