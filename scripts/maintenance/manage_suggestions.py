#!/usr/bin/env python3
"""
Manage data validation suggestions
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "database" / "bensley_master.db"


def list_suggestions():
    """List all pending suggestions"""
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
            e.sender_email
        FROM data_validation_suggestions s
        INNER JOIN emails e ON s.evidence_id = e.email_id
        WHERE s.status = 'pending'
        ORDER BY s.suggestion_id
    """)

    suggestions = cursor.fetchall()

    if not suggestions:
        print("✅ No pending suggestions!")
        conn.close()
        return

    print(f"\n📋 {len(suggestions)} Pending Suggestions:\n")

    for sugg in suggestions:
        print(f"ID {sugg['suggestion_id']}: [{sugg['project_code']}] {sugg['field_name']}")
        print(f"  Current: {sugg['current_value']}")
        print(f"  Suggested: {sugg['suggested_value']}")
        print(f"  Confidence: {sugg['confidence_score']:.0%}")
        print(f"  Email: {sugg['subject'][:60]}")
        print(f"  Evidence: \"{sugg['evidence_snippet'][:100]}...\"")
        print(f"  Reasoning: {sugg['reasoning']}")
        print()

    conn.close()


def approve_suggestion(suggestion_id, notes=""):
    """Approve a suggestion"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE data_validation_suggestions
        SET status = 'approved', reviewed_by = 'user', reviewed_at = datetime('now'), review_notes = ?
        WHERE suggestion_id = ?
    """, (notes or None, suggestion_id))

    conn.commit()
    conn.close()
    print(f"✅ Suggestion {suggestion_id} approved")


def deny_suggestion(suggestion_id, notes=""):
    """Deny a suggestion"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE data_validation_suggestions
        SET status = 'denied', reviewed_by = 'user', reviewed_at = datetime('now'), review_notes = ?
        WHERE suggestion_id = ?
    """, (notes or None, suggestion_id))

    conn.commit()
    conn.close()
    print(f"❌ Suggestion {suggestion_id} denied")


def show_stats():
    """Show statistics"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM data_validation_suggestions
        GROUP BY status
    """)

    print("\n📊 Statistics:")
    for row in cursor.fetchall():
        print(f"  {row['status']}: {row['count']}")

    conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 manage_suggestions.py list")
        print("  python3 manage_suggestions.py approve <id> [notes]")
        print("  python3 manage_suggestions.py deny <id> [notes]")
        print("  python3 manage_suggestions.py stats")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_suggestions()
    elif command == "approve":
        suggestion_id = int(sys.argv[2])
        notes = sys.argv[3] if len(sys.argv) > 3 else ""
        approve_suggestion(suggestion_id, notes)
    elif command == "deny":
        suggestion_id = int(sys.argv[2])
        notes = sys.argv[3] if len(sys.argv) > 3 else ""
        deny_suggestion(suggestion_id, notes)
    elif command == "stats":
        show_stats()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
