#!/usr/bin/env python3
"""
Review and approve/deny data validation suggestions
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "database" / "bensley_master.db"

def review_suggestions():
    """Interactive review of pending suggestions"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.suggestion_id,
            s.project_code,
            s.field_name,
            s.current_value,
            s.suggested_value,
            s.confidence_score,
            s.evidence_snippet,
            s.reasoning,
            e.subject,
            e.sender_email,
            e.date
        FROM data_validation_suggestions s
        INNER JOIN emails e ON s.evidence_id = e.email_id
        WHERE s.status = 'pending'
        ORDER BY s.confidence_score DESC, s.created_at DESC
    """)

    suggestions = cursor.fetchall()

    if not suggestions:
        print("✅ No pending suggestions!")
        return

    print(f"\n📋 {len(suggestions)} Pending Suggestions\n")
    print("=" * 80)

    for i, sugg in enumerate(suggestions, 1):
        print(f"\n[{i}/{len(suggestions)}] Suggestion ID: {sugg['suggestion_id']}")
        print(f"Project: {sugg['project_code']}")
        print(f"Field: {sugg['field_name']}")
        print(f"Current DB value: {sugg['current_value']}")
        print(f"Suggested value: {sugg['suggested_value']}")
        print(f"Confidence: {sugg['confidence_score']:.0%}")
        print(f"\nEvidence from email:")
        print(f"  From: {sugg['sender_email']}")
        print(f"  Date: {sugg['date']}")
        print(f"  Subject: {sugg['subject']}")
        print(f"  Quote: \"{sugg['evidence_snippet'][:150]}...\"")
        print(f"\nReasoning: {sugg['reasoning']}")
        print("-" * 80)

        while True:
            choice = input("\n[A]pprove / [D]eny / [S]kip / [Q]uit? ").strip().lower()

            if choice == 'q':
                print("\nExiting...")
                return

            if choice == 's':
                break

            if choice in ['a', 'd']:
                action = 'approved' if choice == 'a' else 'denied'
                notes = input(f"Notes (optional, press Enter to skip): ").strip()

                cursor.execute("""
                    UPDATE data_validation_suggestions
                    SET status = ?, reviewed_by = 'manual', reviewed_at = datetime('now'), review_notes = ?
                    WHERE suggestion_id = ?
                """, (action, notes or None, sugg['suggestion_id']))

                conn.commit()
                print(f"✅ Marked as {action}")
                break

            print("Invalid choice. Please enter A, D, S, or Q.")

    conn.close()
    print("\n✅ Review complete!")


def show_stats():
    """Show suggestion statistics"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            status,
            COUNT(*) as count
        FROM data_validation_suggestions
        GROUP BY status
    """)

    print("\n📊 Suggestion Statistics:")
    for row in cursor.fetchall():
        print(f"  {row['status']}: {row['count']}")

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        show_stats()
    else:
        review_suggestions()
