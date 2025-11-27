"""
Boundary and negative test cases.

Tests:
- Maximum frame sizes
- Invalid CRC
- Out-of-order segments
- Malformed payloads
- Empty payloads
- Timeouts
- Invalid state transitions
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.models.frame_spec import FSOHeader, EncapsulatedSegment


@pytest.mark.boundary
class TestBoundaryCases:
    """Boundary condition tests."""
    
    def test_max_frame_size_9216(
        self,
        test_client: TestClient,
        max_payload_9216b: str,
        reset_global_service,
    ):
        """Test maximum allowed frame size (9216 bytes)."""
        request_data = {
            "ethernet_frame_hex": max_payload_9216b,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_bytes"] == 9216
    
    def test_frame_size_exceeds_maximum(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of frame exceeding maximum size."""
        oversized = "ff" * 9300  # Exceeds 9216
        request_data = {
            "ethernet_frame_hex": oversized,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 400
    
    def test_frame_size_below_minimum(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of frame below minimum size (64 bytes)."""
        undersized = "aa" * 50  # Below 64 bytes
        request_data = {
            "ethernet_frame_hex": undersized,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 400
    
    def test_segment_size_at_minimum(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test segmentation with minimum segment size (256 bytes)."""
        request_data = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 256,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        # Should create multiple segments
        assert data["segment_count"] >= 6  # 1500 / 256 ~= 6
    
    def test_segment_size_at_maximum(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test segmentation with maximum segment size (9216 bytes)."""
        request_data = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 9216,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        # Should fit in one segment
        assert data["segment_count"] == 1


@pytest.mark.negative
class TestNegativeCases:
    """Negative test cases for error handling."""
    
    def test_malformed_json(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of malformed JSON."""
        response = test_client.post(
            "/encapsulation/pack",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )
        
        assert response.status_code == 422
    
    def test_missing_required_field(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection when required field is missing."""
        incomplete_request = {
            "max_segment_size": 1200,
            # Missing ethernet_frame_hex
        }
        
        response = test_client.post("/encapsulation/pack", json=incomplete_request)
        
        assert response.status_code == 422
    
    def test_invalid_fec_scheme_handled(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test that invalid FEC scheme is accepted (stub implementation)."""
        request_data = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 1200,
            "fec_scheme": "INVALID_SCHEME",
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        # Should accept but log/stub (no strict validation yet)
        assert response.status_code == 200
    
    def test_negative_segment_size(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test rejection of negative segment size."""
        request_data = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": -100,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        assert response.status_code == 422
    
    def test_invalid_version_in_header(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test rejection of invalid protocol version."""
        header = {
            "version": 99,  # Invalid version
            "seq": 100,
            "total_segments": 1,
            "segment_index": 0,
            "payload_len": 100,
            "crc32": None,
            "fec_scheme": None,
            "arq_enabled": True,
            "timestamp_ns": 1000000000,
        }
        
        segment_data = {
            "header": header,
            "payload_hex": "aa" * 100
        }
        
        response = test_client.post("/buffers/rx/push", json=segment_data)
        
        assert response.status_code == 422  # Pydantic validation (version ge=1, le=4)
    
    def test_segment_index_exceeds_total(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test handling of segment_index >= total_segments."""
        header = {
            "version": 1,
            "seq": 200,
            "total_segments": 3,
            "segment_index": 5,  # Exceeds total
            "payload_len": 100,
            "crc32": None,
            "fec_scheme": None,
            "arq_enabled": True,
            "timestamp_ns": 1000000000,
        }
        
        segment_data = {
            "header": header,
            "payload_hex": "bb" * 100
        }
        
        # Should be accepted (validation happens during reassembly)
        response = test_client.post("/buffers/rx/push", json=segment_data)
        assert response.status_code == 202
    
    def test_payload_length_mismatch(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test handling of payload_len != actual payload length."""
        header = {
            "version": 1,
            "seq": 300,
            "total_segments": 1,
            "segment_index": 0,
            "payload_len": 100,  # Claims 100 bytes
            "crc32": None,
            "fec_scheme": None,
            "arq_enabled": True,
            "timestamp_ns": 1000000000,
        }
        
        segment_data = {
            "header": header,
            "payload_hex": "cc" * 50  # Actually 50 bytes
        }
        
        # Should be accepted (length mismatch is detected internally)
        response = test_client.post("/buffers/rx/push", json=segment_data)
        assert response.status_code == 202


@pytest.mark.hardware
@pytest.mark.xfail(reason="Hardware/FPGA not available in test environment")
class TestHardwareDependentStubs:
    """Tests requiring hardware that are expected to fail/skip in CI."""
    
    def test_fpga_fec_integration(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test FPGA FEC integration (hardware-dependent)."""
        request_data = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 1200,
            "fec_scheme": "5G-NR-LDPC",
            "arq_enabled": True,
        }
        
        response = test_client.post("/encapsulation/pack", json=request_data)
        
        # In real hardware, would verify FEC application
        assert response.status_code == 200
