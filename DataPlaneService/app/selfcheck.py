from __future__ import annotations

"""
Self-check utilities for DataPlaneService.

Provides a minimal import/startup verification without running the server.
Intended for CI smoke-checks and developer quick validation.
"""

from typing import Any

# PUBLIC_INTERFACE
def run_self_check() -> dict[str, Any]:
    """Run a lightweight self-check to verify app import and router registration.

    Returns:
        dict: Summary including router counts and tag names.
    """
    # Import inside function to avoid side-effects at module import time
    from .main import app  # type: ignore

    routes = [r for r in app.routes if getattr(r, "path", None)]
    tags = app.openapi_tags or []
    tag_names = [t.get("name") for t in tags]

    # Ensure key routers are present by their prefixes
    prefixes = set()
    for r in routes:
        p = getattr(r, "path", "")
        # normalize first segment as prefix
        if p.startswith("/"):
            parts = p.split("/")
            if len(parts) > 2:
                prefixes.add("/" + parts[1])

    expected_prefixes = {"/encapsulation", "/segmentation", "/stats", "/buffers", "/telemetry"}
    missing = sorted(list(expected_prefixes - prefixes))

    return {
        "route_count": len(routes),
        "prefixes": sorted(list(prefixes)),
        "expected_prefixes": sorted(list(expected_prefixes)),
        "missing_prefixes": missing,
        "openapi_title": app.title,
        "openapi_version": app.version,
        "tag_names": tag_names,
    }


if __name__ == "__main__":
    # Print as plain text for easy CLI use
    result = run_self_check()
    # Avoid printing internal stack traces; just state if ok
    ok = not result["missing_prefixes"]
    status = "OK" if ok else "MISSING_ROUTERS"
    print(f"[selfcheck] {status} :: {result['openapi_title']} v{result['openapi_version']}")
    if not ok:
        print(f"[selfcheck] Missing prefixes: {', '.join(result['missing_prefixes'])}")
    print(f"[selfcheck] Registered tags: {', '.join(result['tag_names'])}")
