#!/usr/bin/env sh
# Simple script to run the DataPlaneService for preview.
# Usage:
#   PORT=3001 ./run.sh
# Or:
#   HOST=0.0.0.0 PORT=3001 LOG_LEVEL=info ./run.sh
#
# Behavior:
# - Changes directory to the service root (the directory of this script)
# - Creates .venv if missing (idempotent), activates it
# - Upgrades pip and installs Python dependencies from requirements.txt on EVERY run
# - Performs a preflight import check for fastapi and uvicorn; if it fails, reinstalls & exits with a clear message
# - Runs uvicorn main:app from the service root so imports resolve without DataPlaneService. prefix.

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "${SCRIPT_DIR}"

PORT="${PORT:-3001}"
HOST="${HOST:-0.0.0.0}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment at .venv"
  python3 -m venv .venv
fi

# Activate venv
# shellcheck disable=SC1091
. ".venv/bin/activate"

# Always install/upgrade to ensure environment is correct for preview runs
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Preflight import check; if it fails, reinstall and exit with instructions
python - <<'PYCHK' || {
  echo "Preflight imports failed; attempting a clean reinstall of requirements..." >&2
  pip install --no-cache-dir -r requirements.txt
  echo "Re-run the script to start the service after successful reinstall." >&2
  exit 1
}
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
