#!/usr/bin/env python3
"""
Cleanup Duplicate Email Link Suggestions (#316)

Finds and removes duplicate link suggestions (link_review + email_link)
for the same email+project combination.

Keeps the suggestion with the HIGHEST confidence score.

Usage:
    python scripts/core/cleanup_duplicate_suggestions.py --dry-run
    python scripts/core/cleanup_duplicate_suggestions.py --apply
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = project_root / "database" / "bensley_master.db"


def find_duplicates(conn) -> list:
    """
    Find duplicate link suggestions (same email + project).

    Returns list of (email_id, project_code, suggestion_ids, keep_id)
    """
    cursor = conn.cursor()

    # Find emails+projects with multiple link suggestions
    cursor.execute("""
        SELECT
            source_id as email_id,
            project_code,
            GROUP_CONCAT(suggestion_id) as suggestion_ids,
            COUNT(*) as count
        FROM ai_suggestions
        WHERE source_type = 'email'
        AND suggestion_type IN ('link_review', 'email_link')
        AND status = 'pending'
        AND project_code IS NOT NULL
        GROUP BY source_id, project_code
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """)

    duplicates = []
    for row in cursor.fetchall():
        email_id, project_code, suggestion_ids_str, count = row
        suggestion_ids = [int(x) for x in suggestion_ids_str.split(',')]

        # Find the one with highest confidence
        cursor.execute("""
            SELECT suggestion_id, suggestion_type, confidence_score
            FROM ai_suggestions
            WHERE suggestion_id IN ({})
            ORDER BY confidence_score DESC
            LIMIT 1
        """.format(','.join('?' * len(suggestion_ids))), suggestion_ids)

        best = cursor.fetchone()
        keep_id = best[0] if best else suggestion_ids[0]

        duplicates.append({
            'email_id': email_id,
            'project_code': project_code,
            'suggestion_ids': suggestion_ids,
            'keep_id': keep_id,
            'count': count,
        })

    return duplicates


def cleanup_duplicates(conn, duplicates: list, dry_run: bool = True) -> dict:
    """
    Remove duplicate suggestions, keeping the highest confidence one.

    Returns stats dict.
    """
    cursor = conn.cursor()
    stats = {
        'groups_found': len(duplicates),
        'duplicates_removed': 0,
        'suggestions_kept': 0,
    }

    for dup in duplicates:
        # IDs to delete (all except the one we're keeping)
        delete_ids = [sid for sid in dup['suggestion_ids'] if sid != dup['keep_id']]

        if dry_run:
            print(f"  Would delete {len(delete_ids)} duplicates for email {dup['email_id']} → {dup['project_code']}")
            print(f"    Keep: suggestion #{dup['keep_id']}")
            print(f"    Delete: {delete_ids}")
        else:
            if delete_ids:
                cursor.execute("""
                    DELETE FROM ai_suggestions
                    WHERE suggestion_id IN ({})
                """.format(','.join('?' * len(delete_ids))), delete_ids)
                print(f"  Deleted {len(delete_ids)} duplicates for email {dup['email_id']} → {dup['project_code']}")

        stats['duplicates_removed'] += len(delete_ids)
        stats['suggestions_kept'] += 1

    if not dry_run:
        conn.commit()

    return stats


def main():
    parser = argparse.ArgumentParser(description='Cleanup duplicate email link suggestions')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without making changes')
    parser.add_argument('--apply', action='store_true', help='Actually delete the duplicates')
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Error: Must specify --dry-run or --apply")
        sys.exit(1)

    dry_run = args.dry_run

    print(f"{'DRY RUN - ' if dry_run else ''}Cleanup Duplicate Suggestions")
    print("=" * 50)

    conn = sqlite3.connect(DB_PATH)

    try:
        duplicates = find_duplicates(conn)

        if not duplicates:
            print("\nNo duplicate link suggestions found!")
            return

        print(f"\nFound {len(duplicates)} email+project combinations with duplicate suggestions:\n")

        stats = cleanup_duplicates(conn, duplicates, dry_run=dry_run)

        print("\n" + "=" * 50)
        print("Summary:")
        print(f"  Groups with duplicates: {stats['groups_found']}")
        print(f"  Suggestions to keep: {stats['suggestions_kept']}")
        print(f"  Duplicates {'would be' if dry_run else ''} removed: {stats['duplicates_removed']}")

        if dry_run:
            print("\nRun with --apply to actually delete duplicates.")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
