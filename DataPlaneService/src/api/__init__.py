"""
API package for DataPlaneService.

This package exposes the FastAPI application and related API modules.
External entrypoints (e.g., the top-level main.py) import app from src.api.main.

Docs:
- Swagger UI: /docs
- OpenAPI JSON: /openapi.json
Health:
- GET / and GET /health
"""

# PUBLIC_INTERFACE
__all__ = ["main"]
