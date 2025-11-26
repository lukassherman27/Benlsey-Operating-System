#!/usr/bin/env python3
"""
Backfill Email Folders

Fix the 2,960 emails with NULL folder by inferring folder from sender:
- If sender is from @bensley.com → "Sent"
- Otherwise → "INBOX"

This is a best-guess approach since we don't have the original folder info.
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("=" * 80)
    print("BACKFILLING EMAIL FOLDERS")
    print("=" * 80)

    db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count emails with NULL folder
    cursor.execute("SELECT COUNT(*) FROM emails WHERE folder IS NULL OR folder = ''")
    null_count = cursor.fetchone()[0]

    print(f"\n📊 Found {null_count:,} emails with NULL/empty folder")

    if null_count == 0:
        print("✅ No emails need backfilling!")
        return

    # Backfill strategy: Infer from sender domain
    print("\n🔄 Backfilling folders based on sender domain...")
    print("   Logic: @bensley.com/@bensley.co.id = Sent, Others = INBOX")

    # Update Sent folder (emails FROM Bensley)
    cursor.execute("""
        UPDATE emails
        SET folder = 'Sent'
        WHERE (folder IS NULL OR folder = '')
          AND (sender_email LIKE '%@bensley.com%' OR sender_email LIKE '%@bensley.co.id%')
    """)
    sent_updated = cursor.rowcount

    # Update INBOX folder (emails TO Bensley)
    cursor.execute("""
        UPDATE emails
        SET folder = 'INBOX'
        WHERE (folder IS NULL OR folder = '')
    """)
    inbox_updated = cursor.rowcount

    conn.commit()

    # Verify results
    cursor.execute("""
        SELECT folder, COUNT(*) as count
        FROM emails
        GROUP BY folder
        ORDER BY count DESC
    """)
    results = cursor.fetchall()

    print(f"\n✅ Backfill complete!")
    print(f"   Sent: {sent_updated:,} emails")
    print(f"   INBOX: {inbox_updated:,} emails")

    print(f"\n📊 Final folder distribution:")
    for folder, count in results:
        folder_name = folder if folder else "(null)"
        print(f"   {folder_name}: {count:,} emails")

    conn.close()

    print("\n✅ Done! Future imports will save folder correctly.\n")

if __name__ == '__main__':
    main()
