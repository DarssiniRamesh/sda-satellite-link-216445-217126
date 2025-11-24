"""
Frame specification models and helpers for DataPlaneService.

Defines Pydantic models for FSO frame headers, encapsulated segments, and
runtime statistics. These are used by routers and services to validate
inputs/outputs and to document the API.

Security: Validates lengths and bounds, ensures only sanitized values
are accepted from external requests.
"""
from __future__ import annotations

from typing import Optional, List, Dict
from pydantic import BaseModel, Field, validator


# PUBLIC_INTERFACE
class FSOHeader(BaseModel):
    """FSO frame header fields used in encapsulation/segmentation."""
    version: int = Field(..., ge=1, le=4, description="Protocol version (1..4).")
    seq: int = Field(..., ge=0, description="Monotonic sequence number for ARQ/order.")
    total_segments: int = Field(..., ge=1, le=4096, description="Total segments for this Ethernet frame.")
    segment_index: int = Field(..., ge=0, description="Zero-based segment index.")
    payload_len: int = Field(..., ge=0, le=9216, description="Length of payload bytes in this segment.")
    crc32: Optional[int] = Field(None, description="CRC32 for payload (optional, if present).")
    fec_scheme: Optional[str] = Field(None, description="FEC scheme identifier, e.g., '5G-NR-LDPC' or None.")
    arq_enabled: bool = Field(True, description="Whether ARQ is enabled for this frame.")
    timestamp_ns: Optional[int] = Field(None, description="TX timestamp in nanoseconds (optional).")


# PUBLIC_INTERFACE
class EncapsulatedSegment(BaseModel):
    """A single encapsulated segment of an Ethernet frame as FSO payload."""
    header: FSOHeader = Field(..., description="FSO header describing the segment.")
    payload_hex: str = Field(..., description="Hex-encoded segment payload (sanitized).")

    @validator("payload_hex")
    def validate_hex(cls, v: str) -> str:
        if not v:
            return v
        # ensure hex characters only
        hv = v.lower()
        for ch in hv:
            if ch not in "0123456789abcdef":
                raise ValueError("payload_hex must be hex-encoded")
        if len(v) % 2 != 0:
            raise ValueError("payload_hex length must be even")
        return v


# PUBLIC_INTERFACE
class EncapsulationRequest(BaseModel):
    """Request to encapsulate an Ethernet frame into FSO segments."""
    ethernet_frame_hex: str = Field(..., description="Hex-encoded raw Ethernet frame.")
    max_segment_size: int = Field(1200, ge=256, le=9216, description="Max payload bytes per FSO segment.")
    fec_scheme: Optional[str] = Field(None, description="Requested FEC scheme identifier.")
    arq_enabled: bool = Field(True, description="Enable ARQ metadata.")


# PUBLIC_INTERFACE
class EncapsulationResponse(BaseModel):
    """Encapsulation response containing segments."""
    segments: List[EncapsulatedSegment] = Field(..., description="Generated FSO segments.")
    total_bytes: int = Field(..., ge=0, description="Total bytes of original Ethernet frame.")
    segment_count: int = Field(..., ge=1, description="Number of segments generated.")


# PUBLIC_INTERFACE
class ReassemblyRequest(BaseModel):
    """Request to reassemble Ethernet frame from segments."""
    segments: List[EncapsulatedSegment] = Field(..., description="Segments to reassemble.")


# PUBLIC_INTERFACE
class ReassemblyResponse(BaseModel):
    """Response containing reassembled frame and status."""
    ethernet_frame_hex: Optional[str] = Field(None, description="Hex-encoded reassembled frame if complete.")
    missing_indices: List[int] = Field(default_factory=list, description="Missing segment indices.")
    status: str = Field(..., description="Status of reassembly: complete or partial.")


# PUBLIC_INTERFACE
class BufferStatus(BaseModel):
    """Status of in-memory queues and reassembly buffers."""
    tx_queue_depth: int = Field(..., ge=0, description="Items pending in TX queue.")
    rx_queue_depth: int = Field(..., ge=0, description="Items pending in RX queue.")
    reassembly_sessions: int = Field(..., ge=0, description="Active reassembly sessions count.")


# PUBLIC_INTERFACE
class ThroughputLatencyStats(BaseModel):
    """Throughput and latency measurement."""
    tx_bps: float = Field(..., ge=0, description="Approximate transmit throughput (bits per second).")
    rx_bps: float = Field(..., ge=0, description="Approximate receive throughput (bits per second).")
    avg_latency_ms: float = Field(..., ge=0, description="Average one-way latency in milliseconds.")
    samples: int = Field(..., ge=0, description="Number of samples used for calculation.")


# PUBLIC_INTERFACE
class TelemetryOverview(BaseModel):
    """Telemetry overview including CRC/FEC/ARQ placeholders."""
    crc_errors: int = Field(..., ge=0, description="Count of CRC errors observed.")
    fec_corrections: int = Field(..., ge=0, description="Count of FEC corrections.")
    arq_retransmissions: int = Field(..., ge=0, description="Count of ARQ retransmissions.")
    last_error: Optional[str] = Field(None, description="Last error summary, if any.")
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Additional telemetry metadata.")
