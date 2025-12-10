#!/usr/bin/env python3
"""
Test script for role-based dashboard stats endpoints
Run after starting the backend server: uvicorn api.main:app --reload --port 8000
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(role=None):
    """Test the dashboard stats endpoint with optional role parameter"""
    url = f"{BASE_URL}/api/dashboard/stats"
    params = {"role": role} if role else {}

    print(f"\n{'='*80}")
    print(f"Testing: GET {url}" + (f"?role={role}" if role else ""))
    print(f"{'='*80}")

    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse:")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"Error: {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("ERROR: Backend server is not running!")
        print("Start it with: cd backend && uvicorn api.main:app --reload --port 8000")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print(f"Dashboard Stats Endpoint Testing - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test all three roles
    test_endpoint("bill")
    test_endpoint("pm")
    test_endpoint("finance")

    # Test legacy endpoint (no role)
    print("\n\n")
    print("Testing legacy endpoint (backward compatibility)...")
    test_endpoint()

    print(f"\n{'='*80}")
    print("Testing complete!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
