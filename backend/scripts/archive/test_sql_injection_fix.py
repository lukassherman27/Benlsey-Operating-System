#!/usr/bin/env python3
"""
Test SQL Injection Fix

Verifies that the SQL injection vulnerability has been patched.
Tests both valid and malicious sort parameters.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.proposal_service import ProposalService
from services.email_service import EmailService

def test_proposal_service():
    """Test proposal service SQL injection protection"""
    print("=" * 80)
    print("TESTING PROPOSAL SERVICE")
    print("=" * 80)

    service = ProposalService()

    # Test 1: Valid sort parameters
    print("\n✅ Test 1: Valid sort parameters")
    try:
        result = service.get_all_proposals(
            page=1,
            per_page=5,
            sort_by='project_code',
            sort_order='ASC'
        )
        print(f"   SUCCESS: Retrieved {len(result['items'])} proposals")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 2: Invalid sort column (SQL injection attempt)
    print("\n🔒 Test 2: SQL injection attempt with malicious column")
    try:
        result = service.get_all_proposals(
            page=1,
            per_page=5,
            sort_by='project_code; DROP TABLE proposals--',
            sort_order='ASC'
        )
        print(f"   ❌ FAILED: SQL injection was NOT blocked!")
        return False
    except ValueError as e:
        print(f"   ✅ SUCCESS: SQL injection blocked - {e}")
    except Exception as e:
        print(f"   ❌ FAILED with unexpected error: {e}")
        return False

    # Test 3: Invalid sort order
    print("\n🔒 Test 3: Invalid sort order attempt")
    try:
        result = service.get_all_proposals(
            page=1,
            per_page=5,
            sort_by='project_code',
            sort_order='ASC; DROP TABLE proposals--'
        )
        print(f"   ❌ FAILED: Invalid sort order was NOT blocked!")
        return False
    except ValueError as e:
        print(f"   ✅ SUCCESS: Invalid sort order blocked - {e}")
    except Exception as e:
        print(f"   ❌ FAILED with unexpected error: {e}")
        return False

    # Test 4: All valid sort columns
    print("\n✅ Test 4: Testing all valid sort columns")
    valid_columns = [
        'proposal_id', 'project_code', 'project_name', 'status',
        'health_score', 'days_since_contact', 'is_active_project',
        'created_at', 'updated_at'
    ]

    for column in valid_columns:
        try:
            result = service.get_all_proposals(
                page=1,
                per_page=1,
                sort_by=column,
                sort_order='DESC'
            )
            print(f"   ✅ {column}: SUCCESS")
        except Exception as e:
            print(f"   ❌ {column}: FAILED - {e}")
            return False

    return True


def test_email_service():
    """Test email service SQL injection protection"""
    print("\n" + "=" * 80)
    print("TESTING EMAIL SERVICE")
    print("=" * 80)

    service = EmailService()

    # Test 1: Valid sort parameters
    print("\n✅ Test 1: Valid sort parameters")
    try:
        result = service.get_all_emails(
            page=1,
            per_page=5,
            sort_by='date',
            sort_order='DESC'
        )
        print(f"   SUCCESS: Retrieved {len(result['items'])} emails")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 2: Invalid sort column (SQL injection attempt)
    print("\n🔒 Test 2: SQL injection attempt")
    try:
        result = service.get_all_emails(
            page=1,
            per_page=5,
            sort_by='date; DELETE FROM emails--',
            sort_order='DESC'
        )
        print(f"   ❌ FAILED: SQL injection was NOT blocked!")
        return False
    except ValueError as e:
        print(f"   ✅ SUCCESS: SQL injection blocked - {e}")
    except Exception as e:
        print(f"   ❌ FAILED with unexpected error: {e}")
        return False

    # Test 3: All valid sort columns
    print("\n✅ Test 3: Testing all valid sort columns")
    valid_columns = ['date', 'sender_email', 'subject', 'email_id']

    for column in valid_columns:
        try:
            result = service.get_all_emails(
                page=1,
                per_page=1,
                sort_by=column,
                sort_order='ASC'
            )
            print(f"   ✅ {column}: SUCCESS")
        except Exception as e:
            print(f"   ❌ {column}: FAILED - {e}")
            return False

    return True


def main():
    print("\n" + "=" * 80)
    print("SQL INJECTION FIX VERIFICATION TEST")
    print("=" * 80)

    all_passed = True

    # Test proposal service
    if not test_proposal_service():
        all_passed = False

    # Test email service
    if not test_email_service():
        all_passed = False

    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED - SQL INJECTION VULNERABILITY FIXED!")
    else:
        print("❌ SOME TESTS FAILED - REVIEW FIXES")
    print("=" * 80)
    print()

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
