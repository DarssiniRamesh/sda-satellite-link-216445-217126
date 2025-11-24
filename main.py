"""
Repository root entrypoint shim for uvicorn to locate FastAPI `app`.

Preferred startup is from the service root:
  cd "$(dirname "$0")" && uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}

This shim imports the app from the service's app.main module under the service root.
"""

from __future__ import annotations

# Import by traversing to the service's app package if available in path.
# This keeps compatibility if uvicorn is ever pointed at the repo root.
try:
    from app.main import app  # type: ignore  # noqa: F401
except Exception:  # Fallback for legacy usage if path differs
    # Final fallback: import via package only if PYTHONPATH includes service root
    from DataPlaneService.app.main import app  # type: ignore  # noqa: F401


# PUBLIC_INTERFACE
def get_app():
    """Return the FastAPI application instance for programmatic use."""
    return app
