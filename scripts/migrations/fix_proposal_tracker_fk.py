#!/usr/bin/env python3
"""
Fix proposal_tracker FK mismatch

The proposal_tracker table has a FK referencing emails(id) but the emails
table uses email_id as its primary key. This script recreates the table
with the correct FK definition.

Run: python scripts/migrations/fix_proposal_tracker_fk.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bensley_master.db"


def run_migration():
    print("=" * 60)
    print("Fix proposal_tracker FK mismatch")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check current state
    print("\n1. Checking current proposal_tracker state...")
    cursor.execute("SELECT COUNT(*) FROM proposal_tracker")
    count = cursor.fetchone()[0]
    print(f"   Records: {count}")

    cursor.execute("SELECT COUNT(*) FROM proposal_tracker WHERE last_email_id IS NOT NULL")
    with_email = cursor.fetchone()[0]
    print(f"   With last_email_id: {with_email}")

    # Recreate table with correct FK
    print("\n2. Recreating proposal_tracker with correct FK...")

    cursor.executescript("""
        -- Disable FK temporarily for migration
        PRAGMA foreign_keys = OFF;

        -- Create new table with correct FK
        CREATE TABLE proposal_tracker_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT UNIQUE NOT NULL,
            project_name TEXT NOT NULL,
            project_value REAL DEFAULT 0,
            country TEXT,

            -- Status tracking
            current_status TEXT CHECK(current_status IN (
                'First Contact',
                'Drafting',
                'Proposal Sent',
                'On Hold',
                'Archived',
                'Contract Signed'
            )) DEFAULT 'First Contact',
            last_week_status TEXT,
            status_changed_date TEXT,
            days_in_current_status INTEGER DEFAULT 0,

            -- Key dates
            first_contact_date TEXT,
            proposal_sent_date TEXT,
            proposal_sent BOOLEAN DEFAULT 0,

            -- Context and notes (auto-populated from emails)
            current_remark TEXT,
            project_summary TEXT,
            latest_email_context TEXT,
            waiting_on TEXT,
            next_steps TEXT,

            -- Tracking
            last_email_date TEXT,
            last_email_id INTEGER,
            is_active BOOLEAN DEFAULT 1,

            -- Metadata
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            last_synced_at TEXT,
            updated_by TEXT,
            source_type TEXT DEFAULT 'manual',
            change_reason TEXT,
            contact_person TEXT,
            contact_email TEXT,
            contact_phone TEXT,

            FOREIGN KEY (project_code) REFERENCES projects(project_code),
            FOREIGN KEY (last_email_id) REFERENCES emails(email_id)
        );

        -- Copy data
        INSERT INTO proposal_tracker_new SELECT * FROM proposal_tracker;

        -- Drop old table and rename
        DROP TABLE proposal_tracker;
        ALTER TABLE proposal_tracker_new RENAME TO proposal_tracker;

        -- Recreate index
        CREATE INDEX idx_tracker_code ON proposal_tracker(project_code);

        -- Re-enable FK
        PRAGMA foreign_keys = ON;
    """)

    conn.commit()

    # Verify
    print("\n3. Verifying migration...")
    cursor.execute("SELECT COUNT(*) FROM proposal_tracker")
    new_count = cursor.fetchone()[0]
    print(f"   Records after migration: {new_count}")

    if new_count == count:
        print("   Data preserved successfully")
    else:
        print(f"   WARNING: Record count changed from {count} to {new_count}")

    # Check FK definition
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='proposal_tracker'")
    schema = cursor.fetchone()[0]
    if "emails(email_id)" in schema:
        print("   FK correctly references emails(email_id)")
    else:
        print("   WARNING: FK may not be correct")

    conn.close()

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
