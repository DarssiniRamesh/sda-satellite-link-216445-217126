"""
Integration tests for complete encapsulation-to-reassembly workflows.

Tests full end-to-end scenarios:
- Pack -> TX dequeue -> RX push -> Reassemble
- Multiple frame handling
- Concurrent operations
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestFullFlowIntegration:
    """Integration tests for complete data flow."""
    
    def test_full_flow_single_frame(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test complete flow: encapsulate -> dequeue TX -> push RX -> reassemble."""
        # Step 1: Encapsulate
        pack_request = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 1200,
            "fec_scheme": "5G-NR-LDPC",
            "arq_enabled": True,
        }
        pack_response = test_client.post("/encapsulation/pack", json=pack_request)
        assert pack_response.status_code == 200
        
        packed_data = pack_response.json()
        segments = packed_data["segments"]
        
        # Step 2: Dequeue from TX
        tx_response = test_client.get(f"/encapsulation/tx/dequeue?n={len(segments)}")
        assert tx_response.status_code == 200
        tx_segments = tx_response.json()
        assert len(tx_segments) == len(segments)
        
        # Step 3: Push to RX (simulating reception)
        for segment in tx_segments:
            rx_push_response = test_client.post("/buffers/rx/push", json=segment)
            assert rx_push_response.status_code == 202
        
        # Step 4: Reassemble
        reassemble_request = {"segments": tx_segments}
        reassemble_response = test_client.post("/segmentation/reassemble", json=reassemble_request)
        assert reassemble_response.status_code == 200
        
        reassembled_data = reassemble_response.json()
        assert reassembled_data["status"] == "complete"
        assert reassembled_data["ethernet_frame_hex"] == sample_ethernet_frame_1500b
    
    def test_full_flow_multiple_frames(
        self,
        test_client: TestClient,
        sample_ethernet_frame_64b: str,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test handling multiple frames in sequence."""
        frames = [sample_ethernet_frame_64b, sample_ethernet_frame_1500b]
        
        for original_frame in frames:
            # Encapsulate
            pack_request = {
                "ethernet_frame_hex": original_frame,
                "max_segment_size": 1200,
                "fec_scheme": None,
                "arq_enabled": True,
            }
            pack_response = test_client.post("/encapsulation/pack", json=pack_request)
            assert pack_response.status_code == 200
            
            segments = pack_response.json()["segments"]
            
            # Dequeue TX
            tx_response = test_client.get(f"/encapsulation/tx/dequeue?n={len(segments)}")
            tx_segments = tx_response.json()
            
            # Push to RX
            for segment in tx_segments:
                test_client.post("/buffers/rx/push", json=segment)
            
            # Reassemble
            reassemble_request = {"segments": tx_segments}
            reassemble_response = test_client.post("/segmentation/reassemble", json=reassemble_request)
            assert reassemble_response.status_code == 200
            
            reassembled = reassemble_response.json()
            assert reassembled["status"] == "complete"
            assert reassembled["ethernet_frame_hex"] == original_frame
    
    def test_stats_reflect_traffic(
        self,
        test_client: TestClient,
        sample_ethernet_frame_1500b: str,
        reset_global_service,
    ):
        """Test that stats endpoints reflect actual traffic."""
        # Check initial state
        initial_buffers = test_client.get("/stats/buffers").json()
        assert initial_buffers["tx_queue_depth"] == 0
        
        # Generate traffic
        pack_request = {
            "ethernet_frame_hex": sample_ethernet_frame_1500b,
            "max_segment_size": 1200,
            "fec_scheme": None,
            "arq_enabled": True,
        }
        pack_response = test_client.post("/encapsulation/pack", json=pack_request)
        segment_count = pack_response.json()["segment_count"]
        
        # Check buffer stats
        buffers = test_client.get("/stats/buffers").json()
        assert buffers["tx_queue_depth"] == segment_count
        
        # Dequeue
        test_client.get(f"/encapsulation/tx/dequeue?n={segment_count}")
        
        # Check emptied
        buffers_after = test_client.get("/stats/buffers").json()
        assert buffers_after["tx_queue_depth"] == 0
