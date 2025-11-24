#!/usr/bin/env sh
# Bootstrap script for preview environments.
# - Creates a local virtual environment in .venv (if not present)
# - Installs dependencies from requirements.txt
# - Launches uvicorn main:app on the configured PORT
# Usage:
#   chmod +x bootstrap.sh
#   PORT=3001 ./bootstrap.sh

set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "${SCRIPT_DIR}"

PORT="${PORT:-3001}"
HOST="${HOST:-0.0.0.0}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Create venv if missing
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# Activate venv
# shellcheck disable=SC1091
. ".venv/bin/activate"

# Upgrade pip and install requirements
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "Starting DataPlaneService using uvicorn main:app on ${HOST}:${PORT}"
exec uvicorn main:app --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"
