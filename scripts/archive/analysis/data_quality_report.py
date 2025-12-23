#!/usr/bin/env python3
"""
Data Quality Report for BDS Operations Platform
Run weekly to check data health

Usage:
    python scripts/analysis/data_quality_report.py

Created: 2025-11-26 by Agent 4 (Data Pipeline)
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Database path - follow project convention
DB_PATH = os.getenv("DATABASE_PATH", "database/bensley_master.db")


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_report():
    """Generate comprehensive data quality report"""
    conn = get_connection()
    cursor = conn.cursor()

    print("=" * 70)
    print(f"BDS DATA QUALITY REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    # ========== TABLE COUNTS ==========
    print("\n" + "-" * 40)
    print("TABLE COUNTS")
    print("-" * 40)

    tables = [
        ("projects", "Active contracts"),
        ("proposals", "Sales pipeline"),
        ("invoices", "Financial records"),
        ("emails", "Communications"),
        ("meeting_transcripts", "Voice memos"),
        ("rfis", "Requests for info"),
        ("project_milestones", "Project tracking"),
        ("communication_log", "Activity log"),
        ("contacts", "People"),
        ("clients", "Companies"),
    ]

    for table, description in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table:25} {count:>6}  ({description})")
        except Exception as e:
            print(f"  {table:25} ERROR  ({str(e)[:30]})")

    # ========== RECENT ACTIVITY (7 days) ==========
    print("\n" + "-" * 40)
    print("RECENT ACTIVITY (Last 7 days)")
    print("-" * 40)

    # Emails
    cursor.execute("""
        SELECT COUNT(*) FROM emails
        WHERE date > datetime('now', '-7 days')
    """)
    print(f"  New emails:              {cursor.fetchone()[0]:>6}")

    # Transcripts
    cursor.execute("""
        SELECT COUNT(*) FROM meeting_transcripts
        WHERE created_at > datetime('now', '-7 days')
    """)
    print(f"  New transcripts:         {cursor.fetchone()[0]:>6}")

    # RFIs
    cursor.execute("""
        SELECT COUNT(*) FROM rfis
        WHERE created_at > datetime('now', '-7 days')
    """)
    print(f"  New RFIs:                {cursor.fetchone()[0]:>6}")

    # ========== DATA QUALITY ISSUES ==========
    print("\n" + "-" * 40)
    print("DATA QUALITY ISSUES")
    print("-" * 40)

    issues_found = 0

    # Milestones without planned_date
    cursor.execute("""
        SELECT COUNT(*) FROM project_milestones
        WHERE planned_date IS NULL
    """)
    null_dates = cursor.fetchone()[0]
    if null_dates > 0:
        print(f"  [WARN] Milestones without planned_date: {null_dates}")
        issues_found += 1
    else:
        print(f"  [OK]   All milestones have planned_date")

    # Open RFIs
    cursor.execute("""
        SELECT COUNT(*) FROM rfis WHERE status = 'open'
    """)
    open_rfis = cursor.fetchone()[0]
    print(f"  [INFO] Open RFIs:                        {open_rfis}")

    # Overdue RFIs
    cursor.execute("""
        SELECT COUNT(*) FROM rfis
        WHERE status = 'open' AND date(date_due) < date('now')
    """)
    overdue_rfis = cursor.fetchone()[0]
    if overdue_rfis > 0:
        print(f"  [WARN] Overdue RFIs:                     {overdue_rfis}")
        issues_found += 1

    # Overdue invoices (>30 days unpaid)
    cursor.execute("""
        SELECT COUNT(*) FROM invoices
        WHERE payment_date IS NULL
        AND status NOT IN ('paid', 'cancelled')
        AND invoice_date < date('now', '-30 days')
    """)
    overdue_inv = cursor.fetchone()[0]
    if overdue_inv > 0:
        print(f"  [WARN] Overdue invoices (>30 days):      {overdue_inv}")
        issues_found += 1

    # Emails with NULL dates
    cursor.execute("""
        SELECT COUNT(*) FROM emails WHERE date IS NULL
    """)
    null_email_dates = cursor.fetchone()[0]
    if null_email_dates > 0:
        print(f"  [WARN] Emails without date:              {null_email_dates}")
        issues_found += 1

    # Projects without project_code
    cursor.execute("""
        SELECT COUNT(*) FROM projects WHERE project_code IS NULL OR project_code = ''
    """)
    missing_codes = cursor.fetchone()[0]
    if missing_codes > 0:
        print(f"  [WARN] Projects without code:            {missing_codes}")
        issues_found += 1

    if issues_found == 0:
        print(f"  [OK]   No critical issues found")

    # ========== TRANSCRIPT COVERAGE ==========
    print("\n" + "-" * 40)
    print("VOICE TRANSCRIPT COVERAGE")
    print("-" * 40)

    cursor.execute("""
        SELECT
            COUNT(DISTINCT detected_project_code) as projects_with_transcripts
        FROM meeting_transcripts
        WHERE detected_project_code IS NOT NULL
    """)
    with_transcripts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT project_code) FROM projects")
    total_projects = cursor.fetchone()[0]

    print(f"  Projects with transcripts: {with_transcripts} / {total_projects}")

    cursor.execute("""
        SELECT detected_project_code, COUNT(*) as count
        FROM meeting_transcripts
        WHERE detected_project_code IS NOT NULL
        GROUP BY detected_project_code
        ORDER BY count DESC
        LIMIT 5
    """)
    print(f"  Top projects by transcript count:")
    for row in cursor.fetchall():
        print(f"    - {row['detected_project_code']}: {row['count']} transcripts")

    # ========== EMAIL DISTRIBUTION ==========
    print("\n" + "-" * 40)
    print("EMAIL DISTRIBUTION")
    print("-" * 40)

    cursor.execute("""
        SELECT
            CASE
                WHEN date IS NULL THEN 'No date'
                WHEN date > datetime('now', '-7 days') THEN 'Last 7 days'
                WHEN date > datetime('now', '-30 days') THEN 'Last 30 days'
                WHEN date > datetime('now', '-90 days') THEN 'Last 90 days'
                ELSE 'Older'
            END as period,
            COUNT(*) as count
        FROM emails
        GROUP BY period
        ORDER BY
            CASE period
                WHEN 'Last 7 days' THEN 1
                WHEN 'Last 30 days' THEN 2
                WHEN 'Last 90 days' THEN 3
                WHEN 'Older' THEN 4
                ELSE 5
            END
    """)
    for row in cursor.fetchall():
        print(f"  {row['period']:20} {row['count']:>6}")

    # ========== PROPOSAL STATUS ==========
    print("\n" + "-" * 40)
    print("PROPOSAL STATUS BREAKDOWN")
    print("-" * 40)

    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM proposals
        GROUP BY status
        ORDER BY count DESC
    """)
    for row in cursor.fetchall():
        status = row['status'] or 'No status'
        print(f"  {status:25} {row['count']:>6}")

    # ========== SUMMARY ==========
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Data quality issues found: {issues_found}")
    if issues_found > 0:
        print("  Run appropriate migrations/scripts to fix issues")
    print(f"  Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")

    conn.close()


if __name__ == "__main__":
    # Change to project root if running from scripts/analysis/
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    os.chdir(project_root)

    run_report()
