"""Tests for ROOT_PATH environment variable configuration."""
import os
import importlib
from fastapi.testclient import TestClient


def test_endpoints_with_root_path_set():
    """Test that endpoints work correctly when ROOT_PATH is set to /api/v1."""
    # Set ROOT_PATH environment variable
    os.environ["ROOT_PATH"] = "/api/v1"
    
    # Reload the main module to pick up the environment variable
    import app.main
    importlib.reload(app.main)
    
    from app.main import app as root_path_app
    
    client = TestClient(root_path_app)
    
    # When ROOT_PATH=/api/v1, endpoints should be accessible without the prefix
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    
    response = client.get("/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total_repositories" in data
    assert "total_automations" in data
    
    response = client.get("/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "results" in data
    assert "count" in data
    
    # Clean up: remove ROOT_PATH and reload module
    del os.environ["ROOT_PATH"]
    importlib.reload(app.main)


def test_endpoints_without_root_path():
    """Test that endpoints work correctly when ROOT_PATH is not set (default behavior)."""
    # Ensure ROOT_PATH is not set
    if "ROOT_PATH" in os.environ:
        del os.environ["ROOT_PATH"]
    
    # Reload the main module
    import app.main
    importlib.reload(app.main)
    
    from app.main import app as default_app
    
    client = TestClient(default_app)
    
    # Without ROOT_PATH, endpoints should require /api/v1 prefix
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    
    response = client.get("/api/v1/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total_repositories" in data
    assert "total_automations" in data
    
    response = client.get("/api/v1/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "results" in data
    
    # Without prefix should fail
    response = client.get("/health")
    assert response.status_code == 404
    
    # Clean up
    importlib.reload(app.main)


def test_openapi_schema_with_root_path():
    """Test that OpenAPI schema includes correct server URL when ROOT_PATH is set."""
    # Set ROOT_PATH environment variable
    os.environ["ROOT_PATH"] = "/api/v1"
    
    # Reload the main module
    import app.main
    importlib.reload(app.main)
    
    from app.main import app as root_path_app
    
    client = TestClient(root_path_app)
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    openapi_schema = response.json()
    assert "servers" in openapi_schema
    assert len(openapi_schema["servers"]) > 0
    # Check that the root_path is reflected in the server URL
    assert openapi_schema["servers"][0]["url"] == "/api/v1"
    
    # Clean up
    del os.environ["ROOT_PATH"]
    importlib.reload(app.main)
