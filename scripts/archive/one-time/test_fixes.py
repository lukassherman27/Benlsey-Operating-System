#!/usr/bin/env python3
"""
Test fixes for email classification issues:
1. @bensley.com emails in INBOX should be classified as internal
2. No placeholder project codes like "25 BK-XXX"
3. New suggestion types should insert successfully
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.context_aware_suggestion_service import get_context_aware_service


def test_fixes():
    service = get_context_aware_service()

    # Test emails: 3 from @bensley.com in INBOX, 2 external
    test_emails = [2024210, 2024645, 2024644, 2024306, 2024213]

    print("\n=== Testing Fixes ===\n")

    issues_found = []

    for email_id in test_emails:
        # Get email info
        email_info = service.execute_query("""
            SELECT email_id, sender_email, folder, subject
            FROM emails WHERE email_id = ?
        """, (email_id,), fetch_one=True)

        if not email_info:
            print(f"Email {email_id} not found, skipping")
            continue

        sender = email_info['sender_email']
        is_bensley = '@bensley.com' in sender.lower() or '@bensleydesign.com' in sender.lower()

        print(f"Processing: {email_id}")
        print(f"  Sender: {sender}")
        print(f"  Folder: {email_info['folder']}")
        print(f"  Expected type: {'internal' if is_bensley else 'external (client/operator/etc)'}")

        # Run analysis
        result = service.generate_suggestions_for_email(email_id)

        if result.get('success'):
            # Check classification
            classified = service.execute_query("""
                SELECT email_type, is_project_related FROM emails WHERE email_id = ?
            """, (email_id,), fetch_one=True)

            actual_type = classified.get('email_type') if classified else 'unknown'
            print(f"  Actual type: {actual_type}")

            # Check Fix 1: @bensley.com should be internal
            if is_bensley and actual_type != 'internal':
                issues_found.append(f"FIX 1 FAILED: Email {email_id} from {sender} classified as {actual_type}, expected internal")
                print(f"  ❌ FIX 1 FAILED: Should be internal!")
            elif is_bensley and actual_type == 'internal':
                print(f"  ✓ FIX 1 OK: Correctly classified as internal")

            # Check suggestions for placeholder codes
            suggestions = service.execute_query("""
                SELECT suggestion_id, project_code, title, suggested_data
                FROM ai_suggestions
                WHERE source_id = ? AND source_type = 'email'
                ORDER BY created_at DESC
            """, (email_id,))

            print(f"  Suggestions created: {len(suggestions) if suggestions else 0}")

            for s in (suggestions or []):
                code = s.get('project_code', '')
                if code and ('XXX' in code or code.endswith('XX')):
                    issues_found.append(f"FIX 2 FAILED: Placeholder code '{code}' in suggestion {s['suggestion_id']}")
                    print(f"  ❌ FIX 2 FAILED: Placeholder code '{code}'")
                elif code:
                    print(f"  ✓ FIX 2 OK: Valid code '{code}'")

            print(f"  Cost: ${result.get('usage', {}).get('estimated_cost_usd', 0):.6f}")
        else:
            error = result.get('error', 'Unknown error')
            if 'CHECK constraint' in error:
                issues_found.append(f"FIX 3 FAILED: CHECK constraint error for email {email_id}")
                print(f"  ❌ FIX 3 FAILED: {error}")
            else:
                print(f"  ❌ ERROR: {error}")

        print()

    # Summary
    print("\n=== SUMMARY ===")
    if not issues_found:
        print("✓ All fixes verified successfully!")
    else:
        print(f"❌ Found {len(issues_found)} issue(s):")
        for issue in issues_found:
            print(f"  - {issue}")

    return len(issues_found) == 0


if __name__ == "__main__":
    success = test_fixes()
    sys.exit(0 if success else 1)
