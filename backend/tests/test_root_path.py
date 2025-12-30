"""Tests for ROOT_PATH environment variable configuration."""

import os
import importlib
import pytest
import sys
from fastapi.testclient import TestClient


@pytest.fixture
def app_with_root_path():
    """Fixture that provides an app instance with ROOT_PATH set."""
    os.environ["ROOT_PATH"] = "/api/v1"

    # Reload the app.main module
    if "app.main" in sys.modules:
        importlib.reload(sys.modules["app.main"])
    else:
        import app.main

    from app.main import app

    yield app

    # Cleanup
    if "ROOT_PATH" in os.environ:
        del os.environ["ROOT_PATH"]
    if "app.main" in sys.modules:
        importlib.reload(sys.modules["app.main"])


@pytest.fixture
def app_without_root_path():
    """Fixture that provides an app instance without ROOT_PATH set."""
    if "ROOT_PATH" in os.environ:
        del os.environ["ROOT_PATH"]

    # Reload the app.main module
    if "app.main" in sys.modules:
        importlib.reload(sys.modules["app.main"])
    else:
        import app.main

    from app.main import app

    yield app

    # Cleanup
    if "app.main" in sys.modules:
        importlib.reload(sys.modules["app.main"])


def test_endpoints_with_root_path_set(app_with_root_path):
    """Test that endpoints work correctly when ROOT_PATH is set to /api/v1."""
    client = TestClient(app_with_root_path)

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


def test_endpoints_without_root_path(app_without_root_path):
    """Test that endpoints work correctly when ROOT_PATH is not set (default behavior)."""
    client = TestClient(app_without_root_path)

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


def test_openapi_schema_with_root_path(app_with_root_path):
    """Test that OpenAPI schema includes correct server URL when ROOT_PATH is set."""
    client = TestClient(app_with_root_path)

    response = client.get("/openapi.json")
    assert response.status_code == 200

    openapi_schema = response.json()
    assert "servers" in openapi_schema
    assert len(openapi_schema["servers"]) > 0
    # Check that the root_path is reflected in the server URL
    assert openapi_schema["servers"][0]["url"] == "/api/v1"
