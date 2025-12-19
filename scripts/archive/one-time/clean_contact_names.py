#!/usr/bin/env python3
"""
Decode Base64 contact names and extract names from email format.
"""
import sqlite3
import re
from email.header import decode_header

DB_PATH = "database/bensley_master.db"

def decode_name(name_str):
    """Decode MIME encoded names"""
    if not name_str:
        return None

    # Handle =?UTF-8?B?...?= format
    if '=?' in name_str:
        try:
            decoded_parts = decode_header(name_str)
            return ''.join(
                part.decode(enc or 'utf-8') if isinstance(part, bytes) else part
                for part, enc in decoded_parts
            )
        except:
            pass

    return name_str

def extract_name_from_email(email_str):
    """Extract name from 'Name <email@domain.com>' format or derive from email"""
    if not email_str:
        return None

    # Handle nested quotes like "'Support @ Monograph'" <email>
    match = re.match(r'^"\'([^\']+)\'"?\s*<', email_str)
    if match:
        name = match.group(1).strip()
        if name:
            return name

    # Handle "Name @COMPANY" <email> or "Name" <email>
    match = re.match(r'^"([^"]+)"?\s*<', email_str)
    if match:
        name = match.group(1).strip()
        # Remove @COMPANY suffix if present
        name = re.sub(r'\s*@\w+$', '', name)
        if name and '@' not in name:
            return name

    # Match Name <email> or 'Name' <email>
    match = re.match(r'^["\']?([^"\'<]+)["\']?\s*<', email_str)
    if match:
        name = match.group(1).strip()
        if name and '@' not in name:
            return name

    # Handle <email@domain.com> - extract from email part
    match = re.match(r'^<?([^@<]+)@', email_str)
    if match:
        local_part = match.group(1).strip()
        # Convert firstname.lastname to Firstname Lastname
        if '.' in local_part and len(local_part) > 3:
            parts = local_part.split('.')
            name = ' '.join(part.capitalize() for part in parts)
            return name

    return None

def clean_contact_names():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get contacts with NULL/empty name but have email
    cursor.execute("""
        SELECT contact_id, name, email
        FROM contacts
        WHERE (name IS NULL OR name = '')
          AND email IS NOT NULL
    """)

    updates = []
    for cid, name, email in cursor.fetchall():
        new_name = extract_name_from_email(email)
        if new_name:
            updates.append((new_name, cid))

    print(f"Found {len(updates)} names to extract from email field")

    # Get Base64 encoded names
    cursor.execute("""
        SELECT contact_id, name FROM contacts
        WHERE name LIKE '%=?UTF-8%' OR name LIKE '%=?utf-8%'
    """)

    for cid, name in cursor.fetchall():
        decoded = decode_name(name)
        if decoded and decoded != name:
            updates.append((decoded, cid))
            print(f"Decoded: {name} -> {decoded}")

    if updates:
        cursor.executemany(
            "UPDATE contacts SET name = ? WHERE contact_id = ?",
            updates
        )
        conn.commit()
        print(f"\nUpdated {len(updates)} contact names")

    # Report
    cursor.execute("""
        SELECT
          SUM(CASE WHEN name IS NULL OR name = '' THEN 1 ELSE 0 END) as missing,
          COUNT(*) as total
        FROM contacts
    """)
    missing, total = cursor.fetchone()
    print(f"Contacts still missing name: {missing}/{total}")

    # Show sample of contacts still missing names
    if missing > 0:
        cursor.execute("""
            SELECT contact_id, email FROM contacts
            WHERE name IS NULL OR name = ''
            LIMIT 5
        """)
        print("\nSample contacts still missing names:")
        for row in cursor.fetchall():
            print(f"  ID {row[0]}: {row[1]}")

    conn.close()

if __name__ == "__main__":
    clean_contact_names()
