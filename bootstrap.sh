#!/usr/bin/env sh
# Bootstrap script for preview/dev environments.
# Behavior:
# - Changes directory to the service root (the directory of this script)
# - Creates .venv if missing (idempotent)
# - Activates it
# - Upgrades pip and installs dependencies from requirements.txt on EVERY start
# - Performs a preflight import check for fastapi and uvicorn; if it fails, reinstalls & exits with a clear message
# - Launches uvicorn main:app from the service root so imports resolve
# Usage:
#   chmod +x bootstrap.sh
#   PORT=3001 ./bootstrap.sh
set -eu

# Always operate from the directory containing this script (service root)
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "${SCRIPT_DIR}"

PORT="${PORT:-3001}"
HOST="${HOST:-0.0.0.0}"
LOG_LEVEL="${LOG_LEVEL:-info}"

# Create venv if missing (idempotent)
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment at .venv"
  python3 -m venv .venv
fi

# Activate venv
# shellcheck disable=SC1091
. ".venv/bin/activate"

# Always upgrade pip and install requirements freshly
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Preflight import check; if it fails, reinstall and exit with a clear message
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

echo "Starting DataPlaneService using uvicorn main:app on ${HOST}:${PORT} (log level: ${LOG_LEVEL})"
# Ensure execution from service root so main:app resolves
exec uvicorn main:app --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"
