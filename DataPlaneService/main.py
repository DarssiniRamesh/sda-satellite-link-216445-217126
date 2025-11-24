"""
Root-level ASGI shim for DataPlaneService.

This module re-exports the FastAPI application instance from app.main so that
uvicorn can import the application using the dotted path "main:app" when the
current working directory is the service root.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 3001
    uvicorn app.main:app --host 0.0.0.0 --port 3001
"""

from app.main import app as app  # re-export FastAPI instance for ASGI servers

# PUBLIC_INTERFACE
def get_app():
    """Return the FastAPI application instance. Useful for testing/frameworks."""
    return app
