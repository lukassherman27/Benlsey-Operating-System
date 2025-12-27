#!/usr/bin/env python3
"""
Migration: Add inbox_source column to emails table

This migration:
1. Adds inbox_source column to store which inbox the email came from
2. Adds inbox_category column for routing (invoices, projects, internal, etc.)
3. Backfills existing data from folder column (e.g., "lukas@bensley.com:INBOX")
4. Creates index for efficient filtering

Run: python scripts/migrations/add_inbox_source_column.py
"""

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bensley_master.db"


def run_migration():
    print("=" * 60)
    print("Migration: Add inbox_source column")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(emails)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'inbox_source' in columns:
        print("Column 'inbox_source' already exists. Skipping creation.")
    else:
        print("Adding 'inbox_source' column...")
        cursor.execute("ALTER TABLE emails ADD COLUMN inbox_source TEXT")
        print("  Added inbox_source column")

    if 'inbox_category' in columns:
        print("Column 'inbox_category' already exists. Skipping creation.")
    else:
        print("Adding 'inbox_category' column...")
        cursor.execute("""
            ALTER TABLE emails ADD COLUMN inbox_category TEXT
            CHECK(inbox_category IN (
                'proposals',      -- Bill's proposals inbox
                'projects',       -- Project correspondence
                'invoices',       -- Payment/invoice tracking
                'internal',       -- Internal (dailywork, scheduling)
                'general',        -- General inbox (lukas@, bill@)
                'unknown'         -- Unclassified
            ))
        """)
        print("  Added inbox_category column")

    conn.commit()

    # Backfill existing data
    print("\nBackfilling inbox_source from folder column...")

    # Find emails with account:folder format
    cursor.execute("""
        SELECT email_id, folder
        FROM emails
        WHERE folder LIKE '%@%:%'
        AND inbox_source IS NULL
    """)

    emails_to_update = cursor.fetchall()
    updated_count = 0

    for email_id, folder in emails_to_update:
        # Parse "account@domain.com:FOLDER" format
        if ':' in folder:
            inbox_source = folder.split(':')[0]

            # Determine inbox category based on email address
            inbox_category = categorize_inbox(inbox_source)

            cursor.execute("""
                UPDATE emails
                SET inbox_source = ?, inbox_category = ?
                WHERE email_id = ?
            """, (inbox_source, inbox_category, email_id))
            updated_count += 1

    # Handle legacy emails without account prefix
    cursor.execute("""
        UPDATE emails
        SET inbox_source = 'lukas@bensley.com',
            inbox_category = 'general'
        WHERE inbox_source IS NULL
        AND folder IN ('INBOX', 'Sent')
    """)
    legacy_count = cursor.rowcount

    conn.commit()

    print(f"  Updated {updated_count} emails with account:folder format")
    print(f"  Updated {legacy_count} legacy emails (assumed lukas@)")

    # Create index
    print("\nCreating indexes...")
    try:
        cursor.execute("CREATE INDEX idx_emails_inbox_source ON emails(inbox_source)")
        print("  Created idx_emails_inbox_source")
    except sqlite3.OperationalError:
        print("  Index idx_emails_inbox_source already exists")

    try:
        cursor.execute("CREATE INDEX idx_emails_inbox_category ON emails(inbox_category)")
        print("  Created idx_emails_inbox_category")
    except sqlite3.OperationalError:
        print("  Index idx_emails_inbox_category already exists")

    conn.commit()

    # Summary
    cursor.execute("SELECT inbox_source, COUNT(*) FROM emails GROUP BY inbox_source")
    print("\nEmails by inbox_source:")
    for row in cursor.fetchall():
        print(f"  {row[0] or 'NULL'}: {row[1]}")

    cursor.execute("SELECT inbox_category, COUNT(*) FROM emails GROUP BY inbox_category")
    print("\nEmails by inbox_category:")
    for row in cursor.fetchall():
        print(f"  {row[0] or 'NULL'}: {row[1]}")

    conn.close()
    print("\nMigration complete!")


def categorize_inbox(inbox_email: str) -> str:
    """
    Categorize an inbox email address into a routing category.

    Categories:
    - proposals: BD/proposals work (bd@, businessdevelopment@)
    - projects: Project correspondence (projects@)
    - invoices: Payment tracking (invoices@)
    - internal: Internal comms (dailywork@, scheduling@)
    - general: Personal inboxes (lukas@, bill@)
    """
    inbox_lower = inbox_email.lower()

    if inbox_lower.startswith('projects@'):
        return 'projects'
    elif inbox_lower.startswith('invoices@'):
        return 'invoices'
    elif inbox_lower.startswith('dailywork@') or inbox_lower.startswith('scheduling@'):
        return 'internal'
    elif inbox_lower.startswith('bd@') or inbox_lower.startswith('businessdevelopment@'):
        return 'proposals'
    elif inbox_lower.startswith('lukas@') or inbox_lower.startswith('bill@'):
        return 'general'
    else:
        return 'unknown'


if __name__ == "__main__":
    run_migration()
