#!/usr/bin/env python3
"""
Safe Table Migration - Desktop → OneDrive

Migrates ONLY matching projects with validation.
"""
import sqlite3
import os
from datetime import datetime

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "database/bensley_master.db"

def migrate_table_safely():
    """Migrate project_fee_breakdown from Desktop → OneDrive"""

    print("="*80)
    print("SAFE TABLE MIGRATION")
    print("="*80)

    # Step 1: Backup OneDrive database
    print("\n[1/6] Creating backup...")
    backup_path = f"database/backups/bensley_master_pre_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.makedirs("database/backups", exist_ok=True)
    os.system(f"cp {ONEDRIVE_DB} {backup_path}")
    print(f"✅ Backup created: {backup_path}")

    # Step 2: Connect to both databases
    print("\n[2/6] Connecting to databases...")
    desktop_conn = sqlite3.connect(DESKTOP_DB)
    onedrive_conn = sqlite3.connect(ONEDRIVE_DB)

    desktop_cursor = desktop_conn.cursor()
    onedrive_cursor = onedrive_conn.cursor()
    print("✅ Connected")

    # Step 3: Get OneDrive project codes (only migrate data for these)
    print("\n[3/6] Getting OneDrive project codes...")
    onedrive_cursor.execute("SELECT project_code FROM projects")
    onedrive_projects = {row[0] for row in onedrive_cursor.fetchall()}
    print(f"✅ Found {len(onedrive_projects)} projects in OneDrive")
    print(f"   Sample: {list(onedrive_projects)[:5]}")

    # Step 4: Get Desktop CREATE TABLE statement
    print("\n[4/6] Getting table schema from Desktop...")
    desktop_cursor.execute("""
        SELECT sql FROM sqlite_master
        WHERE type='table' AND name='project_fee_breakdown'
    """)
    create_table_sql = desktop_cursor.fetchone()[0]
    print("✅ Got schema")

    # Check if table already exists in OneDrive
    onedrive_cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='project_fee_breakdown'
    """)

    if onedrive_cursor.fetchone():
        print("⚠️  Table already exists in OneDrive - will DROP and recreate")
        onedrive_cursor.execute("DROP TABLE project_fee_breakdown")

    # Create table in OneDrive
    onedrive_cursor.execute(create_table_sql)
    print("✅ Created project_fee_breakdown table in OneDrive")

    # Step 5: Get Desktop data and filter to OneDrive projects only
    print("\n[5/6] Migrating data (only for OneDrive projects)...")
    desktop_cursor.execute("SELECT * FROM project_fee_breakdown")
    all_rows = desktop_cursor.fetchall()

    # Get column names
    desktop_cursor.execute("PRAGMA table_info(project_fee_breakdown)")
    columns = [col[1] for col in desktop_cursor.fetchall()]
    project_code_idx = columns.index('project_code')

    # Filter to only projects that exist in OneDrive
    matching_rows = [row for row in all_rows if row[project_code_idx] in onedrive_projects]

    print(f"   Total rows in Desktop: {len(all_rows)}")
    print(f"   Rows matching OneDrive projects: {len(matching_rows)}")
    print(f"   Filtering out: {len(all_rows) - len(matching_rows)} rows for non-existent projects")

    # Insert matching rows
    placeholders = ','.join(['?' for _ in columns])
    insert_sql = f"INSERT INTO project_fee_breakdown VALUES ({placeholders})"

    inserted = 0
    for row in matching_rows:
        try:
            onedrive_cursor.execute(insert_sql, row)
            inserted += 1
        except Exception as e:
            print(f"⚠️  Failed to insert row: {e}")

    print(f"✅ Inserted {inserted} rows")

    # Step 6: Verify
    print("\n[6/6] Verifying migration...")

    # Check row count
    onedrive_cursor.execute("SELECT COUNT(*) FROM project_fee_breakdown")
    onedrive_count = onedrive_cursor.fetchone()[0]
    print(f"   OneDrive now has: {onedrive_count} fee breakdown rows")

    # Check specific project (24 BK-074 - Dang Thai Mai)
    onedrive_cursor.execute("""
        SELECT phase, phase_fee_usd, discipline
        FROM project_fee_breakdown
        WHERE project_code = '24 BK-074'
        ORDER BY phase
    """)
    dang_thai_fees = onedrive_cursor.fetchall()

    if dang_thai_fees:
        print(f"\n   ✅ Dang Thai Mai (24 BK-074) has {len(dang_thai_fees)} fee breakdown entries:")
        total_fee = 0
        for phase, fee, discipline in dang_thai_fees[:5]:  # Show first 5
            total_fee += fee or 0
            print(f"      • {phase} ({discipline}): ${fee:,.0f}")
        print(f"   Total: ${total_fee:,.0f}")
    else:
        print("   ⚠️  WARNING: No fee breakdown found for 24 BK-074")

    # Final confirmation
    print("\n" + "="*80)
    print("MIGRATION SUMMARY")
    print("="*80)
    print(f"✅ Migrated {inserted} fee breakdown rows")
    print(f"✅ Filtered to OneDrive projects only")
    print(f"✅ Backup saved: {backup_path}")
    print("\nCommit changes? (yes/no): ", end="")

    response = input().strip().lower()

    if response == 'yes':
        onedrive_conn.commit()
        print("\n✅ MIGRATION COMPLETE!")
        print(f"   You can restore from backup if needed: {backup_path}")
    else:
        onedrive_conn.rollback()
        print("\n❌ MIGRATION CANCELLED - No changes made")

    desktop_conn.close()
    onedrive_conn.close()

if __name__ == '__main__':
    migrate_table_safely()
