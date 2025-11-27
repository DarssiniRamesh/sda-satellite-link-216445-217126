"""
Unit tests for segmentation/reassembly router endpoints.

Tests:
- POST /segmentation/reassemble - Frame reassembly from segments
- In-order delivery guarantees
- Partial and complete reassembly scenarios
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.models.frame_spec import EncapsulatedSegment, FSOHeader


@pytest.mark.unit
class TestReassembly:
    """Test suite for /segmentation/reassemble endpoint."""
    
    def test_reassemble_complete_frame(
        self,
        test_client: TestClient,
        sample_segment_set,
        reset_global_service,
    ):
        """Test successful reassembly of complete frame from all segments."""
        request_data = {
            "segments": [seg.model_dump() for seg in sample_segment_set]
        }
        
        response = test_client.post("/segmentation/reassemble", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "complete"
        assert data["ethernet_frame_hex"] is not None
        assert len(data["missing_indices"]) == 0
        
        # Verify reassembled frame length
        expected_len = sum(seg.header.payload_len for seg in sample_segment_set)
        actual_len = len(data["ethernet_frame_hex"]) // 2
        assert actual_len == expected_len
    
    def test_reassemble_out_of_order(
        self,
        test_client: TestClient,
        sample_segment_set,
        reset_global_service,
    ):
        """Test reassembly with out-of-order segments (should handle correctly)."""
        # Shuffle segments
        shuffled = [sample_segment_set[2], sample_segment_set[0], sample_segment_set[1]]
        
        request_data = {
            "segments": [seg.model_dump() for seg in shuffled]
        }
        
        response = test_client.post("/segmentation/reassemble", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still complete successfully (in-order delivery requirement)
        assert data["status"] == "complete"
        assert data["ethernet_frame_hex"] is not None
    
    def test_reassemble_partial_missing_segment(
        self,
        test_client: TestClient,
        sample_segment_set,
        reset_global_service,
    ):
        """Test partial reassembly when segments are missing."""
        # Only provide first 2 of 3 segments
        partial_segments = sample_segment_set[:2]
        
        request_data = {
            "segments": [seg.model_dump() for seg in partial_segments]
        }
        
        response = test_client.post("/segmentation/reassemble", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "partial"
        assert data["ethernet_frame_hex"] is None
        assert 2 in data["missing_indices"]  # Missing index 2
    
    def test_reassemble_duplicate_segments(
        self,
        test_client: TestClient,
        sample_segment_set,
        reset_global_service,
    ):
        """Test reassembly with duplicate segments (should handle gracefully)."""
        # Include duplicate of first segment
        with_duplicate = sample_segment_set + [sample_segment_set[0]]
        
        request_data = {
            "segments": [seg.model_dump() for seg in with_duplicate]
        }
        
        response = test_client.post("/segmentation/reassemble", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should complete despite duplicate
        assert data["status"] == "complete"
    
    @pytest.mark.boundary
    def test_reassemble_empty_segments_list(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of empty segments list."""
        request_data = {"segments": []}
        
        response = test_client.post("/segmentation/reassemble", json=request_data)
        
        assert response.status_code == 400
    
    @pytest.mark.negative
    def test_reassemble_invalid_segment_structure(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of malformed segment data."""
        request_data = {
            "segments": [
                {
                    "header": {"invalid": "structure"},
                    "payload_hex": "aabb"
                }
            ]
        }
        
        response = test_client.post("/segmentation/reassemble", json=request_data)
        
        assert response.status_code == 422  # Pydantic validation error
    
    @pytest.mark.negative
    def test_reassemble_invalid_payload_hex(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of non-hex payload."""
        header = FSOHeader(
            version=1,
            seq=300,
            total_segments=1,
            segment_index=0,
            payload_len=10,
            crc32=None,
            fec_scheme=None,
            arq_enabled=True,
            timestamp_ns=1000000000,
        )
        
        invalid_segment = {
            "header": header.model_dump(),
            "payload_hex": "invalid_hex_XYZ"
        }
        
        request_data = {"segments": [invalid_segment]}
        
        response = test_client.post("/segmentation/reassemble", json=request_data)
        
        assert response.status_code == 422


@pytest.mark.integration
class TestInOrderDelivery:
    """Test in-order delivery guarantees."""
    
    def test_sequence_number_ordering(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test that segments are processed in sequence number order."""
        # Create multiple frames with different sequence numbers
        frames_data = []
        for seq_offset in range(3):
            segments = []
            for idx in range(2):
                header = FSOHeader(
                    version=1,
                    seq=100 + seq_offset,
                    total_segments=2,
                    segment_index=idx,
                    payload_len=100,
                    crc32=None,
                    fec_scheme=None,
                    arq_enabled=True,
                    timestamp_ns=1000000000,
                )
                segment = EncapsulatedSegment(
                    header=header,
                    payload_hex=f"{seq_offset:02x}" * 100
                )
                segments.append(segment)
            frames_data.append(segments)
        
        # Reassemble in sequence order
        for segments in frames_data:
            request_data = {"segments": [seg.model_dump() for seg in segments]}
            response = test_client.post("/segmentation/reassemble", json=request_data)
            assert response.status_code == 200
            assert response.json()["status"] == "complete"
