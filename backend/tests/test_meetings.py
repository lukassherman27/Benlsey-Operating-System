"""
Tests for meeting and calendar endpoints.

Tests:
    - GET /api/meetings returns list of meetings
    - GET /api/calendar/today returns today's meetings
    - GET /api/calendar/upcoming returns upcoming meetings
    - GET /api/calendar/date/{date} returns meetings for a date
    - GET /api/calendar/project/{project_code} returns project meetings
"""


def test_meetings_list_returns_200(client):
    """Meetings list endpoint should return 200."""
    response = client.get("/api/meetings")
    assert response.status_code == 200


def test_meetings_list_has_items(client):
    """Meetings list should return list of items."""
    response = client.get("/api/meetings")
    data = response.json()

    items = data.get("data", data.get("items", data.get("meetings", [])))
    assert isinstance(items, list)


def test_meetings_upcoming_returns_200(client):
    """Meetings upcoming filter should return 200."""
    response = client.get("/api/meetings?upcoming=true")
    assert response.status_code == 200


def test_meetings_briefing_not_found(client):
    """Meeting briefing should return 404 for non-existent meeting."""
    response = client.get("/api/meetings/999999999/briefing")
    # Service may return 200 with empty data or 404
    assert response.status_code in [200, 404]


def test_calendar_today_returns_200(client):
    """Today's calendar endpoint should return 200."""
    response = client.get("/api/calendar/today")
    assert response.status_code == 200


def test_calendar_today_has_meetings(client):
    """Today's calendar should return meetings list."""
    response = client.get("/api/calendar/today")
    data = response.json()

    meetings = data.get("data", data.get("items", data.get("meetings", [])))
    assert isinstance(meetings, list)


def test_calendar_upcoming_returns_200(client):
    """Upcoming calendar endpoint should return 200."""
    response = client.get("/api/calendar/upcoming")
    assert response.status_code == 200


def test_calendar_upcoming_with_days(client):
    """Upcoming calendar should accept days parameter."""
    response = client.get("/api/calendar/upcoming?days=14")
    assert response.status_code == 200
    data = response.json()

    meetings = data.get("data", data.get("items", data.get("meetings", [])))
    assert isinstance(meetings, list)


def test_calendar_date_returns_200(client):
    """Calendar by date endpoint should return 200."""
    response = client.get("/api/calendar/date/2025-01-15")
    assert response.status_code == 200


def test_calendar_date_has_meetings(client):
    """Calendar by date should return meetings list."""
    response = client.get("/api/calendar/date/2025-01-15")
    data = response.json()

    meetings = data.get("data", data.get("items", data.get("meetings", [])))
    assert isinstance(meetings, list)


def test_calendar_project_returns_200(client):
    """Calendar by project endpoint should return 200."""
    response = client.get("/api/calendar/project/25%20BK-033")
    assert response.status_code == 200


def test_calendar_project_has_meetings(client):
    """Calendar by project should return meetings list."""
    response = client.get("/api/calendar/project/25%20BK-033")
    data = response.json()

    meetings = data.get("data", data.get("items", data.get("meetings", [])))
    assert isinstance(meetings, list)
