"""
PUBLIC_INTERFACE
ASGI entrypoint for DataPlaneService.

This module re-exports the FastAPI `app` object from src.api.main so that
the preview orchestrator can start the service using:
    uvicorn main:app

No ports or host settings are defined here. Use environment variables and/or
uvicorn CLI flags to configure host/port when starting the service.
"""
from __future__ import annotations

# Re-export FastAPI app from the internal module path so `uvicorn main:app` works.
from src.api.main import app as app  # noqa: F401

# Explicit module export list for linters and clarity.
__all__ = ["app"]
