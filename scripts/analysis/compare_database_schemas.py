#!/usr/bin/env python3
"""
Compare database schemas to determine which has better architecture
"""

import sqlite3
import os

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"

def get_all_tables(db_path):
    """Get all table names"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_table_schema(db_path, table_name):
    """Get CREATE TABLE statement for a table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_table_columns(db_path, table_name):
    """Get column info for a table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    conn.close()
    return columns

def get_indexes(db_path):
    """Get all indexes"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name")
    indexes = cursor.fetchall()
    conn.close()
    return indexes

def main():
    print("="*120)
    print("DATABASE SCHEMA COMPARISON")
    print("="*120)

    # Get tables from both databases
    print("\n[1/5] Comparing tables...")
    desktop_tables = set(get_all_tables(DESKTOP_DB))
    onedrive_tables = set(get_all_tables(ONEDRIVE_DB))

    print(f"  Desktop has {len(desktop_tables)} tables")
    print(f"  OneDrive has {len(onedrive_tables)} tables")

    only_desktop = desktop_tables - onedrive_tables
    only_onedrive = onedrive_tables - desktop_tables
    common_tables = desktop_tables & onedrive_tables

    if only_desktop:
        print(f"\n  ✅ Tables ONLY in Desktop ({len(only_desktop)}):")
        for table in sorted(only_desktop):
            print(f"    - {table}")

    if only_onedrive:
        print(f"\n  ✅ Tables ONLY in OneDrive ({len(only_onedrive)}):")
        for table in sorted(only_onedrive):
            print(f"    - {table}")

    print(f"\n  Tables in both: {len(common_tables)}")

    # Compare key table schemas
    print("\n[2/5] Comparing schemas for key tables...")
    key_tables = ['emails', 'invoices', 'projects', 'proposals']

    schema_differences = []
    for table in key_tables:
        if table in common_tables:
            desktop_cols = get_table_columns(DESKTOP_DB, table)
            onedrive_cols = get_table_columns(ONEDRIVE_DB, table)

            desktop_col_names = set([col[1] for col in desktop_cols])
            onedrive_col_names = set([col[1] for col in onedrive_cols])

            only_desktop_cols = desktop_col_names - onedrive_col_names
            only_onedrive_cols = onedrive_col_names - desktop_col_names

            if only_desktop_cols or only_onedrive_cols:
                schema_differences.append({
                    'table': table,
                    'only_desktop': only_desktop_cols,
                    'only_onedrive': only_onedrive_cols
                })

    if schema_differences:
        print("\n  Schema differences found:")
        for diff in schema_differences:
            print(f"\n  Table: {diff['table']}")
            if diff['only_desktop']:
                print(f"    ✅ Columns ONLY in Desktop: {', '.join(diff['only_desktop'])}")
            if diff['only_onedrive']:
                print(f"    ✅ Columns ONLY in OneDrive: {', '.join(diff['only_onedrive'])}")
    else:
        print("  No schema differences in key tables")

    # Compare indexes
    print("\n[3/5] Comparing indexes...")
    desktop_indexes = get_indexes(DESKTOP_DB)
    onedrive_indexes = get_indexes(ONEDRIVE_DB)

    print(f"  Desktop has {len(desktop_indexes)} indexes")
    print(f"  OneDrive has {len(onedrive_indexes)} indexes")

    desktop_idx_names = set([idx[0] for idx in desktop_indexes])
    onedrive_idx_names = set([idx[0] for idx in onedrive_indexes])

    only_desktop_idx = desktop_idx_names - onedrive_idx_names
    only_onedrive_idx = onedrive_idx_names - desktop_idx_names

    if only_desktop_idx:
        print(f"\n  ✅ Indexes ONLY in Desktop ({len(only_desktop_idx)}):")
        for idx in sorted(only_desktop_idx):
            print(f"    - {idx}")

    if only_onedrive_idx:
        print(f"\n  ✅ Indexes ONLY in OneDrive ({len(only_onedrive_idx)}):")
        for idx in sorted(only_onedrive_idx):
            print(f"    - {idx}")

    # Check for migration tracking
    print("\n[4/5] Checking migration tracking...")

    desktop_has_migrations = 'schema_migrations' in desktop_tables or 'migrations' in desktop_tables
    onedrive_has_migrations = 'schema_migrations' in onedrive_tables or 'migrations' in onedrive_tables

    print(f"  Desktop has migration tracking: {desktop_has_migrations}")
    print(f"  OneDrive has migration tracking: {onedrive_has_migrations}")

    # Detailed comparison of emails table (key for date_normalized)
    print("\n[5/5] Detailed comparison of 'emails' table...")

    if 'emails' in common_tables:
        desktop_emails_cols = get_table_columns(DESKTOP_DB, 'emails')
        onedrive_emails_cols = get_table_columns(ONEDRIVE_DB, 'emails')

        print(f"\n  Desktop 'emails' columns ({len(desktop_emails_cols)}):")
        for col in desktop_emails_cols:
            print(f"    {col[1]:<30} {col[2]:<15}")

        print(f"\n  OneDrive 'emails' columns ({len(onedrive_emails_cols)}):")
        for col in onedrive_emails_cols:
            print(f"    {col[1]:<30} {col[2]:<15}")

    # Architecture assessment
    print("\n" + "="*120)
    print("ARCHITECTURE ASSESSMENT")
    print("="*120)

    score_desktop = 0
    score_onedrive = 0

    # More tables = more features
    if len(desktop_tables) > len(onedrive_tables):
        score_desktop += 1
        print(f"✅ Desktop: Has more tables ({len(desktop_tables)} vs {len(onedrive_tables)})")
    else:
        score_onedrive += 1
        print(f"✅ OneDrive: Has more tables ({len(onedrive_tables)} vs {len(desktop_tables)})")

    # More indexes = better performance
    if len(desktop_indexes) > len(onedrive_indexes):
        score_desktop += 1
        print(f"✅ Desktop: Has more indexes ({len(desktop_indexes)} vs {len(onedrive_indexes)})")
    else:
        score_onedrive += 1
        print(f"✅ OneDrive: Has more indexes ({len(onedrive_indexes)} vs {len(desktop_indexes)})")

    # Has date_normalized
    desktop_has_date_norm = 'date_normalized' in [col[1] for col in get_table_columns(DESKTOP_DB, 'emails')]
    onedrive_has_date_norm = 'date_normalized' in [col[1] for col in get_table_columns(ONEDRIVE_DB, 'emails')]

    if onedrive_has_date_norm and not desktop_has_date_norm:
        score_onedrive += 2  # This is important
        print(f"✅ OneDrive: Has date_normalized column (CRITICAL FIX)")
    elif desktop_has_date_norm and not onedrive_has_date_norm:
        score_desktop += 2
        print(f"✅ Desktop: Has date_normalized column (CRITICAL FIX)")

    # Check for newer tables
    if only_onedrive:
        score_onedrive += len(only_onedrive)
        print(f"✅ OneDrive: Has {len(only_onedrive)} additional tables (newer features)")

    if only_desktop:
        score_desktop += len(only_desktop)
        print(f"✅ Desktop: Has {len(only_desktop)} additional tables (newer features)")

    print(f"\n{'='*120}")
    print(f"FINAL ARCHITECTURE SCORE")
    print(f"{'='*120}")
    print(f"Desktop: {score_desktop} points")
    print(f"OneDrive: {score_onedrive} points")

    if score_onedrive > score_desktop:
        print(f"\n🏆 WINNER: OneDrive has BETTER ARCHITECTURE")
        print(f"\nRecommendation:")
        print(f"  • Use OneDrive database as the master (better schema)")
        print(f"  • Migrate invoice/project DATA from Desktop → OneDrive")
        print(f"  • Keep OneDrive's schema and structure")
    else:
        print(f"\n🏆 WINNER: Desktop has BETTER ARCHITECTURE")
        print(f"\nRecommendation:")
        print(f"  • Use Desktop database as the master (better schema)")
        print(f"  • Migrate email DATA and schema updates from OneDrive → Desktop")
        print(f"  • Apply OneDrive's schema improvements to Desktop")

    print("="*120)

if __name__ == '__main__':
    main()
