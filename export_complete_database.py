#!/usr/bin/env python3
"""
Complete Database Export - Shows EVERYTHING in the database
Exports all tables with all data to a readable text file
"""

import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = os.path.expanduser("~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db")
OUTPUT_PATH = os.path.expanduser("~/Desktop/BENSLEY_DATABASE_COMPLETE_EXPORT.txt")

def export_database():
    """Export complete database contents to text file"""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        # Header
        f.write("=" * 100 + "\n")
        f.write("BENSLEY MASTER DATABASE - COMPLETE EXPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 100 + "\n\n")

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        f.write(f"TOTAL TABLES: {len(tables)}\n")
        f.write(f"Tables: {', '.join(tables)}\n\n")

        # Export each table
        for table in tables:
            print(f"Exporting table: {table}")

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]

            # Get column info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]

            # Write table header
            f.write("\n" + "=" * 100 + "\n")
            f.write(f"TABLE: {table.upper()}\n")
            f.write(f"Rows: {row_count}\n")
            f.write(f"Columns: {', '.join(col_names)}\n")
            f.write("=" * 100 + "\n\n")

            if row_count == 0:
                f.write("(Empty table)\n\n")
                continue

            # Get all data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()

            # Write each row
            for i, row in enumerate(rows, 1):
                f.write(f"\n--- Record {i} of {row_count} ---\n")

                for col_name in col_names:
                    value = row[col_name]

                    # Format value
                    if value is None:
                        value_str = "(NULL)"
                    elif isinstance(value, str) and len(value) > 200:
                        value_str = value[:200] + f"... ({len(value)} chars total)"
                    else:
                        value_str = str(value)

                    f.write(f"{col_name}: {value_str}\n")

                f.write("\n")

        # Summary Statistics
        f.write("\n" + "=" * 100 + "\n")
        f.write("SUMMARY STATISTICS\n")
        f.write("=" * 100 + "\n\n")

        # Check if proposals table has data
        cursor.execute("SELECT COUNT(*) as count FROM proposals")
        proposals_count = cursor.fetchone()['count']

        if proposals_count > 0:
            cursor.execute("""
                SELECT
                    status,
                    COUNT(*) as count
                FROM proposals
                GROUP BY status
                ORDER BY count DESC
            """)

            f.write("PROPOSALS TABLE (Original Import):\n")
            f.write("-" * 80 + "\n")
            for row in cursor.fetchall():
                status = row['status'] or 'unknown'
                count = row['count']
                f.write(f"{status.upper()}: {count}\n")
            f.write("\n")

        # Check if projects table exists and has data
        cursor.execute("SELECT COUNT(*) as count FROM projects")
        projects_count = cursor.fetchone()['count']

        if projects_count > 0:
            cursor.execute("""
                SELECT
                    status,
                    is_active_project,
                    COUNT(*) as count,
                    AVG(health_score) as avg_health
                FROM projects
                GROUP BY status, is_active_project
                ORDER BY is_active_project DESC, status
            """)

            f.write("PROJECTS TABLE (Enhanced Tracking):\n")
            f.write("-" * 80 + "\n")
            for row in cursor.fetchall():
                status = row['status'] or 'unknown'
                is_active = 'ACTIVE PROJECT' if row['is_active_project'] == 1 else 'PROPOSAL'
                count = row['count']
                avg_health = row['avg_health'] or 0
                f.write(f"{is_active} - {status.upper()}: {count} (Avg Health: {avg_health:.1f}%)\n")
            f.write("\n")

        # Email breakdown
        cursor.execute("""
            SELECT
                folder,
                COUNT(*) as count
            FROM emails
            GROUP BY folder
        """)

        f.write("EMAILS BREAKDOWN:\n")
        f.write("-" * 80 + "\n")
        for row in cursor.fetchall():
            f.write(f"{row['folder']}: {row['count']} emails\n")

        f.write("\n")

        # Email content categories
        cursor.execute("""
            SELECT
                category,
                COUNT(*) as count,
                AVG(importance_score) as avg_importance
            FROM email_content
            GROUP BY category
            ORDER BY count DESC
        """)

        f.write("EMAIL CATEGORIES:\n")
        f.write("-" * 80 + "\n")
        for row in cursor.fetchall():
            category = row['category'] or 'uncategorized'
            count = row['count']
            avg_imp = row['avg_importance'] or 0
            f.write(f"{category}: {count} (Avg Importance: {avg_imp:.1f}%)\n")

        f.write("\n")

        # Document breakdown
        cursor.execute("""
            SELECT
                document_type,
                COUNT(*) as count
            FROM documents
            WHERE document_type IS NOT NULL
            GROUP BY document_type
            ORDER BY count DESC
        """)

        f.write("DOCUMENTS BY TYPE:\n")
        f.write("-" * 80 + "\n")
        for row in cursor.fetchall():
            f.write(f"{row['document_type']}: {row['count']} documents\n")

        f.write("\n")

        # Database size
        db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
        f.write(f"DATABASE FILE SIZE: {db_size_mb:.2f} MB\n")

        f.write("\n" + "=" * 100 + "\n")
        f.write("END OF EXPORT\n")
        f.write("=" * 100 + "\n")

    conn.close()

    print(f"\n✅ Complete database export saved to: {OUTPUT_PATH}")
    print(f"📊 File size: {os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB")

if __name__ == "__main__":
    print("Starting complete database export...")
    export_database()
    print("\n✅ Done!")
