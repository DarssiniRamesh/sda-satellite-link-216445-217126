"""
Local entrypoint shim for uvicorn to locate FastAPI `app` when running from the DataPlaneService directory.

This enables:
  uvicorn main:app --host 0.0.0.0 --port ${PORT:-3001}

It imports the application instance from the package module DataPlaneService.app.main,
with fallbacks to handle different current working directories (CWD) and Python path setups.
"""
from __future__ import annotations

import importlib
import os
import sys
from types import ModuleType
from typing import Any

# Attempt 1: Absolute import via package path from repository root
#   sda-satellite-link-217126/DataPlaneService/app/main.py -> DataPlaneService.app.main:app
try:
    from DataPlaneService.app.main import app  # type: ignore  # noqa: F401
except Exception:
    # Attempt 2: Relative import when CWD is the DataPlaneService directory and it's a package
    try:
        from app.main import app  # type: ignore  # noqa: F401
    except Exception:
        # Attempt 3: Adjust sys.path to include the parent directory of DataPlaneService
        # so that 'DataPlaneService.app.main' becomes importable.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        # Retry absolute import after path fix
        try:
            from DataPlaneService.app.main import app  # type: ignore  # noqa: F401
        except Exception as e:
            # As a last resort, try dynamic import using importlib with both variants
            app: Any | None = None
            for mod_name in ("DataPlaneService.app.main", "app.main"):
                try:
                    mod: ModuleType = importlib.import_module(mod_name)
                    if hasattr(mod, "app"):
                        app = getattr(mod, "app")
                        break
                except Exception:
                    continue
            if app is None:
                # Provide a clear error to aid debugging in CI logs
                raise ImportError(
                    "Unable to import FastAPI application 'app'. Tried "
                    "'DataPlaneService.app.main' and 'app.main', with sys.path parent fallback."
                ) from e


# PUBLIC_INTERFACE
def get_app():
    """Return the FastAPI application instance for programmatic use."""
    return app
