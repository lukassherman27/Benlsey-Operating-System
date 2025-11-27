#!/usr/bin/env python3
"""
Test script for admin interface functions
Tests all CRUD operations for validation suggestions and email links
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_get_validation_suggestions():
    """Test GET /api/admin/validation/suggestions"""
    print("\n=== Testing: Get Validation Suggestions ===")
    response = requests.get(f"{BASE_URL}/api/admin/validation/suggestions")
    print(f"Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"✓ Found {data['stats']['pending']} pending suggestions")
        print(f"✓ Total suggestions: {data['total']}")
        return True
    else:
        print(f"✗ Error: {response.text}")
        return False

def test_get_email_links():
    """Test GET /api/admin/email-links"""
    print("\n=== Testing: Get Email Links ===")
    response = requests.get(f"{BASE_URL}/api/admin/email-links?limit=5")
    print(f"Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"✓ Found {data['total']} total email links")
        print(f"✓ Showing {len(data['links'])} links")
        if data['links']:
            first_link = data['links'][0]
            print(f"  - Link ID: {first_link['link_id']}")
            print(f"  - Project: {first_link['project_code']} - {first_link['project_name']}")
            print(f"  - Confidence: {first_link['confidence_score']}")
            return first_link['link_id']
    else:
        print(f"✗ Error: {response.text}")
        return None

def test_unlink_email(link_id: int):
    """Test DELETE /api/admin/email-links/{link_id}"""
    print(f"\n=== Testing: Unlink Email (ID: {link_id}) ===")
    response = requests.delete(
        f"{BASE_URL}/api/admin/email-links/{link_id}?user=test_admin"
    )
    print(f"Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"✓ {data.get('message', 'Success')}")
        return True
    else:
        print(f"✗ Error: {response.text}")
        return False

def test_approve_suggestion(suggestion_id: int):
    """Test POST /api/admin/validation/suggestions/{id}/approve"""
    print(f"\n=== Testing: Approve Suggestion (ID: {suggestion_id}) ===")
    response = requests.post(
        f"{BASE_URL}/api/admin/validation/suggestions/{suggestion_id}/approve",
        headers={"Content-Type": "application/json"},
        json={
            "reviewed_by": "test_admin",
            "notes": "Test approval"
        }
    )
    print(f"Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"✓ {data.get('message', 'Success')}")
        return True
    else:
        print(f"✗ Error: {response.text}")
        return False

def main():
    print("=" * 60)
    print("ADMIN INTERFACE FUNCTION TESTS")
    print("=" * 60)

    # Test 1: Validation Suggestions
    test_get_validation_suggestions()

    # Test 2: Email Links
    link_id = test_get_email_links()

    # Test 3: Unlink (if we have a link_id)
    if link_id:
        test_unlink_email(link_id)

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
