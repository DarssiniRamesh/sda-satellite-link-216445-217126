"""
Telemetry router: exposes a WebSocket for runtime stats streaming and a helper docs route.
"""
from __future__ import annotations

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import JSONResponse

from ..services.encapsulation_service import EncapsulationService

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def get_service() -> EncapsulationService:
    from ..state import get_encapsulation_service
    return get_encapsulation_service()


# PUBLIC_INTERFACE
@router.get(
    "/ws-usage",
    summary="WebSocket usage help",
    description="Provides instructions on connecting to the telemetry WebSocket at /telemetry/ws.",
)
def ws_usage() -> JSONResponse:
    """Simple help text for using the telemetry WebSocket."""
    return JSONResponse(
        content={
            "websocket": "/telemetry/ws",
            "notes": "Connect via ws://<host>/telemetry/ws. Receives JSON messages with throughput, latency, and buffer status every second.",
        }
    )


# PUBLIC_INTERFACE
@router.websocket(
    "/ws"
)
async def telemetry_ws(websocket: WebSocket, svc: EncapsulationService = Depends(get_service)) -> None:
    """
    WebSocket endpoint that streams JSON telemetry:
    {
      "tx_bps": <float>,
      "rx_bps": <float>,
      "avg_latency_ms": <float>,
      "samples": <int>,
      "tx_queue_depth": <int>,
      "rx_queue_depth": <int>,
      "reassembly_sessions": <int>
    }
    """
    await websocket.accept()
    try:
        while True:
            tx_bps, rx_bps, avg_lat_ms, samples = svc.throughput_latency()
            txd, rxd, sess = svc.buffer_status()
            payload = {
                "tx_bps": tx_bps,
                "rx_bps": rx_bps,
                "avg_latency_ms": avg_lat_ms,
                "samples": samples,
                "tx_queue_depth": txd,
                "rx_queue_depth": rxd,
                "reassembly_sessions": sess,
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return
