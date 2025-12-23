"""Tests for rate limiting on the index endpoint."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.routes import last_indexing_time, INDEXING_COOLDOWN_MINUTES
import time


def test_index_rate_limiting():
    """Test that the index endpoint enforces rate limiting."""
    client = TestClient(app)
    
    # Reset the rate limit state
    import app.api.routes as routes_module
    routes_module.last_indexing_time = None
    
    # First request should succeed
    response1 = client.post("/api/v1/index")
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["started"] is True
    
    # Second immediate request should be rate limited
    response2 = client.post("/api/v1/index")
    assert response2.status_code == 429
    data2 = response2.json()
    assert "rate limit" in data2["detail"].lower()
    assert "wait" in data2["detail"].lower()
    
    # Reset for other tests
    routes_module.last_indexing_time = None


def test_index_rate_limit_message():
    """Test that the rate limit message includes time remaining."""
    client = TestClient(app)
    
    # Reset the rate limit state
    import app.api.routes as routes_module
    routes_module.last_indexing_time = None
    
    # Trigger first request
    response1 = client.post("/api/v1/index")
    assert response1.status_code == 200
    
    # Second request should show remaining time
    response2 = client.post("/api/v1/index")
    assert response2.status_code == 429
    data = response2.json()
    
    # Check that the message contains time information
    assert "m" in data["detail"]  # minutes
    assert "s" in data["detail"]  # seconds
    
    # Reset for other tests
    routes_module.last_indexing_time = None
