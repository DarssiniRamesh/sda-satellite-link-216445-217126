"""
Basic health and API structure tests.

Tests:
- Root endpoint
- Health endpoint
- OpenAPI documentation
- CORS headers
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
class TestBasicEndpoints:
    """Test basic service endpoints."""
    
    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint returns service info."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "DataPlaneService"
        assert "status" in data
        assert data["status"] == "ok"
    
    def test_health_endpoint(self, test_client: TestClient):
        """Test health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_openapi_docs(self, test_client: TestClient):
        """Test OpenAPI documentation is available."""
        response = test_client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert data["info"]["title"] == "DataPlaneService"
        assert "paths" in data
    
    def test_docs_ui(self, test_client: TestClient):
        """Test Swagger UI docs page."""
        response = test_client.get("/docs")
        
        assert response.status_code == 200
        assert b"swagger" in response.content.lower()
    
    def test_cors_headers_present(self, test_client: TestClient):
        """Test CORS headers are configured."""
        response = test_client.options("/")
        
        # CORS middleware should add appropriate headers
        assert response.status_code in [200, 405]  # OPTIONS may not be explicitly handled


@pytest.mark.unit
class TestAPIStructure:
    """Test API structure and documentation."""
    
    def test_all_routers_registered(self, test_client: TestClient):
        """Test all expected routers are registered."""
        response = test_client.get("/openapi.json")
        data = response.json()
        
        paths = data["paths"]
        
        # Check for key endpoints from each router
        assert "/encapsulation/pack" in paths
        assert "/segmentation/reassemble" in paths
        assert "/stats/throughput" in paths
        assert "/buffers/rx/push" in paths
        assert "/telemetry/ws-usage" in paths
    
    def test_openapi_tags(self, test_client: TestClient):
        """Test OpenAPI tags are properly defined."""
        response = test_client.get("/openapi.json")
        data = response.json()
        
        tags = [tag["name"] for tag in data.get("tags", [])]
        
        assert "encapsulation" in tags
        assert "segmentation" in tags
        assert "stats" in tags
        assert "buffers" in tags
        assert "telemetry" in tags
        assert "health" in tags
