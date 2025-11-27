"""
Unit tests for buffers router endpoints.

Tests:
- POST /buffers/rx/push - RX segment ingestion
- Buffer state management
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.models.frame_spec import EncapsulatedSegment, FSOHeader


@pytest.mark.unit
class TestRXPush:
    """Test suite for /buffers/rx/push endpoint."""
    
    def test_push_valid_segment(
        self,
        test_client: TestClient,
        sample_fso_segment,
        reset_global_service,
    ):
        """Test pushing a valid segment to RX buffer."""
        response = test_client.post(
            "/buffers/rx/push",
            json=sample_fso_segment.model_dump(),
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
    
    def test_push_multiple_segments(
        self,
        test_client: TestClient,
        sample_segment_set,
        reset_global_service,
    ):
        """Test pushing multiple segments sequentially."""
        for segment in sample_segment_set:
            response = test_client.post(
                "/buffers/rx/push",
                json=segment.model_dump(),
            )
            assert response.status_code == 202
        
        # Verify segments are in RX queue
        dequeue_response = test_client.get("/encapsulation/rx/dequeue?n=10")
        assert dequeue_response.status_code == 200
        data = dequeue_response.json()
        assert len(data) == len(sample_segment_set)
    
    @pytest.mark.negative
    def test_push_invalid_segment_structure(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of malformed segment."""
        invalid_data = {
            "header": {"bad": "structure"},
            "payload_hex": "aabb"
        }
        
        response = test_client.post("/buffers/rx/push", json=invalid_data)
        
        assert response.status_code == 422
    
    @pytest.mark.negative
    def test_push_invalid_payload_hex(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of non-hex payload."""
        header = FSOHeader(
            version=1,
            seq=400,
            total_segments=1,
            segment_index=0,
            payload_len=10,
            crc32=None,
            fec_scheme=None,
            arq_enabled=True,
            timestamp_ns=1000000000,
        )
        
        segment_data = {
            "header": header.model_dump(),
            "payload_hex": "GHIJKL"  # Invalid hex
        }
        
        response = test_client.post("/buffers/rx/push", json=segment_data)
        
        # Should be accepted at API level but fail internally (logged as CRC error)
        # API returns 400 due to validation in accept_rx_segment
        assert response.status_code in [400, 422]
    
    @pytest.mark.boundary
    def test_push_empty_payload(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test pushing segment with empty payload."""
        header = FSOHeader(
            version=1,
            seq=500,
            total_segments=1,
            segment_index=0,
            payload_len=0,
            crc32=None,
            fec_scheme=None,
            arq_enabled=False,
            timestamp_ns=1000000000,
        )
        
        segment_data = {
            "header": header.model_dump(),
            "payload_hex": ""
        }
        
        response = test_client.post("/buffers/rx/push", json=segment_data)
        
        # Should accept empty payload
        assert response.status_code == 202
