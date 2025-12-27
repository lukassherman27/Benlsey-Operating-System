#!/usr/bin/env python3
"""
Cleanup Orphaned Records

This script cleans up orphaned records that would block FK enforcement.
Run this BEFORE enable_fk_enforcement.py.

Fixes:
1. Duplicate email_proposal_links - keeps one, deletes extras
2. Empty email_project_links - deletes records with NULL/empty project_code
3. Orphaned ai_suggestions - clears source_id for suggestions pointing to deleted emails

Run: python scripts/migrations/cleanup_orphans.py
     python scripts/migrations/cleanup_orphans.py --dry-run  # Preview only
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bensley_master.db"


def cleanup_duplicate_email_proposal_links(cursor, dry_run: bool) -> int:
    """
    Remove duplicate email_proposal_links, keeping only one per email/proposal pair.
    """
    print("\n1. Cleaning up duplicate email_proposal_links...")

    # Find duplicates
    cursor.execute("""
        SELECT email_id, proposal_id, COUNT(*) as cnt
        FROM email_proposal_links
        GROUP BY email_id, proposal_id
        HAVING COUNT(*) > 1
    """)
    duplicates = cursor.fetchall()

    if not duplicates:
        print("   No duplicates found")
        return 0

    print(f"   Found {len(duplicates)} duplicate pairs")

    deleted = 0
    for email_id, proposal_id, count in duplicates:
        # Get all rowids for this pair
        cursor.execute("""
            SELECT rowid FROM email_proposal_links
            WHERE email_id = ? AND proposal_id = ?
            ORDER BY created_at DESC
        """, (email_id, proposal_id))
        rowids = [row[0] for row in cursor.fetchall()]

        # Keep the first (most recent), delete the rest
        to_delete = rowids[1:]  # All except first
        if to_delete and not dry_run:
            placeholders = ','.join('?' * len(to_delete))
            cursor.execute(f"""
                DELETE FROM email_proposal_links WHERE rowid IN ({placeholders})
            """, to_delete)
            deleted += len(to_delete)
        elif to_delete:
            deleted += len(to_delete)
            print(f"   Would delete {len(to_delete)} duplicates for email {email_id} -> proposal {proposal_id}")

    print(f"   {'Would delete' if dry_run else 'Deleted'}: {deleted} duplicate records")
    return deleted


def cleanup_empty_email_project_links(cursor, dry_run: bool) -> int:
    """
    Remove email_project_links with NULL or empty project_code.
    """
    print("\n2. Cleaning up empty email_project_links...")

    cursor.execute("""
        SELECT COUNT(*) FROM email_project_links
        WHERE project_code IS NULL OR project_code = ''
    """)
    count = cursor.fetchone()[0]

    if count == 0:
        print("   No empty project_codes found")
        return 0

    print(f"   Found {count} records with empty project_code")

    if not dry_run:
        cursor.execute("""
            DELETE FROM email_project_links
            WHERE project_code IS NULL OR project_code = ''
        """)
        print(f"   Deleted: {count} records")
    else:
        print(f"   Would delete: {count} records")

    return count


def cleanup_orphaned_ai_suggestions(cursor, dry_run: bool) -> int:
    """
    Clear source_id for ai_suggestions pointing to deleted emails.
    We don't delete the suggestions, just clear the broken reference.
    """
    print("\n3. Cleaning up orphaned ai_suggestions...")

    cursor.execute("""
        SELECT COUNT(*) FROM ai_suggestions
        WHERE source_type = 'email'
        AND source_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM emails e WHERE e.email_id = source_id)
    """)
    count = cursor.fetchone()[0]

    if count == 0:
        print("   No orphaned suggestions found")
        return 0

    print(f"   Found {count} suggestions with invalid email references")

    if not dry_run:
        cursor.execute("""
            UPDATE ai_suggestions
            SET source_id = NULL
            WHERE source_type = 'email'
            AND source_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM emails e WHERE e.email_id = source_id)
        """)
        print(f"   Cleared source_id for: {count} suggestions")
    else:
        print(f"   Would clear source_id for: {count} suggestions")

    return count


def cleanup_orphaned_email_project_links(cursor, dry_run: bool) -> int:
    """
    Remove email_project_links pointing to non-existent projects.
    """
    print("\n4. Cleaning up orphaned email_project_links (bad project_code)...")

    cursor.execute("""
        SELECT COUNT(*) FROM email_project_links epl
        WHERE project_code IS NOT NULL AND project_code != ''
        AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_code = epl.project_code)
        AND NOT EXISTS (SELECT 1 FROM proposals pr WHERE pr.project_code = epl.project_code)
    """)
    count = cursor.fetchone()[0]

    if count == 0:
        print("   No orphaned project links found")
        return 0

    print(f"   Found {count} links to non-existent projects/proposals")

    if not dry_run:
        cursor.execute("""
            DELETE FROM email_project_links
            WHERE project_code IS NOT NULL AND project_code != ''
            AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_code = project_code)
            AND NOT EXISTS (SELECT 1 FROM proposals pr WHERE pr.project_code = project_code)
        """)
        print(f"   Deleted: {count} records")
    else:
        print(f"   Would delete: {count} records")

    return count


def run_cleanup(dry_run: bool = False):
    """Run all cleanup tasks."""
    print("=" * 60)
    print(f"ORPHAN CLEANUP - {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    total_fixed = 0

    try:
        # Run all cleanup tasks
        total_fixed += cleanup_duplicate_email_proposal_links(cursor, dry_run)
        total_fixed += cleanup_empty_email_project_links(cursor, dry_run)
        total_fixed += cleanup_orphaned_ai_suggestions(cursor, dry_run)
        total_fixed += cleanup_orphaned_email_project_links(cursor, dry_run)

        if not dry_run:
            conn.commit()
            print("\n" + "=" * 60)
            print(f"CLEANUP COMPLETE - Fixed {total_fixed} issues")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print(f"DRY RUN COMPLETE - Would fix {total_fixed} issues")
            print("Run without --dry-run to apply changes")
            print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        conn.close()

    return total_fixed


def main():
    parser = argparse.ArgumentParser(description="Cleanup orphaned database records")
    parser.add_argument('--dry-run', action='store_true', help="Preview changes without applying")

    args = parser.parse_args()
    run_cleanup(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
