# DataPlaneService

FastAPI-based Data Plane Service for the OCT system.

Startup (recommended from service root):
- Run directly with uvicorn:
  uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}

- Using helper script (auto-creates .venv, installs dependencies on each run, preflight check):
  PORT=3001 ./run.sh

- Using bootstrap script (same behavior, used as Docker entrypoint):
  chmod +x bootstrap.sh
  PORT=3001 ./bootstrap.sh

Docker:
- docker build -t dataplane:latest .
- docker run -e PORT=3001 -p 3001:3001 dataplane:latest

Environment:
- Optional .env at the service root for settings like PORT, LOG_LEVEL, and APP_VERSION.
- PORT usage:
  - Defaults to 3001 if not set
  - Override examples:
    - PORT=8080 ./run.sh
    - PORT=8080 ./bootstrap.sh
    - docker run -e PORT=8080 -p 8080:8080 dataplane:latest

Endpoints:
- GET /healthz   -> 200 {"status":"ok"}
- GET /readyz    -> 200 {"status":"ready"}
- GET /version   -> 200 {"name": "...", "version": "...", "description": "..."}

OpenAPI/Docs:
- Swagger UI: /docs
- OpenAPI JSON: /openapi.json

Notes:
- Standardize on running from the service root with `uvicorn main:app`.
- The repo-root main.py is a compatibility shim; prefer using the service root.
