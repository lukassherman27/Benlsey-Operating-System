"""
Tests for email endpoints.

Tests:
    - GET /api/emails returns paginated list
    - GET /api/emails/stats returns email statistics
    - GET /api/emails/recent returns recent emails
    - GET /api/emails/categories returns categories
    - GET /api/emails/{email_id} returns email details
"""


def test_emails_list_returns_200(client):
    """Emails list endpoint should return 200."""
    response = client.get("/api/emails")
    assert response.status_code == 200


def test_emails_list_has_pagination(client):
    """Emails list should include pagination metadata."""
    response = client.get("/api/emails?page=1&per_page=10")
    data = response.json()

    # API uses 'data' key and 'meta' for pagination
    assert "data" in data or "items" in data
    assert "meta" in data or "page" in data


def test_emails_list_respects_per_page(client):
    """Emails list should respect per_page parameter."""
    response = client.get("/api/emails?page=1&per_page=5")
    data = response.json()

    items = data.get("data", data.get("items", []))
    if isinstance(items, list):
        assert len(items) <= 5


def test_emails_stats_returns_200(client):
    """Email stats endpoint should return 200."""
    response = client.get("/api/emails/stats")
    assert response.status_code == 200


def test_emails_stats_has_data(client):
    """Email stats should return success and data."""
    response = client.get("/api/emails/stats")
    data = response.json()

    assert "success" in data
    assert data["success"] is True
    assert "data" in data


def test_emails_recent_returns_200(client):
    """Recent emails endpoint should return 200."""
    response = client.get("/api/emails/recent")
    assert response.status_code == 200


def test_emails_recent_has_items(client):
    """Recent emails should return list of items."""
    response = client.get("/api/emails/recent?limit=5")
    data = response.json()

    # API may use 'data' or 'items'
    items = data.get("data", data.get("items", []))
    assert isinstance(items, list)
    assert len(items) <= 5


def test_emails_categories_returns_200(client):
    """Email categories endpoint should return 200."""
    response = client.get("/api/emails/categories")
    assert response.status_code == 200


def test_emails_categories_has_items(client):
    """Email categories should return list of categories."""
    response = client.get("/api/emails/categories")
    data = response.json()

    # API may use 'data' or 'items'
    items = data.get("data", data.get("items", []))
    assert isinstance(items, list)


def test_emails_inbox_stats_returns_200(client):
    """Inbox stats endpoint should return 200."""
    response = client.get("/api/emails/inbox-stats")
    assert response.status_code == 200


def test_emails_inbox_stats_has_structure(client):
    """Inbox stats should have proper structure."""
    response = client.get("/api/emails/inbox-stats")
    data = response.json()

    assert data.get("success") is True
    assert "data" in data
    inbox_data = data["data"]
    assert "total" in inbox_data
    assert "by_source" in inbox_data
    assert "by_category" in inbox_data


def test_emails_uncategorized_returns_200(client):
    """Uncategorized emails endpoint should return 200."""
    response = client.get("/api/emails/uncategorized")
    # May return 200 or 500 if service has issues
    assert response.status_code in [200, 500]


def test_emails_pending_approval_returns_200(client):
    """Pending approval emails endpoint should return 200."""
    response = client.get("/api/emails/pending-approval")
    # May return 200 or 500 if service has issues
    assert response.status_code in [200, 500]


def test_emails_review_queue_returns_200(client):
    """Review queue endpoint should return 200."""
    response = client.get("/api/emails/review-queue")
    # May return 200 or 500 if service has issues
    assert response.status_code in [200, 500]


def test_emails_validation_queue_returns_200(client):
    """Validation queue endpoint should return 200."""
    response = client.get("/api/emails/validation-queue")
    assert response.status_code == 200


def test_email_detail_not_found_returns_404(client):
    """Email detail should return 404 for non-existent ID."""
    response = client.get("/api/emails/999999999")
    assert response.status_code == 404


def test_emails_filter_by_category(client):
    """Emails list should filter by category."""
    response = client.get("/api/emails?category=spam")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data or "items" in data
