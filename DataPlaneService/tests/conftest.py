"""
Shared pytest fixtures and configuration for DataPlaneService tests.

Provides:
- FastAPI TestClient fixtures
- Sample payload builders for Ethernet and FSO frames
- Mock/stub fixtures for external interfaces
- Test data generators
"""
from __future__ import annotations

import pytest
from typing import List, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.state import get_encapsulation_service
from app.services.encapsulation_service import EncapsulationService
from app.models.frame_spec import (
    EncapsulatedSegment,
    FSOHeader,
    EncapsulationRequest,
)


@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient for synchronous API testing."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
async def async_client() -> Generator[AsyncClient, None, None]:
    """Provide an AsyncClient for asynchronous API testing including WebSocket."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
def fresh_service() -> Generator[EncapsulationService, None, None]:
    """Provide a fresh EncapsulationService instance for isolated testing."""
    # Create a new service instance
    service = EncapsulationService()
    yield service
    # Cleanup if needed


@pytest.fixture(scope="function")
def reset_global_service():
    """Reset the global encapsulation service state before each test."""
    # Force recreate singleton
    import app.state as state_module
    state_module._encapsulation_service = None
    yield
    # Clean up after test
    state_module._encapsulation_service = None


@pytest.fixture
def sample_ethernet_frame_64b() -> str:
    """Minimum valid Ethernet frame (64 bytes) as hex string."""
    # Dst MAC (6) + Src MAC (6) + EtherType (2) + Payload (46) + CRC (4) = 64 bytes
    dst_mac = "ffffffffffff"  # broadcast
    src_mac = "aabbccddeeff"
    ethertype = "0800"  # IPv4
    payload = "00" * 46  # minimum payload
    crc = "12345678"  # placeholder CRC
    return dst_mac + src_mac + ethertype + payload + crc


@pytest.fixture
def sample_ethernet_frame_1500b() -> str:
    """Standard Ethernet frame (1500 bytes MTU) as hex string."""
    dst_mac = "001122334455"
    src_mac = "aabbccddeeff"
    ethertype = "0800"
    # Payload: 1500 - 14 (header) - 4 (CRC) = 1482 bytes
    payload = "aa" * 1482
    crc = "abcdef12"
    return dst_mac + src_mac + ethertype + payload + crc


@pytest.fixture
def sample_ethernet_frame_jumbo() -> str:
    """Jumbo Ethernet frame (9000 bytes) as hex string."""
    dst_mac = "ffffffffffff"
    src_mac = "112233445566"
    ethertype = "0800"
    payload = "bb" * 8982  # 9000 - 14 - 4
    crc = "cafebabe"
    return dst_mac + src_mac + ethertype + payload + crc


@pytest.fixture
def sample_encapsulation_request(sample_ethernet_frame_1500b: str) -> EncapsulationRequest:
    """Standard encapsulation request with default parameters."""
    return EncapsulationRequest(
        ethernet_frame_hex=sample_ethernet_frame_1500b,
        max_segment_size=1200,
        fec_scheme="5G-NR-LDPC",
        arq_enabled=True,
    )


@pytest.fixture
def sample_fso_segment() -> EncapsulatedSegment:
    """Sample FSO segment for testing reassembly and RX operations."""
    header = FSOHeader(
        version=1,
        seq=100,
        total_segments=3,
        segment_index=0,
        payload_len=1200,
        crc32=0x12345678,
        fec_scheme="5G-NR-LDPC",
        arq_enabled=True,
        timestamp_ns=1000000000,
    )
    payload_hex = "aa" * 1200
    return EncapsulatedSegment(header=header, payload_hex=payload_hex)


@pytest.fixture
def sample_segment_set() -> List[EncapsulatedSegment]:
    """Set of 3 segments representing a complete frame for reassembly testing."""
    segments = []
    seq = 200
    total = 3
    payload_per_seg = 500
    
    for idx in range(total):
        payload = f"{idx:02x}" * payload_per_seg
        header = FSOHeader(
            version=1,
            seq=seq,
            total_segments=total,
            segment_index=idx,
            payload_len=payload_per_seg,
            crc32=None,  # Will be computed if needed
            fec_scheme=None,
            arq_enabled=True,
            timestamp_ns=1000000000 + idx * 1000000,
        )
        segments.append(EncapsulatedSegment(header=header, payload_hex=payload))
    
    return segments


@pytest.fixture
def invalid_hex_payload() -> str:
    """Invalid hex string for negative testing."""
    return "xyz123"  # contains non-hex characters


@pytest.fixture
def odd_length_hex_payload() -> str:
    """Odd-length hex string for negative testing."""
    return "abc"  # odd length


@pytest.fixture
def empty_payload() -> str:
    """Empty payload for boundary testing."""
    return ""


@pytest.fixture
def max_payload_9216b() -> str:
    """Maximum allowed payload size (9216 bytes)."""
    return "ff" * 9216


# Mock fixtures for hardware interfaces
@pytest.fixture
def mock_fpga_interface():
    """Mock FPGA interface for FEC operations."""
    class MockFPGA:
        def __init__(self):
            self.fec_corrections = 0
            self.crc_errors = 0
        
        def apply_fec(self, data: bytes) -> bytes:
            """Stub FEC application."""
            self.fec_corrections += 1
            return data
        
        def verify_crc(self, data: bytes, crc: int) -> bool:
            """Stub CRC verification."""
            return True
    
    return MockFPGA()


@pytest.fixture
def mock_hardware_unavailable():
    """Marker fixture indicating hardware is not available (for xfail/skip)."""
    return pytest.mark.xfail(reason="Hardware/FPGA not available in test environment")
