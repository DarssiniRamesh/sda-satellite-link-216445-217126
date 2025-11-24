# Project Repository

This repository contains multiple FastAPI backend services for the SDA Satellite Link project.

## DataPlaneService

ASGI Entrypoint:
- The DataPlaneService provides a top-level main.py that re-exports the FastAPI app from src.api.main.
- You can start the service with uvicorn from the DataPlaneService directory.

From the DataPlaneService directory:
```bash
cd DataPlaneService
# Option A: via uvicorn with the default port (3002)
uvicorn main:app --host 0.0.0.0 --port 3002

# Option B: override port via env
export PORT=3002
uvicorn main:app --host 0.0.0.0 --port "${PORT}"
```

Why "uvicorn main:app" works:
- main.py exists at the top-level of DataPlaneService and defines `app` by importing from `src.api.main`.

Port handling:
- Allowed ports: 3000, 3001, 3002, 5000.
- If PORT is unset or invalid, the service defaults to 3002.
- Bind address is 0.0.0.0 by default for containerized environments.

Environment:
- Copy .env.example to .env and adjust as needed:
```bash
cp DataPlaneService/.env.example DataPlaneService/.env
```

Health Check and Swagger UI:
- Health: http://localhost:3002/
- Docs: http://localhost:3002/docs
