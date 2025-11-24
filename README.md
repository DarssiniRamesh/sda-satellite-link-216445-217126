# DataPlaneService

This repository contains the Data Plane Service for the OCT system. It is a FastAPI-based backend that can be run directly with:

- Python module path from repo root:
  uvicorn main:app --host 0.0.0.0 --port 3001

- Using helper script:
  PORT=3001 ./run.sh

- Using Docker:
  docker build -t dataplane:latest .
  docker run -e PORT=3001 -p 3001:3001 dataplane:latest

Environment:
- Optional .env file at repo root (same directory as this README) for settings such as PORT, LOG_LEVEL, and APP_VERSION.
- Defaults to PORT 3001.

Endpoints:
- GET /healthz   -> 200 {"status":"ok"}
- GET /readyz    -> 200 {"status":"ready"}
- GET /version   -> 200 {"name": "...", "version": "...", "description": "..."}

OpenAPI/Docs:
- Swagger UI: /docs
- OpenAPI JSON: /openapi.json

Note:
- This scaffolding is non-destructive and intended to allow the preview runner to import `main:app` from the repo root.