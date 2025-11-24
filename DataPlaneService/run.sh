#!/usr/bin/env bash
set -euo pipefail

# This script installs dependencies if necessary and starts the FastAPI app using uvicorn.
# It does not rely on a pre-created virtual environment.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env if present (non-strict)
if [ -f "${SCRIPT_DIR}/.env" ]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' "${SCRIPT_DIR}/.env" | xargs -I {} echo {})
fi

# Default port is 3001 if not provided
PORT="${PORT:-3001}"

# Install dependencies if uvicorn is not available
if ! command -v uvicorn >/dev/null 2>&1; then
  echo "[run.sh] uvicorn not found. Installing dependencies..."
  # Use pip if available; prefer python3 -m pip for consistency
  if command -v python3 >/dev/null 2>&1; then
    python3 -m pip install --upgrade pip
    python3 -m pip install -r "${SCRIPT_DIR}/requirements.txt"
  else
    python -m pip install --upgrade pip
    python -m pip install -r "${SCRIPT_DIR}/requirements.txt"
  fi
else
  echo "[run.sh] uvicorn found. Ensuring dependencies are installed..."
  # Best-effort install to ensure matching versions
  if command -v python3 >/dev/null 2>&1; then
    python3 -m pip install -r "${SCRIPT_DIR}/requirements.txt" || true
  else
    python -m pip install -r "${SCRIPT_DIR}/requirements.txt" || true
  fi
fi

echo "[run.sh] Starting DataPlaneService on port ${PORT}"
# Start uvicorn with correct module path app.main:app on configured port
# Bind to 0.0.0.0 to be reachable in container
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
