#!/usr/bin/env python3
"""
Review Enrichment Suggestions CLI

Interactive CLI to review email_link_batch and learn_pattern suggestions
created by the enrich-proposals agent.

Usage:
    python scripts/core/review_enrichment_suggestions.py
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "database" / "bensley_master.db"


def get_pending_suggestions(conn):
    """Get all pending enrichment suggestions."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            suggestion_id,
            suggestion_type,
            entity_type,
            entity_id,
            description,
            suggested_value,
            confidence_score,
            reasoning
        FROM ai_suggestions
        WHERE status = 'pending'
        AND suggestion_type IN ('email_link_batch', 'learn_pattern')
        ORDER BY confidence_score DESC, created_at
    """)
    return cursor.fetchall()


def get_proposal_info(conn, proposal_id):
    """Get proposal details."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_code, project_name, status, contact_person, contact_email
        FROM proposals WHERE proposal_id = ?
    """, (proposal_id,))
    return cursor.fetchone()


def get_email_samples(conn, email_ids):
    """Get sample emails for preview."""
    if not email_ids:
        return []
    placeholders = ','.join(['?' for _ in email_ids[:5]])
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT email_id, sender_email, subject, date
        FROM emails
        WHERE email_id IN ({placeholders})
        ORDER BY date DESC
    """, email_ids[:5])
    return cursor.fetchall()


def apply_email_links(conn, proposal_id, email_ids, match_method="enrichment_agent"):
    """Create email_proposal_links for approved emails."""
    cursor = conn.cursor()
    linked = 0
    for email_id in email_ids:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO email_proposal_links
                (email_id, proposal_id, confidence_score, match_method, match_reason)
                VALUES (?, ?, 0.95, ?, 'Approved via enrichment review')
            """, (email_id, proposal_id, match_method))
            if cursor.rowcount > 0:
                linked += 1
        except Exception as e:
            print(f"  Error linking email {email_id}: {e}")
    conn.commit()
    return linked


def create_learned_pattern(conn, pattern_data):
    """Create a learned pattern from approved suggestion."""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO email_learned_patterns
            (pattern_type, pattern_key, target_type, target_code, target_name, confidence, times_used, created_at)
            VALUES (?, ?, 'proposal', ?, ?, 0.85, 0, datetime('now'))
        """, (
            pattern_data.get('pattern_type', 'domain_to_proposal'),
            pattern_data.get('pattern_key'),
            pattern_data.get('target_code'),
            pattern_data.get('target_name')
        ))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"  Error creating pattern: {e}")
        return False


def update_suggestion_status(conn, suggestion_id, status, notes=None):
    """Update suggestion status."""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE ai_suggestions
        SET status = ?,
            processed_at = datetime('now'),
            review_notes = COALESCE(?, review_notes)
        WHERE suggestion_id = ?
    """, (status, notes, suggestion_id))
    conn.commit()


def display_suggestion(suggestion, proposal_info, email_samples):
    """Display a suggestion for review."""
    print("\n" + "="*70)
    print(f"SUGGESTION #{suggestion[0]} ({suggestion[1]})")
    print("="*70)

    if proposal_info:
        print(f"\nProposal: {proposal_info[0]} ({proposal_info[1]})")
        print(f"Status: {proposal_info[2]}")
        print(f"Contact: {proposal_info[3] or 'N/A'} ({proposal_info[4] or 'N/A'})")

    print(f"\nDescription: {suggestion[4]}")
    print(f"Confidence: {suggestion[6]:.0%}")

    if suggestion[7]:
        print(f"\nReasoning: {suggestion[7]}")

    if email_samples:
        print(f"\nSample Emails ({len(email_samples)} shown):")
        for email in email_samples:
            date_str = email[3][:10] if email[3] else "N/A"
            print(f"  • [{date_str}] {email[1][:40]}")
            print(f"    {email[2][:60]}...")

    print()


def main():
    print("\n" + "="*70)
    print("  PROPOSAL ENRICHMENT REVIEW")
    print("="*70)

    conn = sqlite3.connect(DB_PATH)
    suggestions = get_pending_suggestions(conn)

    if not suggestions:
        print("\n✓ No pending enrichment suggestions to review!")
        conn.close()
        return

    print(f"\nFound {len(suggestions)} pending suggestions\n")

    # Group by type
    email_batches = [s for s in suggestions if s[1] == 'email_link_batch']
    pattern_suggestions = [s for s in suggestions if s[1] == 'learn_pattern']

    print(f"  • Email link batches: {len(email_batches)}")
    print(f"  • Pattern suggestions: {len(pattern_suggestions)}")

    # Process email batches first
    approved_count = 0
    rejected_count = 0

    for i, suggestion in enumerate(email_batches):
        suggestion_id = suggestion[0]
        proposal_id = suggestion[3]

        # Parse email IDs from suggested_value
        try:
            email_ids = json.loads(suggestion[5]) if suggestion[5] else []
        except:
            email_ids = []

        proposal_info = get_proposal_info(conn, proposal_id) if proposal_id else None
        email_samples = get_email_samples(conn, email_ids)

        display_suggestion(suggestion, proposal_info, email_samples)

        print(f"[{i+1}/{len(email_batches)}] (A)pprove, (R)eject, (S)kip, (Q)uit: ", end="")
        choice = input().strip().lower()

        if choice == 'a':
            linked = apply_email_links(conn, proposal_id, email_ids)
            update_suggestion_status(conn, suggestion_id, 'approved')
            print(f"  ✓ Approved! Linked {linked} emails.")
            approved_count += 1
        elif choice == 'r':
            update_suggestion_status(conn, suggestion_id, 'rejected')
            print(f"  ✗ Rejected.")
            rejected_count += 1
        elif choice == 'q':
            print("\nExiting...")
            break
        else:
            print(f"  → Skipped.")

    # Process pattern suggestions
    for i, suggestion in enumerate(pattern_suggestions):
        suggestion_id = suggestion[0]

        try:
            pattern_data = json.loads(suggestion[5]) if suggestion[5] else {}
        except:
            pattern_data = {}

        display_suggestion(suggestion, None, None)

        print(f"[{i+1}/{len(pattern_suggestions)}] (A)pprove pattern, (R)eject, (S)kip, (Q)uit: ", end="")
        choice = input().strip().lower()

        if choice == 'a':
            if create_learned_pattern(conn, pattern_data):
                update_suggestion_status(conn, suggestion_id, 'approved')
                print(f"  ✓ Pattern learned!")
                approved_count += 1
            else:
                print(f"  ⚠ Pattern already exists or error.")
        elif choice == 'r':
            update_suggestion_status(conn, suggestion_id, 'rejected')
            print(f"  ✗ Rejected.")
            rejected_count += 1
        elif choice == 'q':
            print("\nExiting...")
            break
        else:
            print(f"  → Skipped.")

    conn.close()

    print("\n" + "="*70)
    print(f"  REVIEW COMPLETE")
    print(f"  Approved: {approved_count}")
    print(f"  Rejected: {rejected_count}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
