#!/usr/bin/env python3
"""
Migrate Critical Missing Tables from Desktop → OneDrive
"""
import sqlite3
import os
from datetime import datetime

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "database/bensley_master.db"

CRITICAL_TABLES = [
    'contacts',
    'invoice_aging',
    'proposal_tracker',
    'email_attachments',
    'team_members',
    'schedule_entries'
]

def migrate_critical_tables():
    """Migrate critical missing tables"""

    print("="*80)
    print("MIGRATING CRITICAL TABLES")
    print("="*80)

    # Backup
    print("\n[1/4] Creating backup...")
    backup_path = f"database/backups/bensley_master_pre_critical_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.makedirs("database/backups", exist_ok=True)
    os.system(f"cp {ONEDRIVE_DB} {backup_path}")
    print(f"✅ Backup: {backup_path}")

    # Connect
    print("\n[2/4] Connecting...")
    desktop_conn = sqlite3.connect(DESKTOP_DB)
    onedrive_conn = sqlite3.connect(ONEDRIVE_DB)

    desktop_conn.row_factory = sqlite3.Row
    onedrive_conn.row_factory = sqlite3.Row

    desktop_cursor = desktop_conn.cursor()
    onedrive_cursor = onedrive_conn.cursor()
    print("✅ Connected")

    # Migrate each table
    print("\n[3/4] Migrating tables...")

    migrated_summary = []

    for table in CRITICAL_TABLES:
        print(f"\n{'─'*80}")
        print(f"📋 {table}")
        print(f"{'─'*80}")

        # Check if table exists in Desktop
        desktop_cursor.execute(f"""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table,))

        if not desktop_cursor.fetchone():
            print(f"   ⚠️  Table doesn't exist in Desktop - skipping")
            continue

        # Get row count in Desktop
        desktop_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        desktop_count = desktop_cursor.fetchone()[0]
        print(f"   Desktop has {desktop_count} rows")

        if desktop_count == 0:
            print(f"   ℹ️  No data to migrate")
            continue

        # Get CREATE TABLE statement from Desktop
        desktop_cursor.execute(f"""
            SELECT sql FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table,))

        create_sql = desktop_cursor.fetchone()[0]

        # Check if table already exists in OneDrive
        onedrive_cursor.execute(f"""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """, (table,))

        if onedrive_cursor.fetchone():
            print(f"   ⚠️  Table already exists in OneDrive - dropping and recreating")
            onedrive_cursor.execute(f"DROP TABLE {table}")

        # Create table in OneDrive
        onedrive_cursor.execute(create_sql)
        print(f"   ✅ Created table in OneDrive")

        # Get all data from Desktop
        desktop_cursor.execute(f"SELECT * FROM {table}")
        rows = desktop_cursor.fetchall()

        # Get column names
        desktop_cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in desktop_cursor.fetchall()]

        # Insert data
        placeholders = ','.join(['?' for _ in columns])
        insert_sql = f"INSERT INTO {table} VALUES ({placeholders})"

        inserted = 0
        errors = 0

        for row in rows:
            try:
                onedrive_cursor.execute(insert_sql, tuple(row))
                inserted += 1
            except Exception as e:
                errors += 1
                if errors <= 3:  # Show first 3 errors
                    print(f"   ⚠️  Error: {e}")

        print(f"   ✅ Inserted {inserted} rows")
        if errors > 0:
            print(f"   ⚠️  {errors} errors")

        migrated_summary.append({
            'table': table,
            'rows': inserted,
            'errors': errors
        })

    # Verification
    print(f"\n{'='*80}")
    print("[4/4] VERIFICATION")
    print(f"{'='*80}")

    for item in migrated_summary:
        status = "✅" if item['errors'] == 0 else "⚠️ "
        print(f"{status} {item['table']:<30} {item['rows']:>6} rows migrated")

    # Final summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    total_rows = sum(item['rows'] for item in migrated_summary)
    total_errors = sum(item['errors'] for item in migrated_summary)

    print(f"✅ Migrated {len(migrated_summary)} tables")
    print(f"✅ Total rows: {total_rows}")
    if total_errors > 0:
        print(f"⚠️  Total errors: {total_errors}")
    print(f"✅ Backup: {backup_path}")

    print("\nCommit changes? (yes/no): ", end="")
    import sys
    response = sys.stdin.readline().strip().lower()

    if response == 'yes':
        onedrive_conn.commit()
        print("\n✅ MIGRATION COMPLETE!")

        # Show what OneDrive now has
        print(f"\n{'='*80}")
        print("ONEDRIVE NOW HAS:")
        print(f"{'='*80}")

        for table in CRITICAL_TABLES:
            try:
                onedrive_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = onedrive_cursor.fetchone()[0]
                print(f"   ✅ {table:<30} {count:>6} rows")
            except:
                print(f"   ❌ {table:<30} (not migrated)")

    else:
        onedrive_conn.rollback()
        print("\n❌ CANCELLED - No changes made")

    desktop_conn.close()
    onedrive_conn.close()

if __name__ == '__main__':
    migrate_critical_tables()
