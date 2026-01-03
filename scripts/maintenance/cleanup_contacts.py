#!/usr/bin/env python3
"""
Cleanup Contacts Data - Issue #401
Fixes data quality issues in the contacts table:
1. Parse email addresses from angle brackets
2. Extract names from email headers
3. Decode MIME-encoded names
4. Flag internal @bensley.com contacts
5. Delete junk contacts (noreply, mailer-daemon, etc.)
6. Merge company info from contact_metadata
"""

import sqlite3
import re
import base64
import quopri
from pathlib import Path
from datetime import datetime

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "database" / "bensley_master.db"

# Junk email patterns to delete
JUNK_PATTERNS = [
    r'noreply@',
    r'no-reply@',
    r'mailer-daemon@',
    r'notifications?@',
    r'@email\.teams\.microsoft\.com',
    r'@notify\.microsoft\.com',
    r'@atlassian\.(com|net)',
    r'@dropbox\.com',
    r'@zoom\.us',
    r'@pipedrive\.com',
    r'@sproutsocial\.com',
    r'@transactional\.n8n\.io',
    r'@tm\.openai\.com',
    r'@mail\.chope\.co',
    r'flight_notification@',
    r'@e\.atlassian\.com',
    r'@po\.atlassian\.net',
    r'@em-s\.dropbox\.com',
    r'@notif\.imigrasi\.go\.id',
    r'@tdacservices\.immigration\.go\.th',
]


def decode_mime_header(encoded_str):
    """Decode MIME-encoded header values like =?UTF-8?B?base64?= or =?UTF-8?Q?quoted?="""
    if not encoded_str or '=?' not in encoded_str:
        return encoded_str

    # Pattern for MIME encoded words
    pattern = r'=\?([^?]+)\?([BQ])\?([^?]+)\?='

    def decode_match(match):
        charset = match.group(1)
        encoding = match.group(2).upper()
        encoded_text = match.group(3)

        try:
            if encoding == 'B':
                decoded_bytes = base64.b64decode(encoded_text)
            elif encoding == 'Q':
                decoded_bytes = quopri.decodestring(encoded_text.replace('_', ' '))
            else:
                return match.group(0)

            return decoded_bytes.decode(charset, errors='replace')
        except Exception:
            return match.group(0)

    return re.sub(pattern, decode_match, encoded_str, flags=re.IGNORECASE)


def parse_email_header(raw_email):
    """
    Parse email from header format like:
    - "Name" <email@domain.com>
    - Name <email@domain.com>
    - <email@domain.com>
    - email@domain.com

    Returns (clean_email, extracted_name)
    """
    if not raw_email:
        return None, None

    raw_email = raw_email.strip()

    # Pattern: "Name" <email> or Name <email>
    match = re.match(r'^"?([^"<]+)"?\s*<([^>]+)>$', raw_email)
    if match:
        name = match.group(1).strip().strip('"').strip("'")
        email = match.group(2).strip()
        return email, name

    # Pattern: <email> only
    match = re.match(r'^<([^>]+)>$', raw_email)
    if match:
        return match.group(1).strip(), None

    # Pattern: Name <email> with possible newlines
    match = re.search(r'<([^>]+)>', raw_email)
    if match:
        email = match.group(1).strip()
        name_part = raw_email[:match.start()].strip().strip('"').strip("'")
        return email, name_part if name_part else None

    # No angle brackets - assume it's just an email
    if '@' in raw_email:
        return raw_email.strip(), None

    return raw_email, None


def normalize_name(name):
    """
    Normalize a name:
    - Strip quotes
    - Decode MIME encoding
    - Convert "Last, First" to "First Last"
    - Title case
    """
    if not name:
        return None

    # Strip quotes and extra whitespace FIRST (before MIME decoding)
    name = name.strip().strip('"').strip("'").strip()

    # Decode MIME
    name = decode_mime_header(name)

    # Strip any remaining quotes
    name = name.strip().strip('"').strip("'").strip()

    # Remove email-like fragments that got mixed in
    name = re.sub(r'<[^>]+>', '', name).strip()

    # Skip if it looks like garbage
    if not name or name.startswith('=?') or len(name) < 2:
        return None

    # Convert "Last, First" to "First Last"
    if ',' in name and name.count(',') == 1:
        parts = name.split(',')
        if len(parts) == 2 and len(parts[0].strip()) > 1 and len(parts[1].strip()) > 1:
            name = f"{parts[1].strip()} {parts[0].strip()}"

    # Title case (but preserve all-caps abbreviations)
    words = name.split()
    normalized_words = []
    for word in words:
        if word.isupper() and len(word) <= 3:
            normalized_words.append(word)  # Keep abbreviations
        else:
            normalized_words.append(word.title())

    name = ' '.join(normalized_words)

    # Final validation
    if len(name) < 2 or '@' in name:
        return None

    return name


def is_junk_contact(email):
    """Check if email matches junk patterns"""
    if not email:
        return False
    email_lower = email.lower()
    for pattern in JUNK_PATTERNS:
        if re.search(pattern, email_lower, re.IGNORECASE):
            return True
    return False


def is_internal_contact(email):
    """Check if email is an internal Bensley contact"""
    if not email:
        return False
    return '@bensley.com' in email.lower() or '@bensley.co.id' in email.lower()


def extract_company_from_domain(email):
    """Extract company name from email domain"""
    if not email or '@' not in email:
        return None

    domain = email.split('@')[1].lower()

    # Skip common domains
    common_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                      'icloud.com', 'qq.com', 'vip.qq.com', '163.com', 'live.com']
    if domain in common_domains:
        return None

    # Extract company name from domain
    company = domain.split('.')[0]

    # Skip if too short or generic
    if len(company) < 3:
        return None

    return company.title()


def run_cleanup(dry_run=True):
    """Run the contacts cleanup"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"{'DRY RUN - ' if dry_run else ''}Contacts Cleanup Script")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print()

    # Get all contacts
    cursor.execute("SELECT contact_id, email, name, role, phone, notes FROM contacts")
    contacts = cursor.fetchall()
    print(f"Total contacts: {len(contacts)}")

    # Stats
    stats = {
        'parsed_emails': 0,
        'extracted_names': 0,
        'decoded_mime': 0,
        'deleted_junk': 0,
        'deleted_duplicates': 0,
        'flagged_internal': 0,
        'added_company': 0,
        'updated': 0,
    }

    # Get company info from contact_metadata
    cursor.execute("SELECT email, company FROM contact_metadata WHERE company IS NOT NULL")
    company_lookup = {row['email'].lower(): row['company'] for row in cursor.fetchall()}
    print(f"Company data from contact_metadata: {len(company_lookup)} entries")
    print()

    # Check if we need to add columns
    cursor.execute("PRAGMA table_info(contacts)")
    columns = [col['name'] for col in cursor.fetchall()]

    if 'is_internal' not in columns:
        if not dry_run:
            cursor.execute("ALTER TABLE contacts ADD COLUMN is_internal INTEGER DEFAULT 0")
            print("Added is_internal column")
        else:
            print("Would add is_internal column")

    if 'company' not in columns:
        if not dry_run:
            cursor.execute("ALTER TABLE contacts ADD COLUMN company TEXT")
            print("Added company column")
        else:
            print("Would add company column")

    print()

    # STEP 1: Parse all contacts and group by clean email
    parsed_contacts = {}  # clean_email -> list of (contact_id, raw_email, name, extracted_name, score)
    junk_to_delete = []

    for contact in contacts:
        contact_id = contact['contact_id']
        raw_email = contact['email']
        current_name = contact['name']

        # Parse email
        clean_email, extracted_name = parse_email_header(raw_email)

        if not clean_email:
            continue

        # Check if junk
        if is_junk_contact(clean_email):
            junk_to_delete.append(contact_id)
            stats['deleted_junk'] += 1
            continue

        # Normalize email for grouping
        email_key = clean_email.lower().strip()

        # Calculate a "quality score" for this record
        score = 0
        if current_name and current_name.strip():
            score += 10  # Has existing name
        if extracted_name and not extracted_name.startswith('=?'):
            score += 5   # Has valid extracted name
        if raw_email == clean_email:
            score += 2   # Already clean format
        if contact['phone']:
            score += 3   # Has phone
        if contact['notes']:
            score += 1   # Has notes

        # Normalize extracted name
        if extracted_name:
            extracted_name = normalize_name(extracted_name)

        if email_key not in parsed_contacts:
            parsed_contacts[email_key] = []

        parsed_contacts[email_key].append({
            'contact_id': contact_id,
            'raw_email': raw_email,
            'clean_email': clean_email,
            'current_name': current_name,
            'extracted_name': extracted_name,
            'score': score,
            'phone': contact['phone'],
            'notes': contact['notes'],
        })

    # STEP 2: Deduplicate - keep best record for each email
    duplicates_to_delete = []
    updates = []

    for email_key, records in parsed_contacts.items():
        # Sort by score descending - best record first
        records.sort(key=lambda x: x['score'], reverse=True)

        # Keep the first (best) record
        best = records[0]

        # Mark others as duplicates
        for dup in records[1:]:
            duplicates_to_delete.append(dup['contact_id'])
            stats['deleted_duplicates'] += 1

        # Determine best name from all records
        # Priority: existing clean name > extracted name from any record
        best_name = None

        # First try to find a good existing name
        for rec in records:
            if rec['current_name'] and rec['current_name'].strip():
                candidate = normalize_name(rec['current_name'])
                if candidate:
                    best_name = candidate
                    if rec == best:
                        stats['decoded_mime'] += 1
                    break

        # If no existing name, try extracted names
        if not best_name:
            for rec in records:
                if rec['extracted_name']:
                    best_name = rec['extracted_name']
                    stats['extracted_names'] += 1
                    break

        # Check internal
        is_internal = 1 if is_internal_contact(email_key) else 0
        if is_internal:
            stats['flagged_internal'] += 1

        # Get company
        company = company_lookup.get(email_key)
        if not company:
            company = extract_company_from_domain(email_key)
        if company:
            stats['added_company'] += 1

        # Check if email changed
        if best['clean_email'] != best['raw_email']:
            stats['parsed_emails'] += 1

        updates.append({
            'contact_id': best['contact_id'],
            'email': best['clean_email'],
            'name': best_name,
            'is_internal': is_internal,
            'company': company,
        })
        stats['updated'] += 1

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Emails to parse (angle brackets): {stats['parsed_emails']}")
    print(f"Names to extract from headers:    {stats['extracted_names']}")
    print(f"MIME-encoded names to decode:     {stats['decoded_mime']}")
    print(f"Junk contacts to delete:          {stats['deleted_junk']}")
    print(f"Duplicate contacts to delete:     {stats['deleted_duplicates']}")
    print(f"Internal contacts to flag:        {stats['flagged_internal']}")
    print(f"Company info to add:              {stats['added_company']}")
    print(f"Total unique contacts to keep:    {stats['updated']}")
    print()

    if dry_run:
        print("DRY RUN - No changes made")
        print("Run with --execute to apply changes")

        # Show some examples
        print()
        print("Sample updates:")
        for u in updates[:5]:
            print(f"  ID {u['contact_id']}: {u['email'][:40]} | {u['name'] or 'NULL'} | internal={u['is_internal']}")

        print()
        print(f"Sample junk to delete ({len(junk_to_delete)} total):")
        if junk_to_delete:
            cursor.execute(f"SELECT email FROM contacts WHERE contact_id IN ({','.join(map(str, junk_to_delete[:10]))})")
            for row in cursor.fetchall():
                print(f"  {row['email'][:60]}")

        print()
        print(f"Sample duplicates to delete ({len(duplicates_to_delete)} total):")
        if duplicates_to_delete:
            cursor.execute(f"SELECT email FROM contacts WHERE contact_id IN ({','.join(map(str, duplicates_to_delete[:10]))})")
            for row in cursor.fetchall():
                print(f"  {row['email'][:60]}")
    else:
        # Apply updates
        print("Applying changes...")

        # Delete junk first
        if junk_to_delete:
            placeholders = ','.join(['?' for _ in junk_to_delete])
            cursor.execute(f"DELETE FROM contacts WHERE contact_id IN ({placeholders})", junk_to_delete)
            print(f"Deleted {len(junk_to_delete)} junk contacts")

        # Delete duplicates
        if duplicates_to_delete:
            placeholders = ','.join(['?' for _ in duplicates_to_delete])
            cursor.execute(f"DELETE FROM contacts WHERE contact_id IN ({placeholders})", duplicates_to_delete)
            print(f"Deleted {len(duplicates_to_delete)} duplicate contacts")

        # Update remaining contacts
        for u in updates:
            cursor.execute("""
                UPDATE contacts
                SET email = ?, name = ?, is_internal = ?, company = ?
                WHERE contact_id = ?
            """, (u['email'], u['name'], u['is_internal'], u['company'], u['contact_id']))

        conn.commit()
        print(f"Updated {len(updates)} contacts")
        print("DONE!")

    conn.close()


if __name__ == '__main__':
    import sys
    dry_run = '--execute' not in sys.argv
    run_cleanup(dry_run=dry_run)
