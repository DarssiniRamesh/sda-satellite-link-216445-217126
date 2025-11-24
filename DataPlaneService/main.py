"""
Top-level ASGI entrypoint for DataPlaneService.

- Exposes `app` imported from src.api.main so `uvicorn main:app` works.
- When executed directly, runs uvicorn bound to 0.0.0.0 honoring env PORT,
  defaulting to 3002 per project standard.

Usage:
    uvicorn main:app --host 0.0.0.0 --port ${PORT:-3002}
"""

from __future__ import annotations

import logging
import os
from typing import Final

from src.api.main import app as _inner_app  # Import the actual FastAPI app

# Re-export the FastAPI app for ASGI servers
app = _inner_app
"""FastAPI app instance re-exported for uvicorn entrypoint (main:app)."""

# Limit exported symbols to 'app' for clarity and tooling that inspects __all__
__all__ = ["app"]


def _determine_port() -> int:
    """
    Determine the port to bind using the PORT environment variable if provided.

    Accepts any valid port in range 1..65535; defaults to 3002.
    """
    default_port: Final[int] = 3002
    env_port = os.getenv("PORT")
    if not env_port:
        return default_port
    try:
        port = int(env_port)
    except (TypeError, ValueError):
        logging.warning("Invalid PORT env value '%s'; falling back to default %s.", env_port, default_port)
        return default_port
    if 1 <= port <= 65535:
        return port
    logging.warning("PORT %s out of range; falling back to default %s.", port, default_port)
    return default_port


if __name__ == "__main__":
    # Optional: support running via `python main.py` during local development.
    try:
        import uvicorn  # Local import to avoid mandatory dependency at import time
    except Exception as exc:  # pragma: no cover - import-time failures logged
        logging.error("Uvicorn is required to run this module directly: %s", exc)
        raise

    port = _determine_port()
    # Bind to all interfaces per requirement
    logging.getLogger(__name__).info("Starting DataPlaneService on %s:%s", "0.0.0.0", port)
    logging.getLogger(__name__).info("Swagger UI: http://%s:%s/docs", "0.0.0.0", port)
    logging.getLogger(__name__).info("OpenAPI JSON: http://%s:%s/openapi.json", "0.0.0.0", port)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
