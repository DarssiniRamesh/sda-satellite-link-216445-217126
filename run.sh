#!/usr/bin/env sh
# Simple script to run the DataPlaneService for preview without manual venv activation.
# Usage:
#   PORT=3001 ./run.sh
# Or:
#   HOST=0.0.0.0 PORT=3001 LOG_LEVEL=info ./run.sh
#
# Behavior:
# - Upgrades pip and installs Python dependencies from requirements.txt on EVERY run
# - Performs a preflight import check for fastapi and uvicorn
# - Runs uvicorn main:app from the service root so imports resolve without DataPlaneService. prefix.

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "${SCRIPT_DIR}"

PORT="${PORT:-3001}"
HOST="${HOST:-0.0.0.0}"
LOG_LEVEL="${LOG_LEVEL:-info}"

PYBIN="python3"
command -v "${PYBIN}" >/dev/null 2>&1 || PYBIN="python"

# Always install/upgrade to ensure environment is correct for preview runs
"${PYBIN}" -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Preflight import check
"${PYBIN}" - <<'PYCHK'
import sys
try:
    import fastapi, uvicorn  # noqa: F401
except Exception as e:
    sys.stderr.write(f"Preflight import check failed: {e}\n")
    sys.exit(1)
else:
    print("Preflight import check passed.")
PYCHK

echo "Starting DataPlaneService on ${HOST}:${PORT} (log level: ${LOG_LEVEL})"
# Run from service root (this directory) so uvicorn main:app resolves
exec uvicorn main:app --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"
