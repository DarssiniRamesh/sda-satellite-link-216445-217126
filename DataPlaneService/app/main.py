from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Initialize FastAPI application with metadata and tags for documentation
app = FastAPI(
    title="DataPlaneService",
    description=(
        "Data Plane Service for the SDA Satellite Link project.\n"
        "Manages Ethernet encapsulation as Free Space Optical (FSO) frames, including packing/segmentation, "
        "packet ordering, delivery, and network interface management. Implements the Layer 2 data plane "
        "for the Optical Communications Terminal (OCT) system, supporting bi-directional Ethernet transport "
        "up to 2.5 Gbps."
    ),
    version="0.1.0",
    openapi_tags=[
        {
            "name": "health",
            "description": "Service health and readiness probes.",
        },
        {
            "name": "root",
            "description": "Root informational endpoints.",
        },
    ],
)

# PUBLIC_INTERFACE
@app.get("/", tags=["root"], summary="Root info", description="Returns a simple message indicating the DataPlaneService is running.")
def root() -> dict:
    """Root endpoint that provides a simple service status message."""
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
            "content": {
                "application/json": {
                    "example": {"status": "healthy"}
                }
            },
        }
    },
)
def health() -> JSONResponse:
    """Health endpoint for liveness checking."""
    return JSONResponse(content={"status": "healthy"}, status_code=200)
