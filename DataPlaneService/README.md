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

## Development

- Entry point: `app/main.py`
- ASGI app path: `app.main:app`
- Requirements: see `requirements.txt`
