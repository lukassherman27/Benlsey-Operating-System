#!/usr/bin/env python3
"""
Test Email Classification and Multi-Link Support

Tests the context-aware suggestion system on 10 sample emails
to verify email classification and multi-project linking work correctly.
"""

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.context_aware_suggestion_service import get_context_aware_service


def test_email_classification():
    """Test on 10 diverse sample emails"""

    service = get_context_aware_service()

    # Get 10 recent unclassified emails
    emails = service.execute_query("""
        SELECT email_id, subject, sender_email, folder
        FROM emails
        WHERE email_type IS NULL
        ORDER BY date DESC
        LIMIT 10
    """)

    if not emails:
        print("No unclassified emails found")
        return

    print(f"\n=== Testing on {len(emails)} emails ===\n")

    results = []
    for email in emails:
        print(f"Processing: {email['email_id']} - {email['subject'][:60]}...")
        result = service.generate_suggestions_for_email(email['email_id'])

        if result.get('success'):
            # Check the classification
            classified = service.execute_query("""
                SELECT email_type, is_project_related, classification_confidence,
                       classification_reasoning
                FROM emails WHERE email_id = ?
            """, (email['email_id'],), fetch_one=True)

            # Check suggestions created
            suggestions = service.execute_query("""
                SELECT suggestion_type, project_code, confidence_score, title
                FROM ai_suggestions
                WHERE source_id = ? AND source_type = 'email'
                ORDER BY created_at DESC
            """, (email['email_id'],))

            result_data = {
                'email_id': email['email_id'],
                'subject': email['subject'][:60],
                'sender': email['sender_email'],
                'email_type': classified.get('email_type') if classified else None,
                'is_project_related': classified.get('is_project_related') if classified else None,
                'confidence': classified.get('classification_confidence') if classified else None,
                'reasoning': classified.get('classification_reasoning')[:100] if classified and classified.get('classification_reasoning') else None,
                'suggestions_count': len(suggestions) if suggestions else 0,
                'linked_projects': [s['project_code'] for s in suggestions if s.get('project_code')] if suggestions else [],
                'cost': result.get('usage', {}).get('estimated_cost_usd', 0),
            }
            results.append(result_data)

            print(f"  → Type: {result_data['email_type']}")
            print(f"  → Project-related: {result_data['is_project_related']}")
            print(f"  → Suggestions: {result_data['suggestions_count']}")
            if result_data['linked_projects']:
                print(f"  → Linked to: {', '.join(result_data['linked_projects'])}")
            print(f"  → Cost: ${result_data['cost']:.6f}")
            print()
        else:
            print(f"  → FAILED: {result.get('error')}")
            print()

    # Summary
    print("\n=== SUMMARY ===")
    print(f"Emails processed: {len(results)}")

    type_counts = {}
    for r in results:
        t = r.get('email_type', 'unknown')
        type_counts[t] = type_counts.get(t, 0) + 1

    print("\nClassification breakdown:")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")

    project_related = sum(1 for r in results if r.get('is_project_related'))
    print(f"\nProject-related: {project_related}/{len(results)}")

    total_cost = sum(r.get('cost', 0) for r in results)
    print(f"Total cost: ${total_cost:.4f}")

    multi_link = sum(1 for r in results if len(r.get('linked_projects', [])) > 1)
    print(f"Multi-link emails: {multi_link}")

    return results


if __name__ == "__main__":
    test_email_classification()
