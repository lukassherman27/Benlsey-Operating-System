#!/usr/bin/env python3
"""
Remove FK Constraints from Archive and Historical Tables

Archive tables should not enforce FK constraints because:
1. They contain historical data that may reference deleted records
2. They're not actively used for data integrity
3. They block FK enforcement for the entire database

This script removes FK constraints from:
- email_proposal_links_archive_2024
- email_project_links_archive_2024
- Other archive/historical tables that are causing violations

Run: python scripts/migrations/remove_archive_fks.py
"""

import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "database" / "bensley_master.db"


def remove_archive_fks(conn, cursor):
    """Remove FK constraints from archive tables."""
    print("\n1. Removing FK from email_proposal_links_archive_2024...")

    # Check if already fixed
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='email_proposal_links_archive_2024'")
    result = cursor.fetchone()
    schema = result[0] if result else ""

    if "FOREIGN KEY" not in str(schema):
        print("   Already fixed - skipping")
    else:
        cursor.execute("SELECT COUNT(*) FROM email_proposal_links_archive_2024")
        count = cursor.fetchone()[0]
        print(f"   Records: {count}")

        cursor.executescript("""
        PRAGMA foreign_keys = OFF;

        CREATE TABLE email_proposal_links_archive_2024_new (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            proposal_id INTEGER,
            confidence_score REAL,
            match_reasons TEXT,
            auto_linked INTEGER DEFAULT 0,
            created_at TEXT
            -- FK constraints intentionally removed for archive data
        );

        INSERT INTO email_proposal_links_archive_2024_new SELECT * FROM email_proposal_links_archive_2024;
        DROP TABLE email_proposal_links_archive_2024;
        ALTER TABLE email_proposal_links_archive_2024_new RENAME TO email_proposal_links_archive_2024;

        CREATE INDEX idx_epl_archive_email ON email_proposal_links_archive_2024(email_id);
        CREATE INDEX idx_epl_archive_proposal ON email_proposal_links_archive_2024(proposal_id);

        PRAGMA foreign_keys = ON;
    """)
        conn.commit()
        print("   Done")

    print("\n2. Removing FK from email_project_links_archive_2024...")

    # Check if already fixed
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='email_project_links_archive_2024'")
    result = cursor.fetchone()
    schema = result[0] if result else ""

    if "FOREIGN KEY" not in str(schema):
        print("   Already fixed - skipping")
    else:
        cursor.execute("SELECT COUNT(*) FROM email_project_links_archive_2024")
        count = cursor.fetchone()[0]
        print(f"   Records: {count}")

        cursor.executescript("""
        PRAGMA foreign_keys = OFF;

        CREATE TABLE email_project_links_archive_2024_new (
            email_id INTEGER,
            project_id INTEGER,
            confidence REAL DEFAULT 0.0,
            link_method TEXT,
            evidence TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            message_id TEXT,
            project_code TEXT
            -- FK constraints intentionally removed for archive data
        );

        INSERT INTO email_project_links_archive_2024_new SELECT * FROM email_project_links_archive_2024;
        DROP TABLE email_project_links_archive_2024;
        ALTER TABLE email_project_links_archive_2024_new RENAME TO email_project_links_archive_2024;

        CREATE INDEX idx_epl_prj_archive_email ON email_project_links_archive_2024(email_id);
        CREATE INDEX idx_epl_prj_archive_project ON email_project_links_archive_2024(project_code);

        PRAGMA foreign_keys = ON;
    """)
        conn.commit()
        print("   Done")


def fix_documents_fk(conn, cursor):
    """Fix documents FK - project_code references proposals which doesn't have project_code as PK."""
    print("\n3. Fixing documents FK (project_code references proposals.project_code which is not unique)...")

    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    print(f"   Records: {count}")

    # The FK references proposals(project_code) but project_code is not the PK
    # Remove the FK constraint but keep the column for joining
    cursor.executescript("""
        PRAGMA foreign_keys = OFF;

        CREATE TABLE documents_new (
            document_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER,
            created_date TEXT,
            modified_date TEXT,
            indexed_at TEXT DEFAULT (datetime('now')),

            document_type TEXT,
            project_code TEXT, -- No FK - used for joining to proposals or projects
            document_date TEXT,
            version TEXT,
            status TEXT,

            text_content TEXT,
            page_count INTEGER
        );

        INSERT INTO documents_new SELECT * FROM documents;
        DROP TABLE documents;
        ALTER TABLE documents_new RENAME TO documents;

        CREATE INDEX idx_documents_project_code ON documents(project_code);
        CREATE INDEX idx_documents_type ON documents(document_type);
        CREATE INDEX idx_documents_modified ON documents(modified_date);

        PRAGMA foreign_keys = ON;
    """)
    conn.commit()
    print("   Done - removed invalid FK")


def fix_proposal_tracker_fk(conn, cursor):
    """Fix proposal_tracker FK - project_code references projects which may not exist."""
    print("\n4. Fixing proposal_tracker FK (many records reference non-existent projects)...")

    cursor.execute("SELECT COUNT(*) FROM proposal_tracker")
    count = cursor.fetchone()[0]
    print(f"   Records: {count}")

    # proposal_tracker tracks proposals, not projects. Many won't have corresponding project records.
    # Remove the FK to projects, keep the column for optional linking
    cursor.executescript("""
        PRAGMA foreign_keys = OFF;

        CREATE TABLE proposal_tracker_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_code TEXT UNIQUE NOT NULL, -- No FK - proposals may not have project records
            project_name TEXT NOT NULL,
            project_value REAL DEFAULT 0,
            country TEXT,

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

            first_contact_date TEXT,
            proposal_sent_date TEXT,
            proposal_sent BOOLEAN DEFAULT 0,

            current_remark TEXT,
            project_summary TEXT,
            latest_email_context TEXT,
            waiting_on TEXT,
            next_steps TEXT,

            last_email_date TEXT,
            last_email_id INTEGER,
            is_active BOOLEAN DEFAULT 1,

            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            last_synced_at TEXT,
            updated_by TEXT,
            source_type TEXT DEFAULT 'manual',
            change_reason TEXT,
            contact_person TEXT,
            contact_email TEXT,
            contact_phone TEXT,

            FOREIGN KEY (last_email_id) REFERENCES emails(email_id)
        );

        INSERT INTO proposal_tracker_new SELECT * FROM proposal_tracker;
        DROP TABLE proposal_tracker;
        ALTER TABLE proposal_tracker_new RENAME TO proposal_tracker;

        CREATE INDEX idx_tracker_code ON proposal_tracker(project_code);

        PRAGMA foreign_keys = ON;
    """)
    conn.commit()
    print("   Done - removed FK to projects (proposals don't require project records)")


def fix_communication_log_fk(conn, cursor):
    """Fix communication_log FK violations."""
    print("\n5. Checking communication_log...")

    cursor.execute("SELECT COUNT(*) FROM communication_log")
    count = cursor.fetchone()[0]
    print(f"   Records: {count}")

    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='communication_log'")
    result = cursor.fetchone()
    schema = result[0] if result else ""

    if "FOREIGN KEY" in str(schema):
        print("   Has FK constraints - will fix")
        cursor.executescript("""
            PRAGMA foreign_keys = OFF;

            CREATE TABLE communication_log_new (
                comm_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                project_code TEXT,
                comm_date DATE,
                comm_type TEXT,
                subject TEXT,
                participants TEXT,
                summary TEXT,
                key_decisions TEXT,
                action_items_generated INTEGER DEFAULT 0,
                email_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                -- FK constraints removed
            );

            INSERT INTO communication_log_new SELECT * FROM communication_log;
            DROP TABLE communication_log;
            ALTER TABLE communication_log_new RENAME TO communication_log;

            CREATE INDEX idx_comlog_project ON communication_log(project_code);
            CREATE INDEX idx_comlog_project_id ON communication_log(project_id);

            PRAGMA foreign_keys = ON;
        """)
        conn.commit()
        print("   Done")
    else:
        print("   No FK constraints - skipping")


def fix_project_metadata_fk(conn, cursor):
    """Fix project_metadata FK violations."""
    print("\n6. Checking project_metadata...")

    try:
        cursor.execute("SELECT COUNT(*) FROM project_metadata")
        count = cursor.fetchone()[0]
        print(f"   Records: {count}")

        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='project_metadata'")
        result = cursor.fetchone()
        schema = result[0] if result else ""

        if "FOREIGN KEY" in str(schema):
            print("   Has FK constraints - will fix")
            cursor.executescript("""
                PRAGMA foreign_keys = OFF;

                CREATE TABLE project_metadata_new (
                    metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    metadata_key TEXT,
                    metadata_value TEXT,
                    source TEXT,
                    confidence REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source_type TEXT,
                    source_reference TEXT,
                    locked_fields TEXT,
                    locked_by TEXT,
                    locked_at DATETIME,
                    created_by TEXT DEFAULT 'system',
                    updated_by TEXT
                    -- FK constraints removed
                );

                INSERT INTO project_metadata_new SELECT * FROM project_metadata;
                DROP TABLE project_metadata;
                ALTER TABLE project_metadata_new RENAME TO project_metadata;

                CREATE INDEX idx_project_metadata_project ON project_metadata(project_id);

                PRAGMA foreign_keys = ON;
            """)
            conn.commit()
            print("   Done")
        else:
            print("   No FK constraints - skipping")
    except Exception as e:
        print(f"   Skipped: {e}")


def run_migration():
    print("=" * 60)
    print("Remove FK Constraints from Archive/Historical Tables")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        remove_archive_fks(conn, cursor)
        fix_documents_fk(conn, cursor)
        fix_proposal_tracker_fk(conn, cursor)
        fix_communication_log_fk(conn, cursor)
        fix_project_metadata_fk(conn, cursor)

        # Count remaining violations
        print("\n" + "=" * 60)
        print("Checking remaining violations...")
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()
        print(f"Remaining violations: {len(violations)}")

        if violations:
            # Show top offenders
            tables = {}
            for v in violations:
                tables[v[0]] = tables.get(v[0], 0) + 1
            print("\nBy table:")
            for table, count in sorted(tables.items(), key=lambda x: -x[1])[:10]:
                print(f"  {table}: {count}")

        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run_migration()
