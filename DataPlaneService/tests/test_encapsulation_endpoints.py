"""
Unit tests for encapsulation router endpoints.

Tests:
- POST /encapsulation/pack - Ethernet frame encapsulation
- GET /encapsulation/tx/dequeue - TX segment retrieval
- GET /encapsulation/rx/dequeue - RX segment retrieval
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.models.frame_spec import EncapsulationRequest, EncapsulationResponse


@pytest.mark.unit
class TestEncapsulationPack:
    """Test suite for /encapsulation/pack endpoint."""
    
    def test_pack_standard_frame(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test encapsulating a standard 1500-byte Ethernet frame."""
        request_data = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 1200,
            "fec_scheme": "5G-NR-LDPC",
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "segments" in data
        assert "total_bytes" in data
        assert "segment_count" in data
        assert data["total_bytes"] == len(sample_ethernet_frame_1500b) // 2
        assert data["segment_count"] >= 1
        assert len(data["segments"]) == data["segment_count"]
        
        # Verify segment structure
        for seg in data["segments"]:
            assert "header" in seg
            assert "payload_hex" in seg
            assert seg["header"]["version"] == 1
            assert seg["header"]["arq_enabled"] is True
    
    def test_pack_minimum_frame(
        self,
        test_client: TestClient,
        sample_ethernet_frame_64b: str,
        reset_global_service,
    ):
        """Test encapsulating minimum 64-byte Ethernet frame."""
        request_data = {
            "ethernet_frame_hex": sample_ethernet_frame_64b,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": False,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_bytes"] == 64
        assert data["segment_count"] == 1  # Should fit in one segment
    
    def test_pack_jumbo_frame_multiple_segments(
        self,
        test_client: TestClient,
        sample_ethernet_frame_jumbo: str,
        reset_global_service,
    ):
        """Test encapsulating jumbo frame requiring multiple segments."""
        request_data = {
            "ethernet_frame_hex": sample_ethernet_frame_jumbo,
            "max_segment_size": 1200,
            "fec_scheme": "5G-NR-LDPC",
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_bytes"] == 9000
        # Should require multiple segments: 9000 / 1200 = 7.5, so 8 segments
        assert data["segment_count"] >= 7
        
        # Verify sequence numbering and indices
        segments = data["segments"]
        for idx, seg in enumerate(segments):
            assert seg["header"]["segment_index"] == idx
            assert seg["header"]["total_segments"] == len(segments)
            assert seg["header"]["seq"] == segments[0]["header"]["seq"]  # All same seq
    
    @pytest.mark.boundary
    def test_pack_invalid_hex(
        self,
        test_client: TestClient,
        invalid_hex_payload: str,
        reset_global_service,
    ):
        """Test rejection of invalid hex string."""
        request_data = {
            "ethernet_frame_hex": invalid_hex_payload,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 400
        assert "detail" in response.json()
    
    @pytest.mark.boundary
    def test_pack_odd_length_hex(
        self,
        test_client: TestClient,
        odd_length_hex_payload: str,
        reset_global_service,
    ):
        """Test rejection of odd-length hex string."""
        request_data = {
            "ethernet_frame_hex": odd_length_hex_payload,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 400
    
    @pytest.mark.boundary
    def test_pack_empty_frame(
        self,
        test_client: TestClient,
        empty_payload: str,
        reset_global_service,
    ):
        """Test rejection of empty Ethernet frame."""
        request_data = {
            "ethernet_frame_hex": empty_payload,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 400
    
    @pytest.mark.boundary
    def test_pack_invalid_segment_size_too_small(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test rejection of segment size below minimum (256 bytes)."""
        request_data = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 100,  # Below minimum
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 422  # Pydantic validation error
    
    @pytest.mark.boundary
    def test_pack_invalid_segment_size_too_large(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test rejection of segment size above maximum (9216 bytes)."""
        request_data = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 10000,  # Above maximum
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 422


@pytest.mark.unit
class TestTXDequeue:
    """Test suite for /encapsulation/tx/dequeue endpoint."""
    
    def test_tx_dequeue_empty_queue(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test dequeueing from empty TX queue."""
        response = test_client.get("/encapsulation/tx/dequeue?n=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_tx_dequeue_after_pack(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test TX queue contains segments after encapsulation."""
        # First pack a frame
        pack_request = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        pack_response = test_client.post("/encapsulation/pack", json=pack_request)
        assert pack_response.status_code == 200
        
        expected_count = pack_response.json()["segment_count"]
        
        # Now dequeue
        response = test_client.get(f"/encapsulation/tx/dequeue?n={expected_count}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_count
        
        # Verify segments have proper structure
        for seg in data:
            assert "header" in seg
            assert "payload_hex" in seg
    
    def test_tx_dequeue_partial(
        self,
        test_client: TestClient,
        sample_ethernet_frame_jumbo: str,
        reset_global_service,
    ):
        """Test partial dequeue from TX queue."""
        # Pack a large frame to get multiple segments
        pack_request = {
            "ethernet_frame_hex": sample_ethernet_frame_jumbo,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        pack_response = test_client.post("/encapsulation/pack", json=pack_request)
        assert pack_response.status_code == 200
        
        total_count = pack_response.json()["segment_count"]
        
        # Dequeue only half
        response = test_client.get("/encapsulation/tx/dequeue?n=3")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Dequeue rest
        response2 = test_client.get(f"/encapsulation/tx/dequeue?n={total_count}")
        assert response2.status_code == 200
        remaining = response2.json()
        assert len(remaining) == total_count - 3
    
    @pytest.mark.boundary
    def test_tx_dequeue_invalid_n_zero(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of n=0."""
        response = test_client.get("/encapsulation/tx/dequeue?n=0")
        
        assert response.status_code == 400
    
    @pytest.mark.boundary
    def test_tx_dequeue_invalid_n_too_large(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of n > 1000."""
        response = test_client.get("/encapsulation/tx/dequeue?n=1001")
        
        assert response.status_code == 400


@pytest.mark.unit
class TestRXDequeue:
    """Test suite for /encapsulation/rx/dequeue endpoint."""
    
    def test_rx_dequeue_empty_queue(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test dequeueing from empty RX queue."""
        response = test_client.get("/encapsulation/rx/dequeue?n=10")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_rx_dequeue_after_push(
        self,
        test_client: TestClient,
        sample_fso_segment,
        reset_global_service,
    ):
        """Test RX queue contains segments after push."""
        # Push a segment to RX
        push_response = test_client.post(
            "/buffers/rx/push",
            json=sample_fso_segment.model_dump(),
        )
        assert push_response.status_code == 202
        
        # Dequeue
        response = test_client.get("/encapsulation/rx/dequeue?n=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["header"]["seq"] == sample_fso_segment.header.seq
    
    @pytest.mark.boundary
    def test_rx_dequeue_invalid_n(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of invalid n parameter."""
        response = test_client.get("/encapsulation/rx/dequeue?n=-1")
        
        assert response.status_code == 400
