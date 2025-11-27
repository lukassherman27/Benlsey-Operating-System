#!/usr/bin/env python3
"""Add project_title column to proposals table"""
import sqlite3
import os

db_path = '/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Adding project_title column to proposals table...")

try:
    # Add project_title column as alias/copy of project_name
    cursor.execute("ALTER TABLE proposals ADD COLUMN project_title TEXT")
    print("✅ Added project_title column")

    # Copy data from project_name to project_title
    cursor.execute("UPDATE proposals SET project_title = project_name")
    count = cursor.rowcount
    print(f"✅ Copied {count} values from project_name to project_title")

    conn.commit()
    print("✅ Database updated successfully")

except Exception as e:
    if "duplicate column name" in str(e):
        print("⚠️  Column already exists, updating values...")
        cursor.execute("UPDATE proposals SET project_title = project_name WHERE project_title IS NULL OR project_title = ''")
        count = cursor.rowcount
        print(f"✅ Updated {count} null/empty values")
        conn.commit()
    else:
        print(f"❌ Error: {e}")
        conn.rollback()

conn.close()
