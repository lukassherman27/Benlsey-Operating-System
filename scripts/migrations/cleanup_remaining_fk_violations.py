#!/usr/bin/env python3
"""
Clean Up Remaining FK Violations

After removing FK constraints from archive tables, there are still some
orphaned records in other tables. This script cleans them up.

Run: python scripts/migrations/cleanup_remaining_fk_violations.py
     python scripts/migrations/cleanup_remaining_fk_violations.py --dry-run
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bensley_master.db"


def cleanup_orphans(cursor, dry_run: bool) -> int:
    """Clean up orphaned records in various tables."""
    total = 0

    # 1. project_milestones -> projects
    cursor.execute("""
        SELECT COUNT(*) FROM project_milestones pm
        WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = pm.project_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n1. Orphaned project_milestones: {count}")
        if not dry_run:
            cursor.execute("""
                DELETE FROM project_milestones
                WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = project_milestones.project_id)
            """)
            print(f"   Deleted {count} records")
        else:
            print(f"   Would delete {count} records")
        total += count

    # 2. proposals_audit_log -> proposals
    cursor.execute("""
        SELECT COUNT(*) FROM proposals_audit_log pal
        WHERE NOT EXISTS (SELECT 1 FROM proposals p WHERE p.proposal_id = pal.proposal_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n2. Orphaned proposals_audit_log: {count}")
        if not dry_run:
            cursor.execute("""
                DELETE FROM proposals_audit_log
                WHERE NOT EXISTS (SELECT 1 FROM proposals p WHERE p.proposal_id = proposals_audit_log.proposal_id)
            """)
            print(f"   Deleted {count} records")
        else:
            print(f"   Would delete {count} records")
        total += count

    # 3. action_items_tracking -> projects
    cursor.execute("""
        SELECT COUNT(*) FROM action_items_tracking ait
        WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = ait.project_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n3. Orphaned action_items_tracking: {count}")
        if not dry_run:
            cursor.execute("""
                DELETE FROM action_items_tracking
                WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = action_items_tracking.project_id)
            """)
            print(f"   Deleted {count} records")
        else:
            print(f"   Would delete {count} records")
        total += count

    # 4. project_status_tracking -> projects
    cursor.execute("""
        SELECT COUNT(*) FROM project_status_tracking pst
        WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = pst.project_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n4. Orphaned project_status_tracking: {count}")
        if not dry_run:
            cursor.execute("""
                DELETE FROM project_status_tracking
                WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = project_status_tracking.project_id)
            """)
            print(f"   Deleted {count} records")
        else:
            print(f"   Would delete {count} records")
        total += count

    # 5. proposal_status_history -> proposals
    cursor.execute("""
        SELECT COUNT(*) FROM proposal_status_history psh
        WHERE NOT EXISTS (SELECT 1 FROM proposals p WHERE p.proposal_id = psh.proposal_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n5. Orphaned proposal_status_history: {count}")
        if not dry_run:
            cursor.execute("""
                DELETE FROM proposal_status_history
                WHERE NOT EXISTS (SELECT 1 FROM proposals p WHERE p.proposal_id = proposal_status_history.proposal_id)
            """)
            print(f"   Deleted {count} records")
        else:
            print(f"   Would delete {count} records")
        total += count

    # 6. deliverables -> projects
    cursor.execute("""
        SELECT COUNT(*) FROM deliverables d
        WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = d.project_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n6. Orphaned deliverables: {count}")
        if not dry_run:
            cursor.execute("""
                DELETE FROM deliverables
                WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = deliverables.project_id)
            """)
            print(f"   Deleted {count} records")
        else:
            print(f"   Would delete {count} records")
        total += count

    # 7. contract_phases -> projects
    cursor.execute("""
        SELECT COUNT(*) FROM contract_phases cp
        WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = cp.project_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n7. Orphaned contract_phases: {count}")
        if not dry_run:
            cursor.execute("""
                DELETE FROM contract_phases
                WHERE NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = contract_phases.project_id)
            """)
            print(f"   Deleted {count} records")
        else:
            print(f"   Would delete {count} records")
        total += count

    # 8. training_feedback -> ai_suggestions
    cursor.execute("""
        SELECT COUNT(*) FROM training_feedback tf
        WHERE NOT EXISTS (SELECT 1 FROM ai_suggestions s WHERE s.suggestion_id = tf.suggestion_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n8. Orphaned training_feedback: {count}")
        if not dry_run:
            cursor.execute("""
                DELETE FROM training_feedback
                WHERE NOT EXISTS (SELECT 1 FROM ai_suggestions s WHERE s.suggestion_id = training_feedback.suggestion_id)
            """)
            print(f"   Deleted {count} records")
        else:
            print(f"   Would delete {count} records")
        total += count

    # 9. document_intelligence -> documents
    cursor.execute("""
        SELECT COUNT(*) FROM document_intelligence di
        WHERE NOT EXISTS (SELECT 1 FROM documents d WHERE d.document_id = di.document_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n9. Orphaned document_intelligence: {count}")
        if not dry_run:
            cursor.execute("""
                DELETE FROM document_intelligence
                WHERE NOT EXISTS (SELECT 1 FROM documents d WHERE d.document_id = document_intelligence.document_id)
            """)
            print(f"   Deleted {count} records")
        else:
            print(f"   Would delete {count} records")
        total += count

    # 10. suggestion_changes -> ai_suggestions
    cursor.execute("""
        SELECT COUNT(*) FROM suggestion_changes sc
        WHERE NOT EXISTS (SELECT 1 FROM ai_suggestions s WHERE s.suggestion_id = sc.suggestion_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n10. Orphaned suggestion_changes: {count}")
        if not dry_run:
            cursor.execute("""
                DELETE FROM suggestion_changes
                WHERE NOT EXISTS (SELECT 1 FROM ai_suggestions s WHERE s.suggestion_id = suggestion_changes.suggestion_id)
            """)
            print(f"   Deleted {count} records")
        else:
            print(f"   Would delete {count} records")
        total += count

    # Also check meeting_transcripts -> projects (from earlier fix)
    cursor.execute("""
        SELECT COUNT(*) FROM meeting_transcripts mt
        WHERE detected_project_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = mt.detected_project_id)
    """)
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"\n11. Orphaned meeting_transcripts (detected_project_id): {count}")
        if not dry_run:
            cursor.execute("""
                UPDATE meeting_transcripts
                SET detected_project_id = NULL
                WHERE detected_project_id IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM projects p WHERE p.project_id = meeting_transcripts.detected_project_id)
            """)
            print(f"   Cleared {count} references")
        else:
            print(f"   Would clear {count} references")
        total += count

    return total


def run_migration(dry_run: bool = False):
    print("=" * 60)
    print(f"CLEANUP REMAINING FK VIOLATIONS - {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        total = cleanup_orphans(cursor, dry_run)

        if not dry_run:
            conn.commit()

        # Check remaining violations
        print("\n" + "=" * 60)
        print("Checking remaining violations...")
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()
        print(f"Remaining violations: {len(violations)}")

        if violations:
            tables = {}
            for v in violations:
                tables[v[0]] = tables.get(v[0], 0) + 1
            print("\nBy table:")
            for table, count in sorted(tables.items(), key=lambda x: -x[1])[:10]:
                print(f"  {table}: {count}")

        print("\n" + "=" * 60)
        if dry_run:
            print(f"DRY RUN COMPLETE - Would clean {total} records")
        else:
            print(f"CLEANUP COMPLETE - Cleaned {total} records")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Clean up remaining FK violations")
    parser.add_argument('--dry-run', action='store_true', help="Preview changes without applying")
    args = parser.parse_args()
    run_migration(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
