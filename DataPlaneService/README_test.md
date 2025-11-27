# DataPlaneService Test Suite

Comprehensive pytest-based test suite for the DataPlaneService FastAPI backend.

## Overview

This test suite provides unit, integration, and boundary tests for all DataPlaneService endpoints and core business logic. Tests are organized by functionality and marked with pytest markers for selective execution.

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures and configuration
├── test_health_basic.py                 # Health checks and basic API structure
├── test_encapsulation_endpoints.py      # Encapsulation REST API tests
├── test_segmentation_endpoints.py       # Segmentation/reassembly API tests
├── test_buffers_endpoints.py            # Buffer management API tests
├── test_stats_endpoints.py              # Stats and telemetry API tests
├── test_websocket_telemetry.py          # WebSocket streaming tests
├── test_encapsulation_service.py        # EncapsulationService unit tests
├── test_integration_full_flow.py        # End-to-end integration tests
└── test_boundary_negative.py            # Boundary and negative test cases
```

## Prerequisites

Install test dependencies:

```bash
pip install -r requirements.txt
```

Or install test dependencies separately:

```bash
pip install pytest pytest-asyncio httpx anyio pytest-cov pytest-timeout
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Test Categories

**Unit tests only:**
```bash
pytest -m unit
```

**Integration tests only:**
```bash
pytest -m integration
```

**Boundary tests only:**
```bash
pytest -m boundary
```

**Negative tests only:**
```bash
pytest -m negative
```

**Skip hardware-dependent tests:**
```bash
pytest -m "not hardware"
```

**WebSocket tests only:**
```bash
pytest -m websocket
```

**FEC/CRC validation tests:**
```bash
pytest -m fec
```

**ARQ behavior tests:**
```bash
pytest -m arq
```

### Run Specific Test Files

```bash
pytest tests/test_encapsulation_endpoints.py
pytest tests/test_integration_full_flow.py -v
```

### Run Specific Test Classes or Functions

```bash
pytest tests/test_encapsulation_endpoints.py::TestEncapsulationPack
pytest tests/test_encapsulation_endpoints.py::TestEncapsulationPack::test_pack_standard_frame
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

View coverage report:
```bash
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
```

### Run in Parallel (if pytest-xdist installed)

```bash
pip install pytest-xdist
pytest -n auto
```

## Test Markers

Tests are marked with the following categories:

| Marker       | Description                                              |
|--------------|----------------------------------------------------------|
| `unit`       | Unit tests for isolated components                       |
| `integration`| Integration tests requiring service interaction          |
| `hardware`   | Tests requiring hardware/FPGA (xfail in CI)              |
| `slow`       | Tests that take significant time                         |
| `websocket`  | WebSocket-related tests                                  |
| `arq`        | ARQ behavior tests                                       |
| `fec`        | FEC/CRC validation tests                                 |
| `boundary`   | Boundary and edge case tests                             |
| `negative`   | Negative test cases for error handling                   |

### Marker Examples

Run only fast tests (exclude slow):
```bash
pytest -m "not slow"
```

Run unit and integration tests:
```bash
pytest -m "unit or integration"
```

Run everything except hardware tests:
```bash
pytest -m "not hardware"
```

## Test Coverage

The test suite covers:

### REST API Endpoints

- ✅ `POST /encapsulation/pack` - Ethernet frame encapsulation
  - Standard frames (1500 bytes)
  - Minimum frames (64 bytes)
  - Jumbo frames (9000 bytes)
  - Multiple segments
  - Invalid hex payloads
  - Odd-length payloads
  - Empty payloads
  - Invalid segment sizes

- ✅ `GET /encapsulation/tx/dequeue` - TX segment retrieval
  - Empty queue
  - After encapsulation
  - Partial dequeue
  - Invalid parameters

- ✅ `GET /encapsulation/rx/dequeue` - RX segment retrieval
  - Empty queue
  - After RX push
  - Invalid parameters

- ✅ `POST /segmentation/reassemble` - Frame reassembly
  - Complete frame reassembly
  - Out-of-order segments
  - Partial reassembly (missing segments)
  - Duplicate segments
  - Empty segments list
  - Invalid segment structure
  - Invalid payload hex

- ✅ `POST /buffers/rx/push` - RX segment ingestion
  - Valid segments
  - Multiple segments
  - Invalid segment structure
  - Invalid payload hex
  - Empty payload

- ✅ `GET /stats/throughput` - Throughput and latency stats
  - Initial state
  - After traffic

- ✅ `GET /stats/buffers` - Buffer status
  - Initial state
  - After encapsulation
  - After RX push

- ✅ `GET /stats/telemetry` - CRC/FEC/ARQ counters
  - Initial state
  - Counter structure

- ✅ `GET /health` - Health check
- ✅ `GET /` - Root endpoint
- ✅ `GET /telemetry/ws-usage` - WebSocket usage help
- ✅ `WS /telemetry/ws` - WebSocket telemetry streaming

### Core Business Logic

- ✅ **EncapsulationService**
  - Frame encapsulation with segmentation
  - CRC32 generation and validation
  - Sequence numbering
  - TX/RX queue management
  - Reassembly state tracking
  - MTU enforcement (64-9216 bytes)
  - Throughput and latency calculation
  - Telemetry counter tracking

### Integration Scenarios

- ✅ Full flow: Encapsulate → TX dequeue → RX push → Reassemble
- ✅ Multiple frame handling
- ✅ Stats reflection of traffic
- ✅ In-order delivery guarantees
- ✅ Sequence number ordering

### Boundary and Negative Cases

- ✅ Maximum frame size (9216 bytes)
- ✅ Minimum frame size (64 bytes)
- ✅ Frames exceeding maximum
- ✅ Frames below minimum
- ✅ Invalid CRC
- ✅ Out-of-order segments
- ✅ Malformed payloads
- ✅ Empty payloads
- ✅ Invalid segment sizes
- ✅ Malformed JSON
- ✅ Missing required fields
- ✅ Negative values
- ✅ Invalid protocol versions
- ✅ Segment index out of bounds
- ✅ Payload length mismatches

### Hardware/FPGA Stubs

- ✅ Tests marked with `@pytest.mark.hardware` are expected to xfail in CI
- ✅ FEC integration stubs (5G-NR-LDPC)
- ✅ CRC validation stubs
- ✅ ARQ behavior stubs

## CI/Headless Execution

Tests are designed to run headlessly in containerized CI environments:

```bash
# Non-interactive mode (suitable for CI)
pytest --tb=short --disable-warnings --color=yes
```

### Environment Variables

No environment variables are required for tests. The test suite uses:
- In-memory service instances
- Fresh state per test (via fixtures)
- Mock/stub interfaces for external dependencies

### Docker Execution

Run tests inside the container:

```bash
docker exec -it <container_name> pytest
```

## Fixtures

### TestClient Fixtures

- `test_client` - Synchronous FastAPI TestClient
- `async_client` - Asynchronous httpx AsyncClient
- `fresh_service` - Fresh EncapsulationService instance
- `reset_global_service` - Reset global service state

### Sample Data Fixtures

- `sample_ethernet_frame_64b` - Minimum 64-byte frame
- `sample_ethernet_frame_1500b` - Standard 1500-byte frame
- `sample_ethernet_frame_jumbo` - Jumbo 9000-byte frame
- `sample_encapsulation_request` - Standard encapsulation request
- `sample_fso_segment` - Sample FSO segment
- `sample_segment_set` - Set of 3 segments for reassembly
- `invalid_hex_payload` - Invalid hex string
- `odd_length_hex_payload` - Odd-length hex string
- `empty_payload` - Empty payload
- `max_payload_9216b` - Maximum 9216-byte payload

### Mock Fixtures

- `mock_fpga_interface` - Mock FPGA for FEC operations
- `mock_hardware_unavailable` - Marker for hardware-dependent tests

## Troubleshooting

### Import Errors

Ensure the service root is in PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

Or run from the service root directory.

### Test Failures Due to State

If tests fail due to shared state, ensure you're using the `reset_global_service` fixture:

```python
def test_my_test(test_client, reset_global_service):
    # Test will have fresh service state
    ...
```

### WebSocket Timeout

WebSocket tests have 2-second timeouts to avoid hanging. If tests timeout:
- Ensure the service is not blocking
- Check for deadlocks in async code
- Verify WebSocket endpoint is properly implemented

### Hardware Tests Failing

Hardware-dependent tests are marked with `@pytest.mark.hardware` and should xfail/skip:

```bash
pytest -m "not hardware"  # Skip hardware tests
```

## Extending the Test Suite

### Adding New Tests

1. Create test file in `tests/` with prefix `test_`
2. Use appropriate markers: `@pytest.mark.unit`, `@pytest.mark.integration`, etc.
3. Use existing fixtures from `conftest.py` or add new ones
4. Follow naming convention: `test_<functionality>_<scenario>`

### Adding New Fixtures

Add to `tests/conftest.py`:

```python
@pytest.fixture
def my_custom_fixture():
    """Fixture description."""
    data = create_test_data()
    yield data
    # Cleanup if needed
```

### Adding New Markers

Add to `pytest.ini`:

```ini
markers =
    mymarker: Description of the marker
```

## Contributing

- Ensure all tests pass before committing: `pytest`
- Maintain >80% code coverage: `pytest --cov=app`
- Add tests for all new features and bug fixes
- Use descriptive test names and docstrings
- Mark tests appropriately for CI execution

## Contact

For issues or questions about the test suite, refer to the main project documentation or open an issue.
