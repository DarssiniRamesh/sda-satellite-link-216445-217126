from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure basic logging early. Users can override with LOG_LEVEL env var.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("DataPlaneService")


class AppMetadata(BaseModel):
    """Application metadata model for version endpoint response."""
    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    description: str = Field(..., description="Service description")


# PUBLIC_INTERFACE
class Settings(BaseSettings):
    """Pydantic settings for the DataPlaneService.

    Values are loaded from environment variables and a local .env file if present.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "DataPlaneService"
    APP_DESCRIPTION: str = (
        "Manages Ethernet encapsulation as FSO frames and provides Layer 2 data plane APIs."
    )
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")

    PORT: int = Field(default=3001, description="Port to run the HTTP server on")
    LOG_LEVEL: str = Field(default=LOG_LEVEL, description="Logging level")

    # Example of future settings:
    # DATABASE_URL: str | None = Field(default=None, description="Database connection string")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache settings to avoid repeated disk/ENV reads."""
    settings = Settings()
    # Sync logging level if provided in settings
    logging.getLogger().setLevel(settings.LOG_LEVEL.upper())
    logger.debug("Settings loaded: %s", settings.model_dump())
    return settings


# Initialize FastAPI app with OpenAPI metadata and tags
settings = get_settings()
openapi_tags = [
    {
        "name": "health",
        "description": "Health and readiness checks for the service.",
    },
    {
        "name": "meta",
        "description": "Service metadata such as version and build information.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_tags=openapi_tags,
    contact={"name": "OCT System", "url": "https://example.com"},
)


# Health endpoint
# PUBLIC_INTERFACE
@app.get(
    "/healthz",
    tags=["health"],
    summary="Health check",
    description="Returns service liveness and basic information.",
    response_model=Dict[str, str],
    responses={
        200: {"description": "Service is alive"},
    },
)
def healthz() -> Dict[str, str]:
    """Health endpoint indicating the service is alive."""
    logger.debug("healthz requested")
    return {"status": "ok"}


# Readiness endpoint (basic, can be extended)
# PUBLIC_INTERFACE
@app.get(
    "/readyz",
    tags=["health"],
    summary="Readiness check",
    description="Returns service readiness. Extend with dependency checks as needed.",
    response_model=Dict[str, str],
    responses={
        200: {"description": "Service is ready"},
    },
)
def readyz() -> Dict[str, str]:
    """Readiness endpoint indicating the service is ready to accept traffic."""
    logger.debug("readyz requested")
    return {"status": "ready"}


# Version endpoint
# PUBLIC_INTERFACE
@app.get(
    "/version",
    tags=["meta"],
    summary="Version information",
    description="Returns the service version and metadata.",
    response_model=AppMetadata,
    responses={
        200: {"description": "Version and metadata returned"},
    },
)
def version() -> AppMetadata:
    """Return version and metadata for the service."""
    logger.debug("version requested")
    return AppMetadata(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
    )


# PUBLIC_INTERFACE
@app.get(
    "/docs/websocket",
    tags=["meta"],
    summary="WebSocket usage",
    description=(
        "Notes: If WebSocket endpoints are added, this route documents how to connect. "
        "Currently, there are no WebSocket routes defined."
    ),
    responses={200: {"description": "WebSocket usage notes"}},
)
def websocket_usage() -> Dict[str, str]:
    """Informational route about WebSocket usage (placeholder for future endpoints)."""
    return {"message": "No WebSocket endpoints defined at this time."}
