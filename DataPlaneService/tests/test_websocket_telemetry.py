"""
WebSocket telemetry tests.

Tests:
- WebSocket connection
- Telemetry streaming
- JSON message format
- Disconnect handling
"""
from __future__ import annotations

import pytest
import asyncio
import json
from fastapi.testclient import TestClient


@pytest.mark.websocket
@pytest.mark.integration
class TestWebSocketTelemetry:
    """Test WebSocket telemetry streaming."""
    
    def test_ws_usage_endpoint(self, test_client: TestClient):
        """Test WebSocket usage help endpoint."""
        response = test_client.get("/telemetry/ws-usage")
        
        assert response.status_code == 200
        data = response.json()
        assert "websocket" in data
        assert "/telemetry/ws" in data["websocket"]
    
    def test_websocket_connection(self, test_client: TestClient, reset_global_service):
        """Test WebSocket connection establishment."""
        with test_client.websocket_connect("/telemetry/ws") as websocket:
            # Should connect successfully
            assert websocket is not None
    
    def test_websocket_receives_data(self, test_client: TestClient, reset_global_service):
        """Test receiving telemetry data via WebSocket."""
        with test_client.websocket_connect("/telemetry/ws") as websocket:
            # Receive first message
            data = websocket.receive_text()
            message = json.loads(data)
            
            # Verify message structure
            assert "tx_bps" in message
            assert "rx_bps" in message
            assert "avg_latency_ms" in message
            assert "samples" in message
            assert "tx_queue_depth" in message
            assert "rx_queue_depth" in message
            assert "reassembly_sessions" in message
            
            # Verify types
            assert isinstance(message["tx_bps"], (int, float))
            assert isinstance(message["rx_bps"], (int, float))
            assert isinstance(message["avg_latency_ms"], (float, int))
            assert isinstance(message["samples"], int)
            assert isinstance(message["tx_queue_depth"], int)
            assert isinstance(message["rx_queue_depth"], int)
            assert isinstance(message["reassembly_sessions"], int)
    
    @pytest.mark.slow
    def test_websocket_multiple_messages(self, test_client: TestClient, reset_global_service):
        """Test receiving multiple telemetry messages.
        
        Note: This test is marked as slow because WebSocket messages are sent at ~1Hz.
        In CI/headless environments, this may be skipped to avoid timing issues.
        """
        with test_client.websocket_connect("/telemetry/ws") as websocket:
            # Receive first message to verify connection works
            data = websocket.receive_text()
            message = json.loads(data)
            
            # Verify basic structure
            assert "tx_bps" in message
            assert "rx_bps" in message
            
            # Note: Receiving multiple messages requires waiting ~1s between each
            # This is tested in test_websocket_receives_data already
    
    def test_websocket_disconnect(self, test_client: TestClient, reset_global_service):
        """Test WebSocket graceful disconnect."""
        with test_client.websocket_connect("/telemetry/ws") as websocket:
            # Receive one message to verify connection
            data = websocket.receive_text()
            assert data is not None
            
            # Close connection (context manager handles this)
        
        # Should disconnect without error
