"""
Unit tests for EncapsulationService core business logic.

Tests:
- Encapsulation logic
- Segmentation with different policies
- CRC validation
- Queue management
- Reassembly state tracking
"""
from __future__ import annotations

import pytest
import binascii

from app.services.encapsulation_service import EncapsulationService
from app.models.frame_spec import (
    EncapsulationRequest,
    EncapsulatedSegment,
    FSOHeader,
    ReassemblyRequest,
)


@pytest.mark.unit
class TestEncapsulationServicePack:
    """Test encapsulation logic in EncapsulationService."""
    
    def test_encapsulate_basic(self, fresh_service: EncapsulationService, sample_ethernet_frame_1500b: str):
        """Test basic encapsulation functionality."""
        request = EncapsulationRequest(
            ethernet_frame_hex=sample_ethernet_frame_1500b,
            max_segment_size=1200,
            fec_scheme=None,
            arq_enabled=True,
        )
        
        response = fresh_service.encapsulate(request)
        
        assert response.total_bytes == len(sample_ethernet_frame_1500b) // 2
        assert response.segment_count >= 1
        assert len(response.segments) == response.segment_count
    
    def test_encapsulate_generates_crc(self, fresh_service: EncapsulationService):
        """Test that CRC32 is generated for each segment."""
        payload = "aa" * 1000
        request = EncapsulationRequest(
            ethernet_frame_hex=payload,
            max_segment_size=500,
            fec_scheme=None,
            arq_enabled=True,
        )
        
        response = fresh_service.encapsulate(request)
        
        # Verify CRC is present and valid
        for segment in response.segments:
            assert segment.header.crc32 is not None
            
            # Validate CRC
            chunk = bytes.fromhex(segment.payload_hex)
            expected_crc = binascii.crc32(chunk) & 0xFFFFFFFF
            assert segment.header.crc32 == expected_crc
    
    def test_encapsulate_sequence_numbering(self, fresh_service: EncapsulationService):
        """Test that sequence numbers increment correctly."""
        payload1 = "aa" * 1000
        payload2 = "bb" * 1000
        
        request1 = EncapsulationRequest(
            ethernet_frame_hex=payload1,
            max_segment_size=1200,
            fec_scheme=None,
            arq_enabled=True,
        )
        request2 = EncapsulationRequest(
            ethernet_frame_hex=payload2,
            max_segment_size=1200,
            fec_scheme=None,
            arq_enabled=True,
        )
        
        response1 = fresh_service.encapsulate(request1)
        response2 = fresh_service.encapsulate(request2)
        
        seq1 = response1.segments[0].header.seq
        seq2 = response2.segments[0].header.seq
        
        assert seq2 == seq1 + 1
    
    @pytest.mark.boundary
    def test_encapsulate_minimum_frame(self, fresh_service: EncapsulationService):
        """Test encapsulating minimum 64-byte frame."""
        payload = "aa" * 64
        request = EncapsulationRequest(
            ethernet_frame_hex=payload,
            max_segment_size=1200,
            fec_scheme=None,
            arq_enabled=True,
        )
        
        response = fresh_service.encapsulate(request)
        
        assert response.total_bytes == 64
        assert response.segment_count == 1
    
    @pytest.mark.boundary
    def test_encapsulate_maximum_frame(self, fresh_service: EncapsulationService):
        """Test encapsulating maximum 9216-byte frame."""
        payload = "ff" * 9216
        request = EncapsulationRequest(
            ethernet_frame_hex=payload,
            max_segment_size=1200,
            fec_scheme=None,
            arq_enabled=True,
        )
        
        response = fresh_service.encapsulate(request)
        
        assert response.total_bytes == 9216
        assert response.segment_count >= 8  # 9216 / 1200 = 7.68
    
    @pytest.mark.boundary
    def test_encapsulate_below_minimum_fails(self, fresh_service: EncapsulationService):
        """Test that frames below 64 bytes are rejected (MTU requirement)."""
        payload = "aa" * 50  # Below minimum
        request = EncapsulationRequest(
            ethernet_frame_hex=payload,
            max_segment_size=1200,
            fec_scheme=None,
            arq_enabled=True,
        )
        
        with pytest.raises(ValueError, match="REQ-DP-MTU"):
            fresh_service.encapsulate(request)
    
    @pytest.mark.boundary
    def test_encapsulate_above_maximum_fails(self, fresh_service: EncapsulationService):
        """Test that frames above 9216 bytes are rejected (MTU requirement)."""
        payload = "aa" * 9300  # Above maximum
        request = EncapsulationRequest(
            ethernet_frame_hex=payload,
            max_segment_size=1200,
            fec_scheme=None,
            arq_enabled=True,
        )
        
        with pytest.raises(ValueError, match="REQ-DP-MTU"):
            fresh_service.encapsulate(request)
    
    def test_encapsulate_enqueues_tx(self, fresh_service: EncapsulationService):
        """Test that encapsulation enqueues segments to TX queue."""
        payload = "aa" * 1000
        request = EncapsulationRequest(
            ethernet_frame_hex=payload,
            max_segment_size=1200,
            fec_scheme=None,
            arq_enabled=True,
        )
        
        response = fresh_service.encapsulate(request)
        
        # Check TX queue depth
        tx_depth, _, _ = fresh_service.buffer_status()
        assert tx_depth == response.segment_count


@pytest.mark.unit
class TestEncapsulationServiceReassembly:
    """Test reassembly logic in EncapsulationService."""
    
    def test_reassemble_complete(self, fresh_service: EncapsulationService, sample_segment_set):
        """Test successful reassembly of complete frame."""
        request = ReassemblyRequest(segments=sample_segment_set)
        
        response = fresh_service.reassemble(request)
        
        assert response.status == "complete"
        assert response.ethernet_frame_hex is not None
        assert len(response.missing_indices) == 0
    
    def test_reassemble_partial(self, fresh_service: EncapsulationService, sample_segment_set):
        """Test partial reassembly with missing segments."""
        # Only provide first 2 segments
        partial = sample_segment_set[:2]
        request = ReassemblyRequest(segments=partial)
        
        response = fresh_service.reassemble(request)
        
        assert response.status == "partial"
        assert response.ethernet_frame_hex is None
        assert 2 in response.missing_indices
    
    def test_reassemble_out_of_order(self, fresh_service: EncapsulationService, sample_segment_set):
        """Test reassembly handles out-of-order segments correctly."""
        # Reverse order
        reversed_segments = list(reversed(sample_segment_set))
        request = ReassemblyRequest(segments=reversed_segments)
        
        response = fresh_service.reassemble(request)
        
        # Should still complete
        assert response.status == "complete"
        assert response.ethernet_frame_hex is not None
    
    @pytest.mark.fec
    def test_crc_validation(self, fresh_service: EncapsulationService):
        """Test CRC validation during RX segment acceptance."""
        # Create segment with valid CRC
        payload = b"test_payload"
        crc = binascii.crc32(payload) & 0xFFFFFFFF
        
        header = FSOHeader(
            version=1,
            seq=999,
            total_segments=1,
            segment_index=0,
            payload_len=len(payload),
            crc32=crc,
            fec_scheme=None,
            arq_enabled=True,
            timestamp_ns=1000000000,
        )
        
        segment = EncapsulatedSegment(header=header, payload_hex=payload.hex())
        
        # Accept segment
        fresh_service.accept_rx_segment(segment)
        
        # Should be in RX queue and reassembly buffer
        rx_depth, _, sessions = fresh_service.buffer_status()
        _, rx_depth_check, _ = fresh_service.buffer_status()
        assert rx_depth_check >= 1
    
    @pytest.mark.fec
    def test_crc_mismatch_counted(self, fresh_service: EncapsulationService):
        """Test that CRC mismatches are counted in telemetry."""
        # Create segment with invalid CRC
        payload = b"test_payload"
        wrong_crc = 0x12345678  # Wrong CRC
        
        header = FSOHeader(
            version=1,
            seq=1000,
            total_segments=1,
            segment_index=0,
            payload_len=len(payload),
            crc32=wrong_crc,
            fec_scheme=None,
            arq_enabled=True,
            timestamp_ns=1000000000,
        )
        
        segment = EncapsulatedSegment(header=header, payload_hex=payload.hex())
        
        initial_errors, _, _ = fresh_service.telemetry_counters()
        
        # Accept segment with bad CRC
        fresh_service.accept_rx_segment(segment)
        
        # CRC error count should increase
        crc_errors, _, _ = fresh_service.telemetry_counters()
        assert crc_errors > initial_errors


@pytest.mark.unit
class TestEncapsulationServiceQueues:
    """Test queue management in EncapsulationService."""
    
    def test_tx_dequeue(self, fresh_service: EncapsulationService):
        """Test TX queue dequeue operation."""
        payload = "aa" * 1000
        request = EncapsulationRequest(
            ethernet_frame_hex=payload,
            max_segment_size=400,
            fec_scheme=None,
            arq_enabled=True,
        )
        
        response = fresh_service.encapsulate(request)
        expected_count = response.segment_count
        
        # Dequeue all
        segments = fresh_service.dequeue_tx(expected_count)
        
        assert len(segments) == expected_count
        
        # Queue should be empty now
        tx_depth, _, _ = fresh_service.buffer_status()
        assert tx_depth == 0
    
    def test_rx_dequeue(self, fresh_service: EncapsulationService, sample_fso_segment):
        """Test RX queue dequeue operation."""
        # Push segment
        fresh_service.accept_rx_segment(sample_fso_segment)
        
        # Dequeue
        segments = fresh_service.dequeue_rx(10)
        
        assert len(segments) == 1
        assert segments[0].header.seq == sample_fso_segment.header.seq
    
    def test_buffer_status(self, fresh_service: EncapsulationService):
        """Test buffer status reporting."""
        tx, rx, sessions = fresh_service.buffer_status()
        
        assert tx == 0
        assert rx == 0
        assert sessions == 0
        
        # Add some traffic
        payload = "aa" * 1000
        request = EncapsulationRequest(
            ethernet_frame_hex=payload,
            max_segment_size=1200,
            fec_scheme=None,
            arq_enabled=True,
        )
        fresh_service.encapsulate(request)
        
        tx_after, _, _ = fresh_service.buffer_status()
        assert tx_after > 0
