"""
Encapsulation and reassembly services with in-memory queues.

Provides segmentation of Ethernet frames into FSO segments and reassembly of
segments back into Ethernet frames. Maintains simple in-memory TX/RX queues
and reassembly buffers keyed by sequence number.

Note: CRC/FEC/ARQ integrations are stubbed for now and exposed via telemetry.
"""
from __future__ import annotations

import binascii
import logging
import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Deque, Dict, List, Optional, Tuple

from ..models.frame_spec import (
    EncapsulationRequest,
    EncapsulationResponse,
    ReassemblyRequest,
    ReassemblyResponse,
    EncapsulatedSegment,
    FSOHeader,
)
from ..models.segmentation_policy import SegmentationPolicy

logger = logging.getLogger(__name__)


@dataclass
class _ReassemblyState:
    total_segments: int
    received: Dict[int, bytes] = field(default_factory=dict)
    created_ns: int = field(default_factory=lambda: time.time_ns())


class EncapsulationService:
    """Service implementing encapsulation, reassembly, and in-memory buffers."""

    def __init__(self) -> None:
        self._tx_queue: Deque[EncapsulatedSegment] = deque()
        self._rx_queue: Deque[EncapsulatedSegment] = deque()
        self._reassembly: Dict[int, _ReassemblyState] = {}
        self._seq_counter: int = 0
        self._lock = Lock()

        # Telemetry counters
        self._crc_errors: int = 0
        self._fec_corrections: int = 0
        self._arq_retx: int = 0

        # Throughput/latency samples
        self._tx_bytes_window: Deque[Tuple[int, int]] = deque(maxlen=1000)  # (timestamp_ns, bytes)
        self._rx_bytes_window: Deque[Tuple[int, int]] = deque(maxlen=1000)
        self._latency_samples_ns: Deque[int] = deque(maxlen=2000)

    # PUBLIC_INTERFACE
    def encapsulate(self, req: EncapsulationRequest) -> EncapsulationResponse:
        """Encapsulate an Ethernet frame into FSO segments and enqueue TX.

        Args:
            req: EncapsulationRequest with frame hex, policy, and flags.

        Returns:
            EncapsulationResponse with generated segments.
        """
        try:
            payload = bytes.fromhex(req.ethernet_frame_hex)
        except ValueError as exc:
            logger.warning("Invalid ethernet_frame_hex: %s", exc)
            raise ValueError("ethernet_frame_hex must be valid hex") from exc

        policy = SegmentationPolicy(
            max_segment_size=req.max_segment_size,
            include_crc32=True,
            arq_enabled=req.arq_enabled,
            fec_scheme=req.fec_scheme,
        )
        seg_size = policy.normalized_size()

        with self._lock:
            seq = self._seq_counter
            self._seq_counter += 1

        total_segments = (len(payload) + seg_size - 1) // seg_size or 1
        segments: List[EncapsulatedSegment] = []
        now_ns = time.time_ns()

        for idx in range(total_segments):
            start = idx * seg_size
            end = min(start + seg_size, len(payload))
            chunk = payload[start:end]
            crc32_val: Optional[int] = None
            if policy.include_crc32:
                crc32_val = binascii.crc32(chunk) & 0xFFFFFFFF

            header = FSOHeader(
                version=1,
                seq=seq,
                total_segments=total_segments,
                segment_index=idx,
                payload_len=len(chunk),
                crc32=crc32_val,
                fec_scheme=policy.fec_scheme,
                arq_enabled=policy.arq_enabled,
                timestamp_ns=now_ns,
            )
            seg = EncapsulatedSegment(header=header, payload_hex=chunk.hex())
            segments.append(seg)

            # enqueue TX and record throughput sample
            with self._lock:
                self._tx_queue.append(seg)
                self._tx_bytes_window.append((now_ns, len(chunk)))

        logger.info("Encapsulated seq=%d into %d segments", seq, total_segments)
        return EncapsulationResponse(
            segments=segments,
            total_bytes=len(payload),
            segment_count=len(segments),
        )

    # PUBLIC_INTERFACE
    def accept_rx_segment(self, seg: EncapsulatedSegment) -> None:
        """Accept a received segment into RX queue and update reassembly buffer."""
        try:
            chunk = bytes.fromhex(seg.payload_hex) if seg.payload_hex else b""
        except ValueError as exc:
            logger.warning("RX segment payload invalid hex: %s", exc)
            self._crc_errors += 1
            return

        # Optional CRC check
        if seg.header.crc32 is not None:
            calc = binascii.crc32(chunk) & 0xFFFFFFFF
            if calc != seg.header.crc32:
                logger.debug("CRC mismatch for seq=%d idx=%d", seg.header.seq, seg.header.segment_index)
                self._crc_errors += 1
                # Still enqueue but mark as error via telemetry counters; ARQ logic would NAK in real system.

        with self._lock:
            self._rx_queue.append(seg)
            self._rx_bytes_window.append((time.time_ns(), len(chunk)))

            state = self._reassembly.get(seg.header.seq)
            if state is None:
                state = _ReassemblyState(total_segments=seg.header.total_segments)
                self._reassembly[seg.header.seq] = state
            state.received[seg.header.segment_index] = chunk

            # Latency estimate if TX timestamp present
            if seg.header.timestamp_ns:
                self._latency_samples_ns.append(max(0, time.time_ns() - seg.header.timestamp_ns))

    # PUBLIC_INTERFACE
    def reassemble(self, req: ReassemblyRequest) -> ReassemblyResponse:
        """Attempt reassembly from provided segments, returns frame or missing indices."""
        for seg in req.segments:
            self.accept_rx_segment(seg)

        # Attempt to complete by sequence numbers present in the request
        seq_ids = {s.header.seq for s in req.segments}
        # For simplicity, if multiple seq seen, reassemble each; return first completed
        with self._lock:
            for seq in sorted(seq_ids):
                state = self._reassembly.get(seq)
                if not state:
                    continue
                missing = [i for i in range(state.total_segments) if i not in state.received]
                if missing:
                    return ReassemblyResponse(ethernet_frame_hex=None, missing_indices=missing, status="partial")
                # complete
                ordered = b"".join(state.received[i] for i in range(state.total_segments))
                # cleanup buffer
                del self._reassembly[seq]
                return ReassemblyResponse(ethernet_frame_hex=ordered.hex(), missing_indices=[], status="complete")

        return ReassemblyResponse(ethernet_frame_hex=None, missing_indices=[], status="partial")

    # PUBLIC_INTERFACE
    def dequeue_tx(self, max_items: int = 10) -> List[EncapsulatedSegment]:
        """Return up to max_items segments from TX queue."""
        items: List[EncapsulatedSegment] = []
        with self._lock:
            for _ in range(min(max_items, len(self._tx_queue))):
                items.append(self._tx_queue.popleft())
        return items

    # PUBLIC_INTERFACE
    def dequeue_rx(self, max_items: int = 10) -> List[EncapsulatedSegment]:
        """Return up to max_items segments from RX queue."""
        items: List[EncapsulatedSegment] = []
        with self._lock:
            for _ in range(min(max_items, len(self._rx_queue))):
                items.append(self._rx_queue.popleft())
        return items

    # PUBLIC_INTERFACE
    def buffer_status(self) -> Tuple[int, int, int]:
        """Return (tx_depth, rx_depth, reassembly_sessions)."""
        with self._lock:
            return len(self._tx_queue), len(self._rx_queue), len(self._reassembly)

    # PUBLIC_INTERFACE
    def telemetry_counters(self) -> Tuple[int, int, int]:
        """Return (crc_errors, fec_corrections, arq_retx)."""
        return self._crc_errors, self._fec_corrections, self._arq_retx

    # PUBLIC_INTERFACE
    def throughput_latency(self) -> Tuple[float, float, float, int]:
        """Compute approximate TX/RX throughput and avg latency (ms)."""
        now_ns = time.time_ns()

        def calc_bps(window: Deque[Tuple[int, int]]) -> float:
            if not window:
                return 0.0
            # consider last second
            one_sec_ns = 1_000_000_000
            cutoff = now_ns - one_sec_ns
            bytes_sum = 0
            for ts, b in list(window):
                if ts >= cutoff:
                    bytes_sum += b
            return float(bytes_sum * 8)  # bits per last second

        tx_bps = calc_bps(self._tx_bytes_window)
        rx_bps = calc_bps(self._rx_bytes_window)

        lat_samples = list(self._latency_samples_ns)
        avg_latency_ms = (sum(lat_samples) / len(lat_samples) / 1_000_000.0) if lat_samples else 0.0
        return tx_bps, rx_bps, avg_latency_ms, len(lat_samples)
