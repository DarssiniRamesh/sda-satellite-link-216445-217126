# DataPlaneService

FastAPI backend service for the SDA Satellite Link project. Provides the scaffolding for the Data Plane Service and starts on port 3001.

## Run

From this directory:

```bash
chmod +x run.sh
./run.sh
```

The service will be available at:
- http://localhost:3001/           (root)
- http://localhost:3001/health     (health)
- http://localhost:3001/docs       (OpenAPI docs)
- http://localhost:3001/openapi.json

WebSocket usage:
- ws://localhost:3001/telemetry/ws (see GET /telemetry/ws-usage)

### Quick self-check (no server)

Run a quick import/startup check:

```bash
python -c "import app.selfcheck as sc; print(sc.run_self_check())"
```

You should see all expected router prefixes present and tag names listed.

## Development

- Entry point: `app/main.py`
- ASGI app paths:
  - Preferred: `app.main:app`
  - Shim: `main:app` (via root-level main.py)
- Requirements: see `requirements.txt`
- Run directly:
  - `uvicorn app.main:app --host 0.0.0.0 --port 3001`
  - or `uvicorn main:app --host 0.0.0.0 --port 3001`
