# DataPlaneService

Minimal FastAPI scaffolding providing health and root endpoints.

## Endpoints
- GET `/` — service metadata
- GET `/health` — health probe

## Run locally
```bash
pip install -r requirements.txt
uvicorn src.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```
