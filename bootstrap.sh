#!/usr/bin/env sh
# Bootstrap script for preview/dev environments.
# Behavior:
# - Creates .venv if missing
# - Activates it
# - Upgrades pip and installs dependencies from requirements.txt on EVERY start
# - Performs a preflight import check for fastapi and uvicorn
# - Launches uvicorn main:app from the service root so imports resolve
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

# Always upgrade pip and install requirements freshly
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Preflight import check
python - <<'PYCHK'
import sys
try:
    import fastapi, uvicorn  # noqa: F401
except Exception as e:
    sys.stderr.write(f"Preflight import check failed: {e}\n")
    sys.exit(1)
else:
    print("Preflight import check passed.")
PYCHK

echo "Starting DataPlaneService using uvicorn main:app on ${HOST}:${PORT} (log level: ${LOG_LEVEL})"
# Ensure execution from service root so main:app resolves
exec uvicorn main:app --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"
