"""
Stats router: exposes throughput, latency, and buffer utilization.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..models.frame_spec import ThroughputLatencyStats, BufferStatus, TelemetryOverview
from ..services.encapsulation_service import EncapsulationService

router = APIRouter(prefix="/stats", tags=["stats"])


def get_service() -> EncapsulationService:
    from ..state import get_encapsulation_service
    return get_encapsulation_service()


# PUBLIC_INTERFACE
@router.get(
    "/throughput",
    response_model=ThroughputLatencyStats,
    summary="Get throughput and latency",
    description="Returns approximate TX/RX throughput (bps) and average latency (ms) based on in-memory samples.",
)
def get_throughput(svc: EncapsulationService = Depends(get_service)) -> ThroughputLatencyStats:
    """Return approximate throughput and latency stats."""
    tx_bps, rx_bps, avg_lat_ms, samples = svc.throughput_latency()
    return ThroughputLatencyStats(tx_bps=tx_bps, rx_bps=rx_bps, avg_latency_ms=avg_lat_ms, samples=samples)


# PUBLIC_INTERFACE
@router.get(
    "/buffers",
    response_model=BufferStatus,
    summary="Get buffer status",
    description="Returns depths of TX/RX queues and number of active reassembly sessions.",
)
def get_buffers(svc: EncapsulationService = Depends(get_service)) -> BufferStatus:
    """Return buffer depths and reassembly session count."""
    tx, rx, sessions = svc.buffer_status()
    return BufferStatus(tx_queue_depth=tx, rx_queue_depth=rx, reassembly_sessions=sessions)


# PUBLIC_INTERFACE
@router.get(
    "/telemetry",
    response_model=TelemetryOverview,
    summary="Get CRC/FEC/ARQ telemetry",
    description="Returns counters for CRC errors, FEC corrections, and ARQ retransmissions. Values are stubs for now.",
)
def get_telemetry(svc: EncapsulationService = Depends(get_service)) -> TelemetryOverview:
    """Return telemetry counters. CRC/FEC/ARQ are stubs until integrated."""
    crc, fec, arq = svc.telemetry_counters()
    return TelemetryOverview(
        crc_errors=crc,
        fec_corrections=fec,
        arq_retransmissions=arq,
        last_error=None,
        metadata={"note": "CRC/FEC/ARQ counters are stubs pending integration."},
    )
