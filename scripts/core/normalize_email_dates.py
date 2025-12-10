#!/usr/bin/env python3
"""
Normalize email dates to ISO format for proper sorting.
Run from: /Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System
"""
import sqlite3
from datetime import datetime
from email.utils import parsedate_to_datetime
import re

DB_PATH = "database/bensley_master.db"

def parse_date(date_str):
    """Parse various date formats to datetime"""
    if not date_str:
        return None

    # Already ISO format: 2025-09-08 19:17:45+07:00
    if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', date_str):
        return date_str  # Already good

    # ISO-T format: 2025-11-25T07:44:45+00:00
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', date_str):
        return date_str.replace('T', ' ')

    # RFC 2822: Wed, 20 Aug 2025 14:28:13 +0000
    try:
        dt = parsedate_to_datetime(date_str)
        # Format with timezone offset
        tz_offset = dt.strftime('%z')
        if tz_offset:
            # Insert colon in timezone: +0000 -> +00:00
            tz_offset = tz_offset[:3] + ':' + tz_offset[3:]
        return dt.strftime('%Y-%m-%d %H:%M:%S') + tz_offset
    except:
        pass

    return None

def normalize_dates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all emails with non-ISO dates
    cursor.execute("""
        SELECT email_id, date FROM emails
        WHERE date IS NOT NULL
          AND date NOT LIKE '____-__-__ %'
    """)

    updates = []
    errors = []

    for email_id, date_str in cursor.fetchall():
        normalized = parse_date(date_str)
        if normalized and normalized != date_str:
            updates.append((normalized, email_id))
        elif not normalized:
            errors.append((email_id, date_str))

    print(f"Found {len(updates)} dates to normalize")
    print(f"Found {len(errors)} unparseable dates")

    if errors:
        print("\nUnparseable dates:")
        for eid, d in errors[:10]:
            print(f"  {eid}: {d}")

    # Apply updates
    if updates:
        cursor.executemany("UPDATE emails SET date = ? WHERE email_id = ?", updates)
        conn.commit()
        print(f"\nUpdated {len(updates)} email dates")

    # Verify
    cursor.execute("""
        SELECT
          CASE
            WHEN date LIKE '____-__-__ %' THEN 'ISO'
            ELSE 'Other'
          END as format,
          COUNT(*)
        FROM emails GROUP BY format
    """)
    print("\nDate formats after normalization:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()

if __name__ == "__main__":
    normalize_dates()
