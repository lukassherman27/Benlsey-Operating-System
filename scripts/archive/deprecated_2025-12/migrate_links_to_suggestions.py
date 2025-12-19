"""
Migrate Links to Suggestions

DISABLED: 2025-12-02 - No longer needed. All needs_review links were deleted
because they were created by flawed auto-linking logic.

Converts all email links flagged with needs_review=1 into link_review suggestions
so they can be reviewed in the UI.

This is a one-time migration script that should be run after migration 060.

Usage:
    python scripts/core/migrate_links_to_suggestions.py [--dry-run]
"""

import sys
print("=" * 70)
print("This migration script is no longer needed.")
print("All needs_review links were deleted on 2025-12-02.")
print("=" * 70)
sys.exit(0)

import sqlite3
import json
import os
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Default database path
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')


def get_connection(db_path: str = DB_PATH):
    """Get database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_project_links_for_review(conn) -> List[Dict[str, Any]]:
    """Get all project links flagged for review."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            epl.email_id,
            epl.project_id,
            epl.project_code,
            epl.link_method,
            epl.confidence,
            epl.evidence,
            e.subject as email_subject,
            e.sender_email,
            e.date as email_date,
            p.project_title as project_name
        FROM email_project_links epl
        JOIN emails e ON epl.email_id = e.email_id
        LEFT JOIN projects p ON epl.project_id = p.project_id
        WHERE epl.needs_review = 1
    """)
    return [dict(row) for row in cursor.fetchall()]


def get_proposal_links_for_review(conn) -> List[Dict[str, Any]]:
    """Get all proposal links flagged for review."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            epl.email_id,
            epl.proposal_id,
            epl.match_method,
            epl.confidence_score,
            epl.match_reason,
            e.subject as email_subject,
            e.sender_email,
            e.date as email_date,
            pr.project_code,
            pr.project_name
        FROM email_proposal_links epl
        JOIN emails e ON epl.email_id = e.email_id
        LEFT JOIN proposals pr ON epl.proposal_id = pr.proposal_id
        WHERE epl.needs_review = 1
    """)
    return [dict(row) for row in cursor.fetchall()]


def check_existing_suggestion(conn, email_id: int, target_type: str, target_id: int) -> bool:
    """Check if a suggestion already exists for this link."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT suggestion_id FROM ai_suggestions
        WHERE suggestion_type = 'link_review'
        AND suggested_data LIKE ?
        AND status = 'pending'
    """, (f'%"email_id": {email_id}%',))
    return cursor.fetchone() is not None


def create_suggestion(
    conn,
    link_type: str,
    email_id: int,
    target_id: int,
    project_code: str,
    link_method: str,
    confidence: float,
    email_subject: str,
    sender_email: str,
    evidence: str = None
) -> int:
    """Create a link_review suggestion for a flagged link."""
    cursor = conn.cursor()

    # Build suggested_data
    suggested_data = {
        "link_type": link_type,
        "email_id": email_id,
        "project_code": project_code,
        "link_method": link_method,
        "confidence": confidence,
        "email_subject": email_subject,
        "sender_email": sender_email
    }

    if link_type == "project":
        suggested_data["project_id"] = target_id
    else:
        suggested_data["proposal_id"] = target_id

    if evidence:
        suggested_data["evidence"] = evidence

    # Truncate subject for title
    subject_short = email_subject[:50] + "..." if email_subject and len(email_subject) > 50 else email_subject

    title = f"Review link: {subject_short or 'No subject'}"
    description = f"Auto-linked email to {project_code or f'{link_type} #{target_id}'} via {link_method} (confidence: {confidence:.0%})"

    cursor.execute("""
        INSERT INTO ai_suggestions (
            suggestion_type,
            priority,
            confidence_score,
            source_type,
            source_id,
            title,
            description,
            suggested_action,
            suggested_data,
            target_table,
            target_id,
            project_code,
            proposal_id,
            status,
            is_actionable,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "link_review",
        "medium",
        confidence or 0.5,
        "email",
        email_id,
        title,
        description,
        f"Review and approve/reject this {link_type} link",
        json.dumps(suggested_data),
        f"email_{link_type}_links",
        email_id,
        project_code,
        target_id if link_type == "proposal" else None,
        "pending",
        1,
        datetime.now().isoformat()
    ))

    return cursor.lastrowid


def migrate_links(db_path: str = DB_PATH, dry_run: bool = False) -> Dict[str, int]:
    """
    Migrate all flagged links to suggestions.

    Returns stats about the migration.
    """
    conn = get_connection(db_path)
    stats = {
        "project_links_found": 0,
        "proposal_links_found": 0,
        "suggestions_created": 0,
        "already_exists": 0,
        "errors": 0
    }

    try:
        # Process project links
        project_links = get_project_links_for_review(conn)
        stats["project_links_found"] = len(project_links)

        print(f"Found {len(project_links)} project links to migrate...")

        for link in project_links:
            try:
                # Skip if suggestion already exists
                if check_existing_suggestion(conn, link["email_id"], "project", link["project_id"]):
                    stats["already_exists"] += 1
                    continue

                if not dry_run:
                    create_suggestion(
                        conn=conn,
                        link_type="project",
                        email_id=link["email_id"],
                        target_id=link["project_id"],
                        project_code=link["project_code"] or link.get("project_name"),
                        link_method=link["link_method"],
                        confidence=link["confidence"] or 0.5,
                        email_subject=link["email_subject"],
                        sender_email=link["sender_email"],
                        evidence=link["evidence"]
                    )
                stats["suggestions_created"] += 1

            except Exception as e:
                print(f"Error creating suggestion for project link {link['email_id']}->{link['project_id']}: {e}")
                stats["errors"] += 1

        # Process proposal links
        proposal_links = get_proposal_links_for_review(conn)
        stats["proposal_links_found"] = len(proposal_links)

        print(f"Found {len(proposal_links)} proposal links to migrate...")

        for link in proposal_links:
            try:
                # Skip if suggestion already exists
                if check_existing_suggestion(conn, link["email_id"], "proposal", link["proposal_id"]):
                    stats["already_exists"] += 1
                    continue

                if not dry_run:
                    create_suggestion(
                        conn=conn,
                        link_type="proposal",
                        email_id=link["email_id"],
                        target_id=link["proposal_id"],
                        project_code=link["project_code"] or link.get("project_name"),
                        link_method=link["match_method"],
                        confidence=link["confidence_score"] or 0.5,
                        email_subject=link["email_subject"],
                        sender_email=link["sender_email"],
                        evidence=link["match_reason"]
                    )
                stats["suggestions_created"] += 1

            except Exception as e:
                print(f"Error creating suggestion for proposal link {link['email_id']}->{link['proposal_id']}: {e}")
                stats["errors"] += 1

        if not dry_run:
            conn.commit()

    finally:
        conn.close()

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Migrate flagged email links to reviewable suggestions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--db-path",
        default=DB_PATH,
        help=f"Path to database (default: {DB_PATH})"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Email Link Migration to Suggestions")
    print("=" * 60)

    if args.dry_run:
        print("DRY RUN - No changes will be made\n")

    stats = migrate_links(args.db_path, args.dry_run)

    print("\n" + "=" * 60)
    print("Migration Results:")
    print("=" * 60)
    print(f"  Project links found:     {stats['project_links_found']}")
    print(f"  Proposal links found:    {stats['proposal_links_found']}")
    print(f"  Suggestions created:     {stats['suggestions_created']}")
    print(f"  Already existed:         {stats['already_exists']}")
    print(f"  Errors:                  {stats['errors']}")
    print("=" * 60)

    if args.dry_run:
        print("\nRun without --dry-run to execute the migration.")


if __name__ == "__main__":
    main()
