"""
FastAPI application for the DataPlaneService.

Exposes:
- Health check at GET /
- Readiness check at GET /health

Security and Compliance:
- CORS is enabled broadly for development. Restrict origins for production.
"""

from __future__ import annotations

from typing import Dict, Final

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# PUBLIC_INTERFACE
app: Final[FastAPI] = FastAPI(
    title="Data Plane Service",
    version="0.1.0",
    description="Manages Ethernet encapsulation and data plane functions for the OCT system.",
    openapi_tags=[{"name": "Health", "description": "Service health and readiness"}],
)

# Configure CORS. Consider restricting allow_origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log OpenAPI/docs URLs on startup for discoverability in preview/local environments
_logger = logging.getLogger(__name__)

@app.on_event("startup")
async def _log_docs_urls() -> None:
    port = os.getenv("PORT") or "3002"
    host = "0.0.0.0"
    try:
        p = int(port)
        if not (1 <= p <= 65535):
            port = "3002"
    except ValueError:
        port = "3002"
    _logger.info("Data Plane Service started")
    _logger.info("Swagger UI: http://%s:%s/docs", host, port)
    _logger.info("OpenAPI JSON: http://%s:%s/openapi.json", host, port)


# PUBLIC_INTERFACE
@app.get("/", summary="Health Check", tags=["Health"])
def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        A simple JSON message indicating the service is healthy.
    """
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get("/health", summary="Readiness/Health probe", tags=["Health"])
def readiness() -> Dict[str, str]:
    """Readiness endpoint for liveness probes."""
    return {"status": "ok"}
