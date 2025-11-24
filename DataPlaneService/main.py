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
from typing import Any, Optional

# Import resolution strategy:
# 1) Try local package import when CWD is the service folder: from app.main import app
# 2) Try absolute package import: from DataPlaneService.app.main import app
# 3) If that fails, prepend parent directory to sys.path and retry the absolute import
# 4) As a final fallback, use importlib to attempt both variants explicitly

app: Any  # will be bound by one of the branches below

# Attempt 1: When uvicorn is launched from DataPlaneService/ (CWD=service folder)
try:
    from app.main import app as _app  # type: ignore
    app = _app
except Exception:
    # Attempt 2: Absolute import (works when repo root is on PYTHONPATH)
    try:
        from DataPlaneService.app.main import app as _app  # type: ignore
        app = _app
    except Exception:
        # Attempt 3: Ensure parent of this file (repo root) is on sys.path, then retry absolute import
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        try:
            from DataPlaneService.app.main import app as _app  # type: ignore
            app = _app
        except Exception as e:
            # Attempt 4: Dynamic import tries both names explicitly
            resolved_app: Optional[Any] = None
            for mod_name in ("app.main", "DataPlaneService.app.main"):
                try:
                    mod: ModuleType = importlib.import_module(mod_name)
                    if hasattr(mod, "app"):
                        resolved_app = getattr(mod, "app")
                        break
                except Exception:
                    continue
            if resolved_app is None:
                raise ImportError(
                    "Unable to import FastAPI application 'app'. Tried 'app.main' and "
                    "'DataPlaneService.app.main', including sys.path parent fallback."
                ) from e
            app = resolved_app


# PUBLIC_INTERFACE
def get_app():
    """Return the FastAPI application instance for programmatic use."""
    return app
