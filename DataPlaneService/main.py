"""
Local entrypoint shim for uvicorn to locate FastAPI `app` when running from the DataPlaneService directory.

This enables:
  uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}

The application instance is imported directly from app.main assuming the current
working directory is the DataPlaneService service root.
"""

from __future__ import annotations

# Import directly from local app package as scripts and Docker ensure correct CWD
from app.main import app  # noqa: F401


# PUBLIC_INTERFACE
def get_app():
    """Return the FastAPI application instance for programmatic use."""
    return app
