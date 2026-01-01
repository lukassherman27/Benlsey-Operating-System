#!/usr/bin/env python3
"""
Data Quality Cleanup Script
Fixes critical data quality issues: #306, #307, #308

Usage:
    python scripts/core/data_quality_cleanup.py --dry-run    # Preview changes (default)
    python scripts/core/data_quality_cleanup.py --execute    # Actually delete records

Issues addressed:
    #306: Orphaned project_team records (168) - project_codes that don't exist
    #307: Duplicate invoices (47 invoice_numbers with triplicates) - $12.7M affected
    #308: Orphaned invoice_aging records (33) - invoice_numbers that don't exist
"""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "database" / "bensley_master.db"


def get_connection():
    """Get database connection with FK enforcement."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def audit_orphaned_project_team(cursor) -> list:
    """Find project_team records with non-existent project_codes."""
    cursor.execute("""
        SELECT pt.id, pt.project_code, pt.contact_id, pt.staff_id, pt.role_custom
        FROM project_team pt
        WHERE pt.project_code NOT IN (SELECT project_code FROM projects)
    """)
    return cursor.fetchall()


def audit_duplicate_invoices(cursor) -> list:
    """Find duplicate invoices (keeping lowest invoice_id for each invoice_number)."""
    cursor.execute("""
        WITH dups AS (
            SELECT invoice_number, MIN(invoice_id) as keep_id
            FROM invoices
            GROUP BY invoice_number
            HAVING COUNT(*) > 1
        )
        SELECT i.invoice_id, i.invoice_number, i.project_id, i.invoice_amount, i.status
        FROM invoices i
        INNER JOIN dups d ON i.invoice_number = d.invoice_number
        WHERE i.invoice_id != d.keep_id
        ORDER BY i.invoice_number, i.invoice_id
    """)
    return cursor.fetchall()


def audit_orphaned_invoice_aging(cursor) -> list:
    """Find invoice_aging records with non-existent invoice_numbers."""
    cursor.execute("""
        SELECT ia.id, ia.invoice_number, ia.project_code, ia.outstanding_amount
        FROM invoice_aging ia
        WHERE ia.invoice_number NOT IN (SELECT invoice_number FROM invoices)
    """)
    return cursor.fetchall()


def fix_orphaned_project_team(cursor, execute: bool) -> int:
    """Delete orphaned project_team records."""
    if execute:
        cursor.execute("""
            DELETE FROM project_team
            WHERE project_code NOT IN (SELECT project_code FROM projects)
        """)
        return cursor.rowcount
    return len(audit_orphaned_project_team(cursor))


def fix_duplicate_invoices(cursor, execute: bool) -> int:
    """Delete duplicate invoices, keeping the one with lowest invoice_id."""
    if execute:
        cursor.execute("""
            WITH dups AS (
                SELECT invoice_number, MIN(invoice_id) as keep_id
                FROM invoices
                GROUP BY invoice_number
                HAVING COUNT(*) > 1
            )
            DELETE FROM invoices
            WHERE invoice_id IN (
                SELECT i.invoice_id
                FROM invoices i
                INNER JOIN dups d ON i.invoice_number = d.invoice_number
                WHERE i.invoice_id != d.keep_id
            )
        """)
        return cursor.rowcount
    return len(audit_duplicate_invoices(cursor))


def fix_orphaned_invoice_aging(cursor, execute: bool) -> int:
    """Delete orphaned invoice_aging records."""
    if execute:
        cursor.execute("""
            DELETE FROM invoice_aging
            WHERE invoice_number NOT IN (SELECT invoice_number FROM invoices)
        """)
        return cursor.rowcount
    return len(audit_orphaned_invoice_aging(cursor))


def main():
    parser = argparse.ArgumentParser(description="Data Quality Cleanup Script")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview changes without modifying database (default)")
    group.add_argument("--execute", action="store_true",
                       help="Actually delete records")
    args = parser.parse_args()

    execute = args.execute
    mode = "EXECUTE" if execute else "DRY RUN"

    print(f"\n{'='*60}")
    print(f"Data Quality Cleanup - {mode}")
    print(f"Database: {DB_PATH}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    conn = get_connection()
    cursor = conn.cursor()

    # Issue #306: Orphaned project_team
    print("Issue #306: Orphaned project_team records")
    print("-" * 40)
    orphaned_team = audit_orphaned_project_team(cursor)
    print(f"  Found: {len(orphaned_team)} orphaned records")
    if orphaned_team and not execute:
        print("  Sample project_codes:")
        unique_codes = set(r['project_code'] for r in orphaned_team[:10])
        for code in list(unique_codes)[:5]:
            count = sum(1 for r in orphaned_team if r['project_code'] == code)
            print(f"    - {code}: {count} team members")

    count_306 = fix_orphaned_project_team(cursor, execute)
    print(f"  {'Deleted' if execute else 'Would delete'}: {count_306} records\n")

    # Issue #307: Duplicate invoices
    print("Issue #307: Duplicate invoices")
    print("-" * 40)
    dup_invoices = audit_duplicate_invoices(cursor)
    print(f"  Found: {len(dup_invoices)} duplicate invoice records")
    if dup_invoices and not execute:
        total_amount = sum(r['invoice_amount'] or 0 for r in dup_invoices)
        print(f"  Total amount in duplicates: ${total_amount:,.2f}")
        print("  Sample duplicates to remove:")
        for inv in dup_invoices[:5]:
            print(f"    - {inv['invoice_number']}: ${inv['invoice_amount'] or 0:,.2f} (id={inv['invoice_id']})")

    count_307 = fix_duplicate_invoices(cursor, execute)
    print(f"  {'Deleted' if execute else 'Would delete'}: {count_307} records\n")

    # Issue #308: Orphaned invoice_aging
    print("Issue #308: Orphaned invoice_aging records")
    print("-" * 40)
    orphaned_aging = audit_orphaned_invoice_aging(cursor)
    print(f"  Found: {len(orphaned_aging)} orphaned records")
    if orphaned_aging and not execute:
        total_outstanding = sum(r['outstanding_amount'] or 0 for r in orphaned_aging)
        print(f"  Total outstanding in orphans: ${total_outstanding:,.2f}")
        print("  Sample orphaned invoice numbers:")
        for aging in orphaned_aging[:5]:
            print(f"    - {aging['invoice_number']} ({aging['project_code']}): ${aging['outstanding_amount'] or 0:,.2f}")

    count_308 = fix_orphaned_invoice_aging(cursor, execute)
    print(f"  {'Deleted' if execute else 'Would delete'}: {count_308} records\n")

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = count_306 + count_307 + count_308
    print(f"  #306 project_team:    {count_306} records")
    print(f"  #307 invoices:        {count_307} records")
    print(f"  #308 invoice_aging:   {count_308} records")
    print(f"  TOTAL:                {total} records")
    print()

    if execute:
        conn.commit()
        print("Changes COMMITTED to database.")
    else:
        print("No changes made (dry run).")
        print("\nTo execute cleanup, run:")
        print("  python scripts/core/data_quality_cleanup.py --execute")

    conn.close()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
