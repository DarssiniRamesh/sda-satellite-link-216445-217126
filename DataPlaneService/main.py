"""
Root-level ASGI shim for DataPlaneService.

This module re-exports the FastAPI application instance from app.main so that
uvicorn can import the application using the dotted path "main:app" when the
current working directory is the service root.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 3001
    uvicorn app.main:app --host 0.0.0.0 --port 3001
"""

from app.main import app as app  # re-export FastAPI instance for ASGI servers

# PUBLIC_INTERFACE
def get_app():
    """Return the FastAPI application instance. Useful for testing/frameworks."""
    return app

if __name__ == "__main__":
    # Optional self-check quick run
    try:
        from app.selfcheck import run_self_check
        res = run_self_check()
        missing = res.get("missing_prefixes") or []
        status = "OK" if not missing else f"MISSING: {', '.join(missing)}"
        print(f"[DataPlaneService] Self-check {status}")
    except Exception as exc:  # noqa: BLE001
        # Do not expose internals
        print("[DataPlaneService] Self-check failed")
