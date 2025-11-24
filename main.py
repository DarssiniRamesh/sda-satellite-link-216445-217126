"""
Repository root entrypoint to expose the FastAPI application as `app` for uvicorn.

This allows running:
  uvicorn main:app --host 0.0.0.0 --port 3001

It imports the app from the DataPlaneService package.
"""

from DataPlaneService.app.main import app  # noqa: F401


# PUBLIC_INTERFACE
def get_app():
    """Return the FastAPI application instance for programmatic use."""
    return app
