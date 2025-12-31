"""
Tests for proposal endpoints.

Tests:
    - GET /api/proposals/stats returns valid statistics
    - GET /api/proposals returns paginated list
    - GET /api/proposals/at-risk returns at-risk proposals
"""


def test_proposals_stats_returns_200(client):
    """Proposal stats endpoint should return 200."""
    response = client.get("/api/proposals/stats")
    assert response.status_code == 200


def test_proposals_stats_has_required_fields(client):
    """Proposal stats should include key metrics."""
    response = client.get("/api/proposals/stats")
    data = response.json()

    # Stats are nested under 'data' key
    stats = data.get("data", data)

    # Should have core pipeline metrics
    expected_fields = ["active_pipeline", "active_projects", "at_risk"]
    for field in expected_fields:
        assert field in stats, f"Missing field: {field}"

    # Values should be integers
    assert isinstance(stats["active_pipeline"], int)
    assert isinstance(stats["active_projects"], int)


def test_proposals_list_returns_200(client):
    """Proposals list endpoint should return 200."""
    response = client.get("/api/proposals")
    assert response.status_code == 200


def test_proposals_list_has_pagination(client):
    """Proposals list should include pagination metadata."""
    response = client.get("/api/proposals?page=1&per_page=10")
    data = response.json()

    # Should have items/data array
    assert "items" in data or "data" in data or "proposals" in data
    # Pagination info is in 'meta' object
    assert "meta" in data
    meta = data["meta"]
    assert "page" in meta
    assert "per_page" in meta


def test_proposals_list_respects_per_page(client):
    """Proposals list should respect per_page parameter."""
    response = client.get("/api/proposals?page=1&per_page=5")
    data = response.json()

    # Get the actual list (API uses 'items')
    items = data.get("items", data.get("data", data.get("proposals", data)))
    if isinstance(items, list):
        assert len(items) <= 5


def test_proposals_at_risk_returns_200(client):
    """At-risk proposals endpoint should return 200."""
    response = client.get("/api/proposals/at-risk")
    assert response.status_code == 200


def test_proposals_at_risk_has_data_structure(client):
    """At-risk proposals should have proper data structure."""
    response = client.get("/api/proposals/at-risk")
    data = response.json()

    # Should have data array or proposals list
    assert "data" in data or "proposals" in data or isinstance(data, list)


def test_proposals_needs_follow_up_returns_200(client):
    """Needs follow-up endpoint should return 200."""
    response = client.get("/api/proposals/needs-follow-up")
    assert response.status_code == 200


def test_proposals_needs_attention_returns_200(client):
    """Needs attention endpoint should return 200."""
    response = client.get("/api/proposals/needs-attention")
    assert response.status_code == 200


def test_proposals_needs_attention_has_tiers(client):
    """Needs attention should return tiered data."""
    response = client.get("/api/proposals/needs-attention")
    data = response.json()

    assert data.get("success") is True
    assert "summary" in data
    assert "tiers" in data

    # Check tier structure
    tiers = data["tiers"]
    expected_tiers = ["critical", "high", "medium", "watch"]
    for tier in expected_tiers:
        assert tier in tiers


def test_proposal_tracker_stats_returns_200(client):
    """Proposal tracker stats should return 200."""
    response = client.get("/api/proposal-tracker/stats")
    assert response.status_code == 200


def test_proposal_tracker_list_returns_200(client):
    """Proposal tracker list should return 200."""
    response = client.get("/api/proposal-tracker/list")
    assert response.status_code == 200
