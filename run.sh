#!/usr/bin/env sh
# Simple script to run the DataPlaneService without needing to activate a virtualenv.
# Usage: PORT=3001 ./run.sh

set -eu

PORT="${PORT:-3001}"
HOST="${HOST:-0.0.0.0}"
LOG_LEVEL="${LOG_LEVEL:-info}"

echo "Starting DataPlaneService on ${HOST}:${PORT} (log level: ${LOG_LEVEL})"
exec uvicorn main:app --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"
