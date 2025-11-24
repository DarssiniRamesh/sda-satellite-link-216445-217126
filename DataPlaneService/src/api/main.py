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
