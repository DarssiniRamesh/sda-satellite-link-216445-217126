#!/usr/bin/env sh
# Simple script to run the DataPlaneService without needing to activate a virtualenv.
# Usage:
#   PORT=3001 ./run.sh
# Or:
#   HOST=0.0.0.0 PORT=3001 LOG_LEVEL=info ./run.sh
#
# Behavior:
# - Installs Python dependencies from requirements.txt if uvicorn/fastapi are missing.
# - Runs uvicorn main:app from the repository root so imports resolve without DataPlaneService. prefix.

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "${SCRIPT_DIR}"

PORT="${PORT:-3001}"
HOST="${HOST:-0.0.0.0}"
LOG_LEVEL="${LOG_LEVEL:-info}"

PYBIN="python"
command -v "${PYBIN}" >/dev/null 2>&1 || PYBIN="python3"

need_install=0
command -v uvicorn >/dev/null 2>&1 || need_install=1
"$PYBIN" - <<'PYCHK' || need_install=1
try:
    import fastapi, pydantic, dotenv  # type: ignore
except Exception:
    raise SystemExit(1)
PYCHK

if [ "${need_install}" -eq 1 ]; then
  echo "Installing Python dependencies from requirements.txt ..."
  "$PYBIN" -m pip install --upgrade pip >/dev/null 2>&1 || true
  pip install --no-cache-dir -r requirements.txt
fi

echo "Starting DataPlaneService on ${HOST}:${PORT} (log level: ${LOG_LEVEL})"
# Run from service root (this directory) so uvicorn main:app resolves
exec uvicorn main:app --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"
