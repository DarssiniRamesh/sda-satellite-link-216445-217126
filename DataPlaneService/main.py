"""
Local entrypoint shim for uvicorn to locate FastAPI `app` when running from the DataPlaneService directory.

This enables:
  uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}

It imports the application instance from the package module DataPlaneService.app.main.
"""

from DataPlaneService.app.main import app  # noqa: F401


# PUBLIC_INTERFACE
def get_app():
    """Return the FastAPI application instance for programmatic use."""
    return app
