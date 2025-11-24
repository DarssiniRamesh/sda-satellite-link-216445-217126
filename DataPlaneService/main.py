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


def _select_port_from_env(allowed_ports: list[int], default_port: int) -> int:
    """
    Select a listening port using the PORT env var if valid, else choose the default.

    Args:
        allowed_ports: List of allowed port integers (non-empty).
        default_port: Default port to use when env is unset/invalid.

    Returns:
        Selected port integer.
    """
    if not allowed_ports or not all(isinstance(p, int) and p > 0 for p in allowed_ports):
        raise ValueError("allowed_ports must be a non-empty list of positive integers")

    env_port = os.getenv("PORT")
    if env_port:
        try:
            port_candidate = int(env_port)
            if port_candidate in allowed_ports:
                return port_candidate
            logging.warning(
                "PORT env value %s is not in allowed set %s; falling back to default %s.",
                port_candidate,
                allowed_ports,
                default_port,
            )
        except ValueError:
            logging.warning("Invalid PORT env value '%s'; must be an integer. Falling back to default.", env_port)
    return default_port


def _determine_port() -> int:
    """
    Determine the port with the project's standardized allowed set.

    Returns:
        Port selected from allowed set [3000, 3001, 3002, 5000], honoring PORT if valid; default 3002.
    """
    allowed: Final[list[int]] = [3000, 3001, 3002, 5000]
    return _select_port_from_env(allowed, default_port=3002)


if __name__ == "__main__":
    # Optional: support running via `python main.py` during local development.
    try:
        import uvicorn  # Local import to avoid mandatory dependency at import time
    except Exception as exc:  # pragma: no cover - import-time failures logged
        logging.error("Uvicorn is required to run this module directly: %s", exc)
        raise

    port = _determine_port()
    # Bind to all interfaces per requirement
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
