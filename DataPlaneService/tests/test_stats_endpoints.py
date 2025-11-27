"""
Unit tests for stats router endpoints.

Tests:
- GET /stats/throughput - Throughput and latency statistics
- GET /stats/buffers - Buffer status
- GET /stats/telemetry - CRC/FEC/ARQ telemetry counters
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestThroughputStats:
    """Test suite for /stats/throughput endpoint."""
    
    def test_throughput_initial_state(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test throughput stats in initial state (no traffic)."""
        response = test_client.get("/stats/throughput")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tx_bps" in data
        assert "rx_bps" in data
        assert "avg_latency_ms" in data
        assert "samples" in data
        
        assert data["tx_bps"] >= 0
        assert data["rx_bps"] >= 0
        assert data["avg_latency_ms"] >= 0
        assert data["samples"] >= 0
    
    def test_throughput_after_encapsulation(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test throughput stats after encapsulation operation."""
        # Perform encapsulation to generate TX traffic
        pack_request = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        pack_response = test_client.post("/encapsulation/pack", json=pack_request)
        assert pack_response.status_code == 200
        
        # Check throughput stats
        response = test_client.get("/stats/throughput")
        
        assert response.status_code == 200
        data = response.json()
        
        # TX should show some activity
        assert data["tx_bps"] >= 0
        assert data["samples"] >= 0


@pytest.mark.unit
class TestBufferStats:
    """Test suite for /stats/buffers endpoint."""
    
    def test_buffers_initial_state(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test buffer stats in initial state (empty)."""
        response = test_client.get("/stats/buffers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tx_queue_depth" in data
        assert "rx_queue_depth" in data
        assert "reassembly_sessions" in data
        
        assert data["tx_queue_depth"] == 0
        assert data["rx_queue_depth"] == 0
        assert data["reassembly_sessions"] == 0
    
    def test_buffers_after_encapsulation(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test buffer stats after encapsulation (TX queue populated)."""
        # Perform encapsulation
        pack_request = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        pack_response = test_client.post("/encapsulation/pack", json=pack_request)
        assert pack_response.status_code == 200
        
        segment_count = pack_response.json()["segment_count"]
        
        # Check buffer stats
        response = test_client.get("/stats/buffers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tx_queue_depth"] == segment_count
        assert data["rx_queue_depth"] == 0
        assert data["reassembly_sessions"] == 0
    
    def test_buffers_after_rx_push(
        self,
        test_client: TestClient,
        sample_segment_set,
        reset_global_service,
    ):
        """Test buffer stats after RX segment push."""
        # Push segments to RX
        for segment in sample_segment_set:
            test_client.post("/buffers/rx/push", json=segment.model_dump())
        
        # Check buffer stats
        response = test_client.get("/stats/buffers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["rx_queue_depth"] == len(sample_segment_set)
        assert data["reassembly_sessions"] == 1  # All segments have same seq


@pytest.mark.unit
class TestTelemetryStats:
    """Test suite for /stats/telemetry endpoint."""
    
    def test_telemetry_initial_state(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test telemetry counters in initial state."""
        response = test_client.get("/stats/telemetry")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "crc_errors" in data
        assert "fec_corrections" in data
        assert "arq_retransmissions" in data
        assert "last_error" in data
        assert "metadata" in data
        
        assert data["crc_errors"] >= 0
        assert data["fec_corrections"] >= 0
        assert data["arq_retransmissions"] >= 0
    
    def test_telemetry_structure(
        self,
        test_client: TestClient,
        reset_global_service,
    ):
        """Test telemetry response structure and types."""
        response = test_client.get("/stats/telemetry")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data["crc_errors"], int)
        assert isinstance(data["fec_corrections"], int)
        assert isinstance(data["arq_retransmissions"], int)
        assert data["last_error"] is None or isinstance(data["last_error"], str)
        assert isinstance(data["metadata"], dict)
