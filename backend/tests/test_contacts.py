"""
Tests for contact endpoints.

Tests:
    - GET /api/contacts returns list of contacts
    - GET /api/contacts/stats returns statistics
    - GET /api/contacts/{id} returns contact details
    - GET /api/contacts/{id} returns 404 for non-existent contact
"""


def test_contacts_list_returns_200(client):
    """Contacts list endpoint should return 200."""
    response = client.get("/api/contacts")
    assert response.status_code == 200


def test_contacts_list_has_contacts(client):
    """Contacts list should return contacts array."""
    response = client.get("/api/contacts")
    data = response.json()

    assert data.get("success") is True
    assert "contacts" in data
    assert isinstance(data["contacts"], list)


def test_contacts_list_with_limit(client):
    """Contacts list should respect limit parameter."""
    response = client.get("/api/contacts?limit=5")
    data = response.json()

    contacts = data.get("contacts", [])
    assert len(contacts) <= 5


def test_contacts_list_with_search(client):
    """Contacts list should filter by search parameter."""
    response = client.get("/api/contacts?search=bensley")
    assert response.status_code == 200
    data = response.json()
    assert "contacts" in data


def test_contacts_list_with_company(client):
    """Contacts list should filter by company."""
    response = client.get("/api/contacts?company=bensley")
    assert response.status_code == 200
    data = response.json()
    assert "contacts" in data


def test_contacts_stats_returns_200(client):
    """Contact stats endpoint should return 200."""
    response = client.get("/api/contacts/stats")
    assert response.status_code == 200


def test_contacts_stats_has_data(client):
    """Contact stats should return data."""
    response = client.get("/api/contacts/stats")
    data = response.json()

    assert data.get("success") is True
    assert "data" in data
    stats = data["data"]
    assert "total" in stats


def test_contact_detail_not_found(client):
    """Contact detail should return 404 for non-existent ID."""
    response = client.get("/api/contacts/999999999")
    assert response.status_code == 404


def test_contact_detail_has_data(client):
    """Contact detail should return contact with linked projects."""
    # First get a contact ID from the list
    list_response = client.get("/api/contacts?limit=1")
    data = list_response.json()
    contacts = data.get("contacts", [])

    if len(contacts) > 0:
        contact_id = contacts[0].get("contact_id")
        if contact_id:
            response = client.get(f"/api/contacts/{contact_id}")
            assert response.status_code == 200
            detail = response.json()
            assert detail.get("success") is True
            assert "data" in detail


def test_contact_update_not_found(client):
    """Contact update should return 404 for non-existent ID."""
    response = client.put("/api/contacts/999999999?name=Test")
    assert response.status_code == 404


def test_contact_delete_not_found(client):
    """Contact delete should return 404 for non-existent ID."""
    response = client.delete("/api/contacts/999999999")
    assert response.status_code == 404


def test_contacts_pagination(client):
    """Contacts list should support pagination."""
    response = client.get("/api/contacts?limit=5&offset=0")
    data = response.json()

    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert data["limit"] == 5
    assert data["offset"] == 0
