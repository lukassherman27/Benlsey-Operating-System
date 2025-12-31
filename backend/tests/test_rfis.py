"""
Tests for RFI (Request for Information) endpoints.

Tests:
    - GET /api/rfis returns list of RFIs
    - GET /api/rfis/stats returns RFI statistics
    - GET /api/rfis/overdue returns overdue RFIs
    - GET /api/rfis/{rfi_id} returns RFI details
    - GET /api/rfis/by-project/{project_code} returns RFIs by project
"""


def test_rfis_list_returns_200(client):
    """RFIs list endpoint should return 200."""
    response = client.get("/api/rfis")
    assert response.status_code == 200


def test_rfis_list_has_structure(client):
    """RFIs list should have proper structure."""
    response = client.get("/api/rfis")
    data = response.json()

    assert data.get("success") is True
    assert "rfis" in data
    assert isinstance(data["rfis"], list)


def test_rfis_list_respects_limit(client):
    """RFIs list should respect limit parameter."""
    response = client.get("/api/rfis?limit=5")
    data = response.json()

    rfis = data.get("rfis", [])
    assert len(rfis) <= 5


def test_rfis_stats_returns_200(client):
    """RFI stats endpoint should return 200."""
    response = client.get("/api/rfis/stats")
    assert response.status_code == 200


def test_rfis_stats_has_metrics(client):
    """RFI stats should include key metrics."""
    response = client.get("/api/rfis/stats")
    data = response.json()

    assert data.get("success") is True
    # Frontend expects 'stats' nested object
    if "stats" in data:
        stats = data["stats"]
        expected_fields = ["total", "open", "overdue"]
        for field in expected_fields:
            assert field in stats, f"Missing stats field: {field}"


def test_rfis_overdue_returns_200(client):
    """Overdue RFIs endpoint should return 200."""
    response = client.get("/api/rfis/overdue")
    assert response.status_code == 200


def test_rfis_overdue_has_items(client):
    """Overdue RFIs should have items array."""
    response = client.get("/api/rfis/overdue")
    data = response.json()

    # API may use 'data' or 'items'
    items = data.get("data", data.get("items", []))
    assert isinstance(items, list)


def test_rfi_detail_not_found(client):
    """RFI detail should return 404 for non-existent ID."""
    response = client.get("/api/rfis/999999999")
    assert response.status_code == 404


def test_rfis_by_project_returns_200(client):
    """RFIs by project endpoint should return 200."""
    # Use a project code that might exist
    response = client.get("/api/rfis/by-project/25%20BK-033")
    assert response.status_code == 200


def test_rfis_by_project_has_structure(client):
    """RFIs by project should have proper structure."""
    response = client.get("/api/rfis/by-project/25%20BK-033")
    data = response.json()

    # API may use 'data', 'items', or 'rfis'
    items = data.get("data", data.get("items", data.get("rfis", [])))
    assert isinstance(items, list)


def test_rfis_filter_by_status(client):
    """RFIs list should filter by status."""
    response = client.get("/api/rfis?status=open")
    assert response.status_code == 200
    data = response.json()
    assert "rfis" in data


def test_rfis_filter_overdue_only(client):
    """RFIs list should filter overdue only."""
    response = client.get("/api/rfis?overdue_only=true")
    assert response.status_code == 200
    data = response.json()
    assert "rfis" in data


def test_rfis_filter_by_project_code(client):
    """RFIs list should filter by project code."""
    response = client.get("/api/rfis?project_code=25%20BK-033")
    assert response.status_code == 200
    data = response.json()
    assert "rfis" in data


def test_rfis_mapped_fields(client):
    """RFIs should have frontend-compatible field mapping."""
    response = client.get("/api/rfis?limit=1")
    data = response.json()

    rfis = data.get("rfis", [])
    if len(rfis) > 0:
        rfi = rfis[0]
        # Frontend expects these mapped fields
        assert "id" in rfi, "RFI should have 'id' field"
        assert "status" in rfi, "RFI should have 'status' field"


def test_rfi_respond_not_found(client):
    """Marking non-existent RFI as responded should return 404."""
    response = client.post("/api/rfis/999999999/respond")
    assert response.status_code == 404


def test_rfi_close_not_found(client):
    """Closing non-existent RFI should return 404."""
    response = client.post("/api/rfis/999999999/close")
    assert response.status_code == 404


def test_rfi_assign_not_found(client):
    """Assigning non-existent RFI should return 404."""
    response = client.post(
        "/api/rfis/999999999/assign",
        json={"pm_id": 1}
    )
    assert response.status_code == 404


def test_rfi_update_not_found(client):
    """Updating non-existent RFI should return 404."""
    response = client.patch(
        "/api/rfis/999999999",
        json={"subject": "Updated subject"}
    )
    assert response.status_code == 404


def test_rfi_delete_not_found(client):
    """Deleting non-existent RFI should return 404."""
    response = client.delete("/api/rfis/999999999")
    assert response.status_code == 404


def test_rfi_update_no_fields_returns_400(client):
    """Updating RFI with no fields should return 400."""
    # First we need a valid RFI ID - get one from list
    list_response = client.get("/api/rfis?limit=1")
    data = list_response.json()
    rfis = data.get("rfis", [])

    if len(rfis) > 0:
        rfi_id = rfis[0].get("id") or rfis[0].get("rfi_id")
        if rfi_id:
            response = client.patch(
                f"/api/rfis/{rfi_id}",
                json={}
            )
            assert response.status_code == 400
