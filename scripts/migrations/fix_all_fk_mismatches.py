#!/usr/bin/env python3
"""
Fix All FK Mismatches

This script fixes all foreign key column mismatches found in the database schema.
These are FKs that reference wrong column names (e.g., emails(id) instead of emails(email_id)).

Fixes:
1. meeting_transcripts: detected_project_id -> projects(id) should be projects(project_id)
2. invoice_aging: invoice_number -> invoices(invoice_number) is not unique - remove FK

Run: python scripts/migrations/fix_all_fk_mismatches.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bensley_master.db"


def fix_meeting_transcripts(conn, cursor):
    """Fix meeting_transcripts FK: projects(id) -> projects(project_id)"""
    print("\n1. Fixing meeting_transcripts FK...")

    cursor.execute("SELECT COUNT(*) FROM meeting_transcripts")
    count = cursor.fetchone()[0]
    print(f"   Records: {count}")

    cursor.executescript("""
        PRAGMA foreign_keys = OFF;

        CREATE TABLE meeting_transcripts_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audio_filename TEXT,
            audio_path TEXT,
            transcript TEXT,
            summary TEXT,
            key_points TEXT,
            action_items TEXT,
            detected_project_id INTEGER,
            detected_project_code TEXT,
            match_confidence REAL,
            meeting_type TEXT,
            participants TEXT,
            sentiment TEXT,
            duration_seconds REAL,
            recorded_date TEXT,
            processed_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            project_id INTEGER,
            proposal_id INTEGER,
            meeting_title TEXT,
            meeting_date TEXT,
            final_summary_email_id INTEGER,
            polished_summary TEXT,
            FOREIGN KEY (detected_project_id) REFERENCES projects(project_id),
            FOREIGN KEY (project_id) REFERENCES projects(project_id),
            FOREIGN KEY (proposal_id) REFERENCES proposal_tracker(id),
            FOREIGN KEY (final_summary_email_id) REFERENCES emails(email_id)
        );

        INSERT INTO meeting_transcripts_new SELECT * FROM meeting_transcripts;
        DROP TABLE meeting_transcripts;
        ALTER TABLE meeting_transcripts_new RENAME TO meeting_transcripts;

        CREATE INDEX idx_transcripts_project ON meeting_transcripts(project_id);
        CREATE INDEX idx_transcripts_proposal ON meeting_transcripts(proposal_id);

        PRAGMA foreign_keys = ON;
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM meeting_transcripts")
    new_count = cursor.fetchone()[0]
    if new_count == count:
        print("   Fixed - data preserved")
    else:
        print(f"   WARNING: Record count changed from {count} to {new_count}")


def fix_invoice_aging(conn, cursor):
    """Fix invoice_aging FK: invoices(invoice_number) is not unique - remove invalid FK"""
    print("\n2. Fixing invoice_aging FK...")

    cursor.execute("SELECT COUNT(*) FROM invoice_aging")
    count = cursor.fetchone()[0]
    print(f"   Records: {count}")

    # The invoices.invoice_number is not unique, so we can't have a valid FK to it
    # Remove the FK constraint but keep the column for the join relationship
    cursor.executescript("""
        PRAGMA foreign_keys = OFF;

        CREATE TABLE invoice_aging_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT NOT NULL,
            invoice_number TEXT NOT NULL,
            invoice_date TEXT,
            invoice_amount REAL,
            payment_amount REAL,
            outstanding_amount REAL,
            days_outstanding INTEGER,
            aging_category TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_code) REFERENCES projects(project_code)
            -- Note: invoice_number FK removed - invoices.invoice_number is not unique
        );

        INSERT INTO invoice_aging_new SELECT * FROM invoice_aging;
        DROP TABLE invoice_aging;
        ALTER TABLE invoice_aging_new RENAME TO invoice_aging;

        PRAGMA foreign_keys = ON;
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM invoice_aging")
    new_count = cursor.fetchone()[0]
    if new_count == count:
        print("   Fixed - removed invalid FK to non-unique column")
    else:
        print(f"   WARNING: Record count changed from {count} to {new_count}")


def run_migration():
    print("=" * 60)
    print("Fix All FK Mismatches")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        fix_meeting_transcripts(conn, cursor)
        fix_invoice_aging(conn, cursor)

        print("\n" + "=" * 60)
        print("ALL FK MISMATCHES FIXED")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
