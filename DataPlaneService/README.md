# DataPlaneService

FastAPI backend service for the SDA Satellite Link project. Provides the scaffolding for the Data Plane Service and starts on port 3001 by default.

## Run

From this directory:

```bash
chmod +x run.sh
./run.sh
```

Port configuration:
- Default port is 3001.
- Override with environment variable PORT, e.g.:
  - `PORT=3101 ./run.sh`
  - Or create a `.env` file (see `.env.example`) with `PORT=3001` to set a persistent default.

The service will be available at (default):
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
- Run directly (default port 3001, override with PORT):
  - `PORT=3001 uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-3001}`
  - or `PORT=3001 uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}`
