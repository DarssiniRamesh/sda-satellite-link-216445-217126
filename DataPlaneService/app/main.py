from __future__ import annotations

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .routers import encapsulation as encapsulation_router
from .routers import segmentation as segmentation_router
from .routers import stats as stats_router
from .routers import buffers as buffers_router
from .routers import telemetry as telemetry_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataPlaneService")

# Initialize FastAPI application with metadata and tags for documentation
app = FastAPI(
    title="DataPlaneService",
    description=(
        "Data Plane Service for the SDA Satellite Link project.\n"
        "Manages Ethernet encapsulation as Free Space Optical (FSO) frames, including packing/segmentation, "
        "packet ordering, delivery, and network interface management. Implements the Layer 2 data plane "
        "for the Optical Communications Terminal (OCT) system, supporting bi-directional Ethernet transport "
        "up to 2.5 Gbps.\n\n"
        "WebSocket usage: connect to ws://<host>:3001/telemetry/ws to receive JSON telemetry updates at ~1Hz "
        "containing throughput, latency, and buffer status. See GET /telemetry/ws-usage for details."
    ),
    version="0.2.0",
    openapi_tags=[
        {"name": "health", "description": "Service health and readiness probes."},
        {"name": "root", "description": "Root informational endpoints."},
        {"name": "encapsulation", "description": "Ethernet-to-FSO encapsulation operations."},
        {"name": "segmentation", "description": "Reassembly and segmentation controls."},
        {"name": "stats", "description": "Throughput, latency, and buffer statistics."},
        {"name": "buffers", "description": "RX/TX buffer interactions."},
        {
            "name": "telemetry",
            "description": "Telemetry and WebSocket streaming. WebSocket endpoint: /telemetry/ws",
        },
    ],
)

# Allow CORS for local dev/testing. In production, restrict origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# PUBLIC_INTERFACE
@app.get(
    "/",
    tags=["root"],
    summary="Root info",
    description="Returns a simple message indicating the DataPlaneService is running.",
    responses={200: {"description": "Service root", "content": {"application/json": {"example": {"service": "DataPlaneService", "status": "ok"}}}}},
)
def root() -> dict:
    """Root endpoint that provides a simple service status message.

    Returns:
        dict: A minimal JSON object with service name and status.
    """
    return {"service": "DataPlaneService", "status": "ok"}

# PUBLIC_INTERFACE
@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
    description="Returns service health information suitable for liveness probes.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {"application/json": {"example": {"status": "healthy"}}},
        }
    },
)
def health() -> JSONResponse:
    """Health endpoint for liveness checking.

    Returns:
        JSONResponse: JSON payload indicating the service is healthy.
    """
    return JSONResponse(content={"status": "healthy"}, status_code=200)


# Register routers
app.include_router(encapsulation_router.router)
app.include_router(segmentation_router.router)
app.include_router(stats_router.router)
app.include_router(buffers_router.router)
app.include_router(telemetry_router.router)


# Global error handler to avoid leaking internals
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error at %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=500, content={"error": "internal_error", "message": "An internal error occurred."})
