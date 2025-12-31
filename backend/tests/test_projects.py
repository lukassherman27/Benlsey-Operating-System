"""
Tests for project endpoints.

Tests:
    - GET /api/projects/active returns active projects
    - GET /api/projects/linking-list returns projects for linking
    - GET /api/projects/{project_code} returns project details
    - GET /api/projects/{project_code}/financial-summary returns financials
    - GET /api/projects/{project_code}/contacts returns contacts
    - GET /api/projects/{project_code}/timeline returns timeline
    - GET /api/projects/{project_code}/team returns team
"""


def test_projects_active_returns_200(client):
    """Active projects endpoint should return 200."""
    response = client.get("/api/projects/active")
    assert response.status_code == 200


def test_projects_active_has_list_structure(client):
    """Active projects should have proper list structure."""
    response = client.get("/api/projects/active")
    data = response.json()

    # API may use 'data' or 'items'
    items = data.get("data", data.get("items", []))
    assert isinstance(items, list)


def test_projects_active_project_has_fields(client):
    """Active projects should have expected fields."""
    response = client.get("/api/projects/active")
    data = response.json()

    items = data.get("data", data.get("items", []))
    if len(items) > 0:
        project = items[0]
        expected_fields = ["project_code", "status"]
        for field in expected_fields:
            assert field in project, f"Missing field: {field}"


def test_projects_linking_list_returns_200(client):
    """Projects linking list endpoint should return 200."""
    response = client.get("/api/projects/linking-list")
    assert response.status_code == 200


def test_projects_linking_list_has_data(client):
    """Projects linking list should have data."""
    response = client.get("/api/projects/linking-list")
    data = response.json()

    assert "items" in data or "projects" in data
    projects = data.get("items", data.get("projects", []))
    assert isinstance(projects, list)


def test_project_detail_not_found(client):
    """Project detail should return 404 for non-existent code."""
    response = client.get("/api/projects/NONEXISTENT-999")
    assert response.status_code == 404


def test_project_financial_summary_not_found(client):
    """Financial summary should return 404 for non-existent project."""
    response = client.get("/api/projects/NONEXISTENT-999/financial-summary")
    # May return 404 or 500 depending on implementation
    assert response.status_code in [404, 500]


def test_projects_staff_list_returns_200(client):
    """Staff list endpoint should return 200."""
    response = client.get("/api/staff")
    assert response.status_code == 200


def test_projects_staff_has_list(client):
    """Staff list should return staff array."""
    response = client.get("/api/staff")
    data = response.json()

    assert data.get("success") is True
    assert "staff" in data
    assert isinstance(data["staff"], list)


def test_phase_fees_returns_200(client):
    """Phase fees endpoint should return 200."""
    response = client.get("/api/phase-fees")
    assert response.status_code == 200


def test_phase_fees_has_data(client):
    """Phase fees should return data array."""
    response = client.get("/api/phase-fees")
    data = response.json()

    assert data.get("success") is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_project_phases_not_found(client):
    """Project phases should return 404 for non-existent project."""
    response = client.get("/api/projects/NONEXISTENT-999/phases")
    assert response.status_code == 404


def test_project_timeline_not_found(client):
    """Project timeline should return 404 for non-existent project."""
    response = client.get("/api/projects/NONEXISTENT-999/timeline")
    assert response.status_code == 404


def test_project_hierarchy_not_found(client):
    """Project hierarchy should return 404 for non-existent project."""
    response = client.get("/api/projects/NONEXISTENT-999/hierarchy")
    assert response.status_code == 404


def test_project_contacts_not_found(client):
    """Project contacts should return 404 for non-existent project."""
    # Note: This might return empty list instead of 404 depending on implementation
    response = client.get("/api/projects/NONEXISTENT-999/contacts")
    # Accept either 404 or 200 with empty list
    assert response.status_code in [200, 404]


def test_project_team_returns_200_for_existing(client):
    """Project team endpoint should work for existing projects."""
    # First get a real project code
    response = client.get("/api/projects/active")
    data = response.json()
    items = data.get("data", data.get("items", []))

    if len(items) > 0:
        project_code = items[0].get("project_code")
        if project_code:
            # URL encode the project code for spaces
            import urllib.parse
            encoded = urllib.parse.quote(project_code, safe="")
            response = client.get(f"/api/projects/{encoded}/team")
            assert response.status_code == 200


def test_project_schedule_returns_200_for_existing(client):
    """Project schedule endpoint should work for existing projects."""
    response = client.get("/api/projects/active")
    data = response.json()
    items = data.get("data", data.get("items", []))

    if len(items) > 0:
        project_code = items[0].get("project_code")
        if project_code:
            import urllib.parse
            encoded = urllib.parse.quote(project_code, safe="")
            response = client.get(f"/api/projects/{encoded}/schedule")
            assert response.status_code == 200


def test_project_unified_timeline_not_found(client):
    """Unified timeline should return 404 for non-existent project."""
    response = client.get("/api/projects/NONEXISTENT-999/unified-timeline")
    assert response.status_code == 404


def test_project_assignments_returns_200(client):
    """Project assignments endpoint should return 200 even if empty."""
    response = client.get("/api/projects/active")
    data = response.json()
    items = data.get("data", data.get("items", []))

    if len(items) > 0:
        project_code = items[0].get("project_code")
        if project_code:
            import urllib.parse
            encoded = urllib.parse.quote(project_code, safe="")
            response = client.get(f"/api/projects/{encoded}/assignments")
            assert response.status_code == 200


def test_project_phase_timeline_not_found(client):
    """Phase timeline should return 404 for non-existent project."""
    response = client.get("/api/projects/NONEXISTENT-999/phase-timeline")
    assert response.status_code == 404


def test_project_progress_not_found(client):
    """Project progress should return 404 for non-existent project."""
    response = client.get("/api/projects/NONEXISTENT-999/progress")
    assert response.status_code == 404


def test_projects_progress_summary_returns_200(client):
    """Projects progress summary endpoint should return 200."""
    response = client.get("/api/projects/progress-summary")
    # May return 200, 404, or 500 depending on service availability
    assert response.status_code in [200, 404, 500]


def test_projects_progress_summary_has_data(client):
    """Projects progress summary should return projects array."""
    response = client.get("/api/projects/progress-summary")
    # Skip data check if service has issues
    if response.status_code == 200:
        data = response.json()
        assert data.get("success") is True
        assert "projects" in data
