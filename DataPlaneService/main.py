"""
Top-level ASGI entrypoint for DataPlaneService.

This module exposes a FastAPI instance named `app` for ASGI servers (e.g., uvicorn) to import:
    uvicorn main:app --host 0.0.0.0 --port 3010

It imports the application from the internal package path (src.api.main) and re-exports it.
It also provides an optional CLI execution path to run with uvicorn while standardizing port handling.

Environment variables:
    PORT: Preferred listening port. Allowed values: 3000, 3001, 3002, 5000.
          If unset or invalid, the module falls back to the first available from the allowed set,
          defaulting to 3000.

Notes:
- Do not hardcode sensitive values here. Use environment variables or a .env file.
- This file should remain minimal to avoid diverging from app initialization logic.
- Security: avoid printing secrets, use logging safely, and bind to 0.0.0.0 for containerized runtime.
"""

from __future__ import annotations

import logging
import os
from typing import Final

from src.api.main import app as _inner_app  # Import the actual FastAPI app

# Re-export the FastAPI app for ASGI servers
app = _inner_app

# Limit exported symbols to 'app' for clarity and tooling that inspects __all__
__all__ = ["app"]


def _select_port_from_env(allowed_ports: list[int]) -> int:
    """
    Select a listening port using the PORT env var if valid, else choose the first allowed.

    The allowed set is constrained to avoid accidental port sprawl across containers.

    Args:
        allowed_ports: List of allowed port integers (non-empty).

    Returns:
        Selected port integer.
    """
    # Validate allowed_ports defensively
    if not allowed_ports or not all(isinstance(p, int) and p > 0 for p in allowed_ports):
        raise ValueError("allowed_ports must be a non-empty list of positive integers")

    env_port = os.getenv("PORT")
    if env_port:
        try:
            port_candidate = int(env_port)
            if port_candidate in allowed_ports:
                return port_candidate
            logging.warning(
                "PORT env value %s is not in allowed set %s; falling back to first allowed.",
                port_candidate,
                allowed_ports,
            )
        except ValueError:
            logging.warning("Invalid PORT env value '%s'; must be an integer. Falling back.", env_port)
    return allowed_ports[0]


def _determine_port() -> int:
    """
    Determine the port with the project's standardized allowed set.

    Returns:
        Port selected from allowed set [3000, 3001, 3002, 5000], honoring PORT if valid.
    """
    allowed: Final[list[int]] = [3000, 3001, 3002, 5000]
    return _select_port_from_env(allowed)


if __name__ == "__main__":
    # Optional: support running via `python main.py` during local development.
    # Production should use `uvicorn main:app --host 0.0.0.0 --port <port>`
    try:
        import uvicorn  # Local import to avoid mandatory dependency at import time
    except Exception as exc:  # pragma: no cover - import-time failures logged
        logging.error("Uvicorn is required to run this module directly: %s", exc)
        raise

    port = _determine_port()
    # Bind to all interfaces per requirement
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
