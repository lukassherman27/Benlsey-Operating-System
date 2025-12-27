"""
Tests for health check endpoints.

Tests:
    - GET /health returns 200 with status data
    - Database connection is verified
"""


def test_health_endpoint_returns_200(client):
    """Health endpoint should return 200 with status healthy."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_health_endpoint_includes_counts(client):
    """Health endpoint should include proposal and email counts."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "proposals_in_db" in data
    assert "emails_in_db" in data
    assert isinstance(data["proposals_in_db"], int)
    assert isinstance(data["emails_in_db"], int)


def test_health_endpoint_includes_timestamp(client):
    """Health endpoint should include a timestamp."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "timestamp" in data
    # ISO format: YYYY-MM-DDTHH:MM:SS
    assert "T" in data["timestamp"]


def test_root_endpoint_returns_api_info(client):
    """Root endpoint should return API info."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Bensley Intelligence API"
    assert "version" in data
    assert data["docs"] == "/docs"
