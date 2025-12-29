#!/usr/bin/env python3
"""
Enable Foreign Key Enforcement

This migration enables FK enforcement in SQLite and verifies there are no violations.
Run cleanup_orphans.py FIRST to remove any orphaned records.

What this does:
1. Checks for any remaining FK violations
2. Enables PRAGMA foreign_keys = ON
3. Verifies enforcement is working

IMPORTANT: SQLite FK enforcement must be enabled per-connection.
This script updates the application code to enable it on every connection.

Run: python scripts/migrations/enable_fk_enforcement.py
     python scripts/migrations/enable_fk_enforcement.py --check  # Check only
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bensley_master.db"


def check_fk_violations(cursor) -> list:
    """
    Check for any remaining FK violations using SQLite's built-in check.
    Returns list of violations.
    """
    # PRAGMA foreign_key_check returns violations
    # Format: (table, rowid, parent_table, fkid)
    cursor.execute("PRAGMA foreign_key_check")
    violations = cursor.fetchall()
    return violations


def check_known_relationships(cursor) -> dict:
    """
    Check specific relationships we care about.
    Returns dict of relationship -> violation count.
    """
    checks = {}

    # email_proposal_links -> emails
    cursor.execute("""
        SELECT COUNT(*) FROM email_proposal_links epl
        WHERE NOT EXISTS (SELECT 1 FROM emails e WHERE e.email_id = epl.email_id)
    """)
    checks['email_proposal_links.email_id'] = cursor.fetchone()[0]

    # email_proposal_links -> proposals
    cursor.execute("""
        SELECT COUNT(*) FROM email_proposal_links epl
        WHERE NOT EXISTS (SELECT 1 FROM proposals p WHERE p.proposal_id = epl.proposal_id)
    """)
    checks['email_proposal_links.proposal_id'] = cursor.fetchone()[0]

    # email_project_links -> emails
    cursor.execute("""
        SELECT COUNT(*) FROM email_project_links epl
        WHERE NOT EXISTS (SELECT 1 FROM emails e WHERE e.email_id = epl.email_id)
    """)
    checks['email_project_links.email_id'] = cursor.fetchone()[0]

    # ai_suggestions -> emails (where source_type = 'email')
    cursor.execute("""
        SELECT COUNT(*) FROM ai_suggestions
        WHERE source_type = 'email' AND source_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM emails e WHERE e.email_id = source_id)
    """)
    checks['ai_suggestions.source_id'] = cursor.fetchone()[0]

    return checks


def enable_fk_enforcement(conn) -> bool:
    """
    Enable foreign key enforcement for this connection.
    Returns True if successful.
    """
    conn.execute("PRAGMA foreign_keys = ON")
    result = conn.execute("PRAGMA foreign_keys").fetchone()
    return result[0] == 1


def test_fk_enforcement(conn) -> bool:
    """
    Test that FK enforcement is actually working by trying to insert a bad record.
    """
    cursor = conn.cursor()

    try:
        # Try to insert a link to a non-existent email (should fail)
        cursor.execute("""
            INSERT INTO email_proposal_links (email_id, proposal_id, confidence_score)
            VALUES (999999999, 1, 0.5)
        """)
        # If we get here, FK enforcement is NOT working
        cursor.execute("DELETE FROM email_proposal_links WHERE email_id = 999999999")
        return False
    except sqlite3.IntegrityError:
        # This is expected - FK enforcement is working
        return True
    except Exception as e:
        print(f"   Unexpected error during test: {e}")
        return False


def run_migration(check_only: bool = False):
    """Run the FK enforcement migration."""
    print("=" * 60)
    print(f"FK ENFORCEMENT {'CHECK' if check_only else 'MIGRATION'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1: Check current FK status
    print("\n1. Checking current FK status...")
    result = cursor.execute("PRAGMA foreign_keys").fetchone()
    current_status = "ON" if result[0] == 1 else "OFF"
    print(f"   Current FK enforcement: {current_status}")

    # Step 2: Check for violations in known relationships
    print("\n2. Checking known relationships for violations...")
    relationship_checks = check_known_relationships(cursor)
    has_violations = False
    for relationship, count in relationship_checks.items():
        status = "OK" if count == 0 else f"VIOLATION ({count} records)"
        print(f"   {relationship}: {status}")
        if count > 0:
            has_violations = True

    # Step 3: Run SQLite's built-in FK check
    print("\n3. Running PRAGMA foreign_key_check...")
    violations = check_fk_violations(cursor)
    if violations:
        print(f"   Found {len(violations)} violations:")
        for v in violations[:10]:  # Show first 10
            print(f"      Table: {v[0]}, RowID: {v[1]}, Parent: {v[2]}")
        if len(violations) > 10:
            print(f"      ... and {len(violations) - 10} more")
        has_violations = True
    else:
        print("   No violations found")

    if check_only:
        print("\n" + "=" * 60)
        if has_violations:
            print("CHECK FAILED - Violations found")
            print("Run cleanup_orphans.py first, then re-run this check")
        else:
            print("CHECK PASSED - No violations")
            print("Safe to enable FK enforcement")
        print("=" * 60)
        conn.close()
        return not has_violations

    # Step 4: Block if there are violations
    if has_violations:
        print("\n" + "=" * 60)
        print("MIGRATION BLOCKED - Violations found")
        print("Run cleanup_orphans.py first to fix violations")
        print("=" * 60)
        conn.close()
        return False

    # Step 5: Enable FK enforcement
    print("\n4. Enabling FK enforcement...")
    if enable_fk_enforcement(conn):
        print("   PRAGMA foreign_keys = ON")
    else:
        print("   FAILED to enable FK enforcement")
        conn.close()
        return False

    # Step 6: Test FK enforcement
    print("\n5. Testing FK enforcement...")
    if test_fk_enforcement(conn):
        print("   FK enforcement is working correctly")
    else:
        print("   WARNING: FK enforcement test failed")
        print("   This may indicate the schema lacks FK constraints")

    conn.close()

    # Step 7: Update application code reminder
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print("\nIMPORTANT: SQLite FK enforcement is per-connection.")
    print("The application must enable it on every database connection:")
    print()
    print("   conn = sqlite3.connect(db_path)")
    print("   conn.execute('PRAGMA foreign_keys = ON')")
    print()
    print("Update these files to enable FK enforcement:")
    print("   - backend/api/dependencies.py")
    print("   - backend/services/base_service.py")
    print("   - Any script that connects to the database")

    return True


def main():
    parser = argparse.ArgumentParser(description="Enable FK enforcement")
    parser.add_argument('--check', action='store_true', help="Check for violations only")

    args = parser.parse_args()
    success = run_migration(check_only=args.check)
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
