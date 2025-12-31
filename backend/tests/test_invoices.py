"""
Tests for invoice endpoints.

Tests:
    - GET /api/invoices/stats returns statistics
    - GET /api/invoices/aging returns aging breakdown
    - GET /api/invoices/recent returns recent invoices
    - GET /api/invoices/outstanding returns outstanding invoices
    - GET /api/invoices/by-project/{project_code} returns project invoices
"""


def test_invoices_stats_returns_200(client):
    """Invoice stats endpoint should return 200."""
    response = client.get("/api/invoices/stats")
    assert response.status_code == 200


def test_invoices_stats_has_data(client):
    """Invoice stats should return data."""
    response = client.get("/api/invoices/stats")
    data = response.json()

    assert data.get("success") is True
    assert "data" in data


def test_invoices_aging_returns_200(client):
    """Invoice aging endpoint should return 200."""
    response = client.get("/api/invoices/aging")
    assert response.status_code == 200


def test_invoices_aging_has_data(client):
    """Invoice aging should return aging data."""
    response = client.get("/api/invoices/aging")
    data = response.json()

    assert data.get("success") is True
    assert "data" in data


def test_invoices_aging_breakdown_returns_200(client):
    """Invoice aging breakdown endpoint should return 200."""
    response = client.get("/api/invoices/aging-breakdown")
    assert response.status_code == 200


def test_invoices_recent_returns_200(client):
    """Recent invoices endpoint should return 200."""
    response = client.get("/api/invoices/recent")
    assert response.status_code == 200


def test_invoices_recent_has_items(client):
    """Recent invoices should return list of items."""
    response = client.get("/api/invoices/recent?limit=5")
    data = response.json()

    items = data.get("data", data.get("items", []))
    assert isinstance(items, list)
    assert len(items) <= 5


def test_invoices_outstanding_returns_200(client):
    """Outstanding invoices endpoint should return 200."""
    response = client.get("/api/invoices/outstanding")
    assert response.status_code == 200


def test_invoices_outstanding_has_pagination(client):
    """Outstanding invoices should have pagination."""
    response = client.get("/api/invoices/outstanding?page=1&per_page=10")
    data = response.json()

    # Should have pagination info
    assert "meta" in data or "page" in data


def test_invoices_outstanding_filtered_returns_200(client):
    """Filtered outstanding invoices should return 200."""
    response = client.get("/api/invoices/outstanding-filtered?min_days=30")
    assert response.status_code == 200


def test_invoices_recent_paid_returns_200(client):
    """Recent paid invoices endpoint should return 200."""
    response = client.get("/api/invoices/recent-paid")
    assert response.status_code == 200


def test_invoices_largest_outstanding_returns_200(client):
    """Largest outstanding invoices endpoint should return 200."""
    response = client.get("/api/invoices/largest-outstanding")
    assert response.status_code == 200


def test_invoices_oldest_unpaid_returns_200(client):
    """Oldest unpaid invoices endpoint should return 200."""
    response = client.get("/api/invoices/oldest-unpaid-invoices")
    assert response.status_code == 200


def test_invoices_top_outstanding_returns_200(client):
    """Top outstanding invoices endpoint should return 200."""
    response = client.get("/api/invoices/top-outstanding")
    assert response.status_code == 200


def test_invoices_by_project_returns_200(client):
    """Invoices by project endpoint should return 200."""
    response = client.get("/api/invoices/by-project/25%20BK-033")
    assert response.status_code == 200


def test_invoices_by_project_has_items(client):
    """Invoices by project should return list."""
    response = client.get("/api/invoices/by-project/25%20BK-033")
    data = response.json()

    items = data.get("data", data.get("items", data.get("invoices", [])))
    assert isinstance(items, list)


def test_invoices_revenue_trends_returns_200(client):
    """Revenue trends endpoint should return 200."""
    response = client.get("/api/invoices/revenue-trends")
    assert response.status_code == 200


def test_invoices_revenue_trends_has_data(client):
    """Revenue trends should return trend data."""
    response = client.get("/api/invoices/revenue-trends?months=6")
    data = response.json()

    assert data.get("success") is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_invoices_client_payment_behavior_returns_200(client):
    """Client payment behavior endpoint should return 200."""
    response = client.get("/api/invoices/client-payment-behavior")
    assert response.status_code == 200


def test_invoices_client_payment_behavior_has_data(client):
    """Client payment behavior should return client data."""
    response = client.get("/api/invoices/client-payment-behavior?limit=5")
    data = response.json()

    assert data.get("success") is True
    assert "data" in data
    assert isinstance(data["data"], list)
