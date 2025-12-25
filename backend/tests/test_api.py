"""Tests for API endpoints."""
from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint():
    """Test health check endpoint."""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    """Test root endpoint."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_search_endpoint_no_query():
    """Test search endpoint without query parameter."""
    client = TestClient(app)
    response = client.get("/api/v1/search")
    assert response.status_code == 200
    
    data = response.json()
    assert data["query"] == ""


def test_search_endpoint_structure():
    """Test search endpoint response structure."""
    client = TestClient(app)
    response = client.get("/api/v1/search?q=test")
    assert response.status_code == 200
    
    data = response.json()
    assert "query" in data
    assert "results" in data
    assert "count" in data
    assert isinstance(data["results"], list)


def test_statistics_endpoint_structure():
    """Test statistics endpoint response structure."""
    client = TestClient(app)
    response = client.get("/api/v1/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_repositories" in data
    assert "total_automations" in data
    assert isinstance(data["total_repositories"], int)
    assert isinstance(data["total_automations"], int)


def test_index_endpoint():
    """Test index trigger endpoint in development mode."""
    import os
    
    # Save original environment and set to development
    original_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "development"
    
    try:
        client = TestClient(app)
        response = client.post("/api/v1/index")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "started" in data
        assert data["started"] is True
    finally:
        # Restore original environment
        if original_env is not None:
            os.environ["ENVIRONMENT"] = original_env
        elif "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]


def test_index_endpoint_blocked_in_production():
    """Test that index endpoint is blocked in production."""
    import os
    
    # Save original environment and set to production
    original_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "production"
    
    try:
        client = TestClient(app)
        response = client.post("/api/v1/index")
        assert response.status_code == 403
        
        data = response.json()
        assert "detail" in data
        assert "not available in production" in data["detail"].lower()
    finally:
        # Restore original environment
        if original_env is not None:
            os.environ["ENVIRONMENT"] = original_env
        elif "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]
