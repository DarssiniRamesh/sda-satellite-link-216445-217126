# DataPlaneService

Minimal FastAPI scaffolding providing health and root endpoints.

## Endpoints
- GET `/` — service metadata
- GET `/health` — health probe

## Run locally
```bash
pip install -r requirements.txt

# Option 1: Using the preview orchestrator convention (recommended)
# The repository now provides a top-level ASGI entrypoint at main.py.
uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"

# Option 2: Directly referencing the internal module path
uvicorn src.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```
