# DataPlaneService

This repository contains the Data Plane Service for the OCT system. It is a FastAPI-based backend.

How to run:

- From the repository root or the DataPlaneService directory (both supported):
  uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}

- Using helper script (creates .venv if missing, installs dependencies on every run):
  PORT=3001 ./run.sh

- Using bootstrap script with virtualenv (creates .venv if missing, installs dependencies on every start + preflight check):
  chmod +x bootstrap.sh
  PORT=3001 ./bootstrap.sh

- Using Docker (bootstrap is the container entrypoint):
  docker build -t dataplane:latest .
  docker run -e PORT=3001 -p 3001:3001 dataplane:latest

Environment:
- Optional .env file at the service root (same directory as this README) for settings such as PORT, LOG_LEVEL, and APP_VERSION.
- PORT defaults to 3001 if not set. You can override the port by setting the PORT environment variable:
  - Example: PORT=8080 ./run.sh
  - Example: PORT=8080 ./bootstrap.sh
  - Example: docker run -e PORT=8080 -p 8080:8080 dataplane:latest

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
- All startup paths standardize on running from the service root with `uvicorn main:app`, avoiding `DataPlaneService.`-prefixed imports.
