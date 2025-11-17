#!/usr/bin/env python3
"""
Merge proposals table into projects table
Handles column additions dynamically to avoid SQLite limitations
"""

import sqlite3
from datetime import datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


def get_table_columns(cursor, table_name):
    """Get list of columns in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def add_column_if_not_exists(cursor, table_name, column_name, column_type):
    """Add column to table if it doesn't exist"""
    existing_columns = get_table_columns(cursor, table_name)

    if column_name not in existing_columns:
        print(f"  Adding column: {column_name} {column_type}")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        return True
    else:
        print(f"  Column {column_name} already exists, skipping")
        return False


def main():
    print("=" * 80)
    print("MIGRATION: Merge Proposals into Projects Table")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Step 1: Add missing columns from proposals to projects
        print("\nStep 1: Adding missing columns to projects table...")
        columns_to_add = [
            ("project_type", "TEXT"),
            ("country", "TEXT"),
            ("city", "TEXT"),
            ("contract_term_months", "INTEGER"),
            ("folder_path", "TEXT"),
            ("source_db", "TEXT"),
            ("source_ref", "TEXT")
        ]

        for col_name, col_type in columns_to_add:
            add_column_if_not_exists(cursor, "projects", col_name, col_type)

        conn.commit()

        # Step 2: Update existing duplicates
        print("\nStep 2: Updating existing projects with proposals data...")
        cursor.execute("""
            UPDATE projects
            SET
                project_name = COALESCE(project_name, (SELECT project_title FROM proposals WHERE proposals.project_code = projects.project_code)),
                project_type = (SELECT project_type FROM proposals WHERE proposals.project_code = projects.project_code),
                country = (SELECT country FROM proposals WHERE proposals.project_code = projects.project_code),
                city = (SELECT city FROM proposals WHERE proposals.project_code = projects.project_code),
                total_fee_usd = COALESCE(total_fee_usd, (SELECT total_fee_usd FROM proposals WHERE proposals.project_code = projects.project_code)),
                contract_term_months = COALESCE(contract_term_months, (SELECT contract_term_months FROM proposals WHERE proposals.project_code = projects.project_code)),
                contract_expiry_date = COALESCE(contract_expiry_date, (SELECT contract_expiry_date FROM proposals WHERE proposals.project_code = proposals.project_code)),
                folder_path = (SELECT folder_path FROM proposals WHERE proposals.project_code = projects.project_code),
                source_db = (SELECT source_db FROM proposals WHERE proposals.project_code = projects.project_code),
                source_ref = (SELECT source_ref FROM proposals WHERE proposals.project_code = projects.project_code),
                updated_at = ?
            WHERE project_code IN (SELECT project_code FROM proposals)
        """, (datetime.now().isoformat(),))

        print(f"  Updated {cursor.rowcount} existing projects")
        conn.commit()

        # Step 3: Insert proposals that don't exist in projects
        print("\nStep 3: Inserting new proposals into projects table...")
        cursor.execute("""
            INSERT INTO projects (
                project_code,
                project_name,
                project_type,
                country,
                city,
                total_fee_usd,
                contract_term_months,
                contract_expiry_date,
                folder_path,
                source_db,
                source_ref,
                status,
                is_active_project,
                created_at,
                updated_at
            )
            SELECT
                pr.project_code,
                pr.project_title,
                pr.project_type,
                pr.country,
                pr.city,
                pr.total_fee_usd,
                pr.contract_term_months,
                pr.contract_expiry_date,
                pr.folder_path,
                pr.source_db,
                pr.source_ref,
                COALESCE(pr.status, 'proposal'),
                CASE
                    WHEN pr.status IN ('Active', 'Completed') THEN 1
                    ELSE 0
                END,
                pr.date_created,
                ?
            FROM proposals pr
            WHERE pr.project_code NOT IN (SELECT project_code FROM projects)
        """, (datetime.now().isoformat(),))

        print(f"  Inserted {cursor.rowcount} new proposals")
        conn.commit()

        # Step 4: Standardize status values
        print("\nStep 4: Standardizing status values...")
        cursor.execute("""
            UPDATE projects
            SET status = CASE
                WHEN status IN ('Active', 'active') THEN 'active'
                WHEN status IN ('Proposal', 'proposal') THEN 'proposal'
                WHEN status IN ('Completed', 'completed') THEN 'completed'
                WHEN status IN ('On-Hold', 'on_hold', 'on-hold') THEN 'on_hold'
                WHEN status = 'archived' THEN 'archived'
                WHEN status = 'lost' THEN 'lost'
                ELSE 'proposal'
            END,
            is_active_project = CASE
                WHEN status IN ('Active', 'active') THEN 1
                ELSE 0
            END,
            updated_at = ?
        """, (datetime.now().isoformat(),))

        print(f"  Standardized {cursor.rowcount} status values")
        conn.commit()

        # Step 5: Create backup of proposals table
        print("\nStep 5: Creating backup of proposals table...")
        cursor.execute("DROP TABLE IF EXISTS proposals_backup")
        cursor.execute("CREATE TABLE proposals_backup AS SELECT * FROM proposals")
        print("  Backup created: proposals_backup")
        conn.commit()

        # Step 6: Create indexes
        print("\nStep 6: Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_is_active ON projects(is_active_project)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_status_active ON projects(status, is_active_project)")
        print("  Indexes created")
        conn.commit()

        # Step 7: Record migration
        print("\nStep 7: Recording migration...")
        cursor.execute("SELECT version FROM schema_migrations WHERE version = 15")
        if cursor.fetchone():
            print("  Migration 15 already recorded, skipping...")
        else:
            cursor.execute("""
                INSERT INTO schema_migrations (version, name, description, applied_at)
                VALUES (15, '015_merge_proposals_into_projects',
                       'Merge proposals table into unified projects table with lifecycle status', ?)
            """, (datetime.now().isoformat(),))
            conn.commit()
            print("  Migration recorded successfully")

        # Get final counts
        cursor.execute("SELECT COUNT(*) FROM projects")
        total_projects = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'proposal'")
        proposal_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'active' OR is_active_project = 1")
        active_count = cursor.fetchone()[0]

        print("\n" + "=" * 80)
        print("MIGRATION COMPLETE ✅")
        print("=" * 80)
        print(f"\nProjects table now contains:")
        print(f"  Total records: {total_projects}")
        print(f"  Proposals: {proposal_count}")
        print(f"  Active: {active_count}")
        print(f"  Other statuses: {total_projects - proposal_count - active_count}")
        print(f"\nproposals table backed up to: proposals_backup")
        print(f"All services should now use projects table exclusively")
        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
