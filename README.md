# DataPlaneService

This repository contains the Data Plane Service for the OCT system. It is a FastAPI-based backend.

How to run:

- From the repository root:
  uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}

- From the DataPlaneService directory (this is how the preview runs):
  cd DataPlaneService
  uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}

- Using helper script:
  PORT=3001 ./run.sh

- Using Docker:
  docker build -t dataplane:latest .
  docker run -e PORT=3001 -p 3001:3001 dataplane:latest

Environment:
- Optional .env file at repo root (same directory as this README) for settings such as PORT, LOG_LEVEL, and APP_VERSION.
- PORT defaults to 3001 if not set. The Docker image and run.sh use ${PORT} when provided, otherwise default.

Endpoints:
- GET /healthz   -> 200 {"status":"ok"}
- GET /readyz    -> 200 {"status":"ready"}
- GET /version   -> 200 {"name": "...", "version": "...", "description": "..."}

OpenAPI/Docs:
- Swagger UI: /docs
- OpenAPI JSON: /openapi.json

Notes:
- The application object is exposed in two places to support both run contexts:
  - sda-satellite-link-216445-217126/main.py (repo root)
  - sda-satellite-link-216445-217126/DataPlaneService/main.py (service directory)
- This ensures `uvicorn main:app` works whether invoked from the repo root or the DataPlaneService folder.