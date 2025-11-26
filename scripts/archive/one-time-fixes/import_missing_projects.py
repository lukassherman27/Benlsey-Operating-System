#!/usr/bin/env python3
"""
Import Missing Projects + Fee Breakdowns from Desktop → OneDrive
"""
import sqlite3
import os
from datetime import datetime

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "database/bensley_master.db"

MISSING_PROJECTS = [
    '16 BK-076',
    '23 BK-029',
    '25 BK-013',
    '25 BK-021',
    '25 BK-030',
    '25 BK-033'
]

def import_projects_and_fees():
    """Import missing projects and their fee breakdowns"""

    print("="*80)
    print("IMPORT MISSING PROJECTS + FEE BREAKDOWNS")
    print("="*80)

    # Backup first
    print("\n[1/5] Creating backup...")
    backup_path = f"database/backups/bensley_master_pre_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.makedirs("database/backups", exist_ok=True)
    os.system(f"cp {ONEDRIVE_DB} {backup_path}")
    print(f"✅ Backup: {backup_path}")

    # Connect
    print("\n[2/5] Connecting...")
    desktop_conn = sqlite3.connect(DESKTOP_DB)
    onedrive_conn = sqlite3.connect(ONEDRIVE_DB)

    desktop_conn.row_factory = sqlite3.Row
    onedrive_conn.row_factory = sqlite3.Row

    desktop_cursor = desktop_conn.cursor()
    onedrive_cursor = onedrive_conn.cursor()
    print("✅ Connected")

    # Get OneDrive projects schema
    print("\n[3/5] Getting OneDrive projects schema...")
    onedrive_cursor.execute("PRAGMA table_info(projects)")
    onedrive_cols = [col[1] for col in onedrive_cursor.fetchall()]
    print(f"✅ OneDrive projects has {len(onedrive_cols)} columns")

    # Get Desktop projects
    print("\n[4/5] Importing 6 missing projects...")
    desktop_cursor.execute(f"""
        SELECT * FROM projects
        WHERE project_code IN ({','.join(['?' for _ in MISSING_PROJECTS])})
    """, MISSING_PROJECTS)

    desktop_projects = desktop_cursor.fetchall()
    print(f"   Found {len(desktop_projects)} projects in Desktop")

    # Get Desktop project columns
    desktop_cursor.execute("PRAGMA table_info(projects)")
    desktop_cols = [col[1] for col in desktop_cursor.fetchall()]

    # Map Desktop columns to OneDrive columns
    common_cols = [col for col in desktop_cols if col in onedrive_cols]
    print(f"   {len(common_cols)} common columns between databases")

    imported = 0
    for project in desktop_projects:
        try:
            # Build insert using only common columns
            cols_str = ', '.join(common_cols)
            placeholders = ', '.join(['?' for _ in common_cols])
            values = [project[col] for col in common_cols]

            onedrive_cursor.execute(f"""
                INSERT OR REPLACE INTO projects ({cols_str})
                VALUES ({placeholders})
            """, values)

            imported += 1
            print(f"   ✅ {project['project_code']}: {project['project_name'][:50]}")

        except Exception as e:
            print(f"   ❌ Failed {project['project_code']}: {e}")

    print(f"\n✅ Imported {imported} projects")

    # Now migrate ALL fee breakdowns (46 existing + 6 new = 52 total)
    print("\n[5/5] Migrating fee breakdowns...")

    # Get OneDrive project codes (now includes the 6 new ones)
    onedrive_cursor.execute("SELECT project_code FROM projects")
    onedrive_projects = {row[0] for row in onedrive_cursor.fetchall()}
    print(f"   OneDrive now has {len(onedrive_projects)} projects")

    # Drop existing fee breakdown table if exists
    onedrive_cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='project_fee_breakdown'
    """)
    if onedrive_cursor.fetchone():
        onedrive_cursor.execute("DROP TABLE project_fee_breakdown")
        print("   Dropped existing fee_breakdown table")

    # Get Desktop CREATE TABLE statement
    desktop_cursor.execute("""
        SELECT sql FROM sqlite_master
        WHERE type='table' AND name='project_fee_breakdown'
    """)
    create_table_sql = desktop_cursor.fetchone()[0]

    # Create table in OneDrive
    onedrive_cursor.execute(create_table_sql)
    print("   ✅ Created project_fee_breakdown table")

    # Get ALL fee breakdown data
    desktop_cursor.execute("SELECT * FROM project_fee_breakdown")
    all_rows = desktop_cursor.fetchall()

    # Get columns
    desktop_cursor.execute("PRAGMA table_info(project_fee_breakdown)")
    fee_cols = [col[1] for col in desktop_cursor.fetchall()]
    project_code_idx = fee_cols.index('project_code')

    # Filter to OneDrive projects
    matching_rows = [row for row in all_rows if row[project_code_idx] in onedrive_projects]

    print(f"   Desktop has {len(all_rows)} fee breakdown rows")
    print(f"   Migrating {len(matching_rows)} rows for {len(onedrive_projects)} projects")

    # Insert
    placeholders = ','.join(['?' for _ in fee_cols])
    insert_sql = f"INSERT INTO project_fee_breakdown VALUES ({placeholders})"

    fee_imported = 0
    for row in matching_rows:
        try:
            onedrive_cursor.execute(insert_sql, tuple(row))
            fee_imported += 1
        except Exception as e:
            print(f"   ⚠️ Failed to insert: {e}")

    print(f"   ✅ Imported {fee_imported} fee breakdown rows")

    # Verify key projects
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)

    for code in ['24 BK-074', '23 BK-029', '25 BK-033']:
        onedrive_cursor.execute("""
            SELECT COUNT(*) as count, SUM(phase_fee_usd) as total
            FROM project_fee_breakdown
            WHERE project_code = ?
        """, (code,))
        result = onedrive_cursor.fetchone()

        if result['count'] > 0:
            print(f"✅ {code}: {result['count']} phases, ${result['total']:,.0f} total")
        else:
            print(f"⚠️  {code}: No fee breakdown found")

    # Final summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Imported {imported} projects")
    print(f"✅ Imported {fee_imported} fee breakdown rows")
    print(f"✅ OneDrive now has {len(onedrive_projects)} total projects")
    print(f"✅ Backup: {backup_path}")

    print("\nCommit changes? (yes/no): ", end="")
    response = input().strip().lower()

    if response == 'yes':
        onedrive_conn.commit()
        print("\n✅ IMPORT COMPLETE!")
    else:
        onedrive_conn.rollback()
        print("\n❌ CANCELLED - No changes made")

    desktop_conn.close()
    onedrive_conn.close()

if __name__ == '__main__':
    import_projects_and_fees()
