# Project Repository

This repository contains multiple FastAPI backend services for the SDA Satellite Link project.

## DataPlaneService

ASGI Entrypoint:
- The DataPlaneService provides a top-level main.py that re-exports the FastAPI app from src.api.main.
- You can start the service with uvicorn from the DataPlaneService directory:

```bash
cd DataPlaneService
# Option A: via python (uses PORT env or defaults)
python main.py

# Option B: via uvicorn (explicit port)
uvicorn main:app --host 0.0.0.0 --port 3010
```

Port handling:
- The service reads PORT from the environment and validates it against the allowed set: 3000, 3001, 3002, 5000.
- If PORT is unset or invalid, the service defaults to 3000.
- Bind address is 0.0.0.0 by default for containerized environments.

Environment:
- Copy .env.example to .env and adjust as needed:
```bash
cp DataPlaneService/.env.example DataPlaneService/.env
```
Then set PORT to one of the allowed ports if you need a specific value.

Health Check:
- After starting, open http://localhost:<PORT>/ to verify the health endpoint returns:
```json
{"message": "Healthy"}
```