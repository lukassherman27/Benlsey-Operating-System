#!/usr/bin/env python3
"""
Backfill Email Direction Script

Classifies all emails based on sender/recipient domains:
- internal_to_internal: Bensley staff to Bensley staff
- internal_to_external: Bensley staff to external (clients, vendors, etc.)
- external_to_internal: External to Bensley staff
- external_to_external: External forwarded/CC'd (rare)

Usage:
    python scripts/core/backfill_email_direction.py
    python scripts/core/backfill_email_direction.py --limit 500
    python scripts/core/backfill_email_direction.py --dry-run
"""

import os
import sys
import sqlite3
import re
import argparse
from typing import Optional, List, Tuple, Set

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

# Internal Bensley domains
INTERNAL_DOMAINS = {
    'bensley.com',
    'bensleydesign.com',
    'bensley.co.th',
    'bensley.id',
    'bensley.co.id',
}


def extract_email_address(sender: str) -> str:
    """
    Extract clean email address from RFC 5322 format.
    Handles: "Name <email@domain.com>" or just "email@domain.com"
    """
    if not sender:
        return ""

    # Try to extract from angle brackets
    match = re.search(r'<([^>]+@[^>]+)>', sender)
    if match:
        return match.group(1).lower().strip()

    # Try to find email directly
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
    if match:
        return match.group(0).lower().strip()

    return sender.lower().strip()


def extract_domain(email: str) -> Optional[str]:
    """Extract domain from email address."""
    clean_email = extract_email_address(email)
    if '@' not in clean_email:
        return None
    return clean_email.split('@')[1].lower()


def is_internal_domain(domain: Optional[str]) -> bool:
    """Check if domain is a Bensley internal domain."""
    if not domain:
        return False
    return domain in INTERNAL_DOMAINS


def extract_all_emails(recipients: str) -> List[str]:
    """Extract all email addresses from a comma/semicolon separated string."""
    if not recipients:
        return []

    emails = []
    # Split by comma or semicolon
    for part in re.split(r'[,;]', recipients):
        email = extract_email_address(part.strip())
        if email and '@' in email:
            emails.append(email)
    return emails


def classify_email_direction(
    sender_email: str,
    recipient_emails: str
) -> Tuple[str, bool]:
    """
    Classify email direction and whether it's purely internal.

    Returns:
        (direction, is_purely_internal)
        - direction: one of 'internal_to_internal', 'internal_to_external',
                     'external_to_internal', 'external_to_external'
        - is_purely_internal: True if ALL parties are internal
    """
    sender = extract_email_address(sender_email or "")
    sender_domain = extract_domain(sender)
    sender_internal = is_internal_domain(sender_domain)

    recipients = extract_all_emails(recipient_emails or "")
    recipient_domains = [extract_domain(r) for r in recipients]

    if not recipients:
        # No recipients - classify based on sender only
        if sender_internal:
            return 'internal_to_internal', True
        else:
            return 'external_to_internal', False

    # Check if ALL recipients are internal
    all_recipients_internal = all(is_internal_domain(d) for d in recipient_domains if d)
    any_recipient_internal = any(is_internal_domain(d) for d in recipient_domains if d)

    if sender_internal:
        if all_recipients_internal:
            return 'internal_to_internal', True
        else:
            return 'internal_to_external', False
    else:
        if any_recipient_internal:
            return 'external_to_internal', False
        else:
            return 'external_to_external', False


def backfill_email_directions(
    db_path: str = DB_PATH,
    limit: Optional[int] = None,
    dry_run: bool = False
) -> dict:
    """
    Backfill email_direction and is_purely_internal for all emails.

    Args:
        db_path: Path to SQLite database
        limit: Optional limit on number of emails to process
        dry_run: If True, don't actually update the database

    Returns:
        Stats dict with counts by direction
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get emails that need classification
    query = """
        SELECT email_id, sender_email, recipient_emails
        FROM emails
        WHERE email_direction IS NULL OR email_direction = ''
        ORDER BY date DESC
    """
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    emails = cursor.fetchall()

    print(f"Found {len(emails)} emails to classify")

    stats = {
        'total': len(emails),
        'internal_to_internal': 0,
        'internal_to_external': 0,
        'external_to_internal': 0,
        'external_to_external': 0,
        'purely_internal': 0,
    }

    updates = []
    for email in emails:
        direction, is_purely_internal = classify_email_direction(
            email['sender_email'],
            email['recipient_emails']
        )

        stats[direction] += 1
        if is_purely_internal:
            stats['purely_internal'] += 1

        updates.append((
            direction,
            1 if is_purely_internal else 0,
            email['email_id']
        ))

    if not dry_run:
        print("Applying updates...")
        cursor.executemany("""
            UPDATE emails
            SET email_direction = ?, is_purely_internal = ?
            WHERE email_id = ?
        """, updates)
        conn.commit()
        print(f"Updated {len(updates)} emails")
    else:
        print("DRY RUN - no updates applied")

    conn.close()
    return stats


def main():
    parser = argparse.ArgumentParser(description='Backfill email direction classification')
    parser.add_argument('--limit', type=int, help='Limit number of emails to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--db', type=str, default=DB_PATH, help='Database path')

    args = parser.parse_args()

    print("=" * 60)
    print("Email Direction Backfill")
    print("=" * 60)
    print(f"Database: {args.db}")
    print(f"Internal domains: {', '.join(sorted(INTERNAL_DOMAINS))}")
    print()

    stats = backfill_email_directions(
        db_path=args.db,
        limit=args.limit,
        dry_run=args.dry_run
    )

    print()
    print("=" * 60)
    print("Results:")
    print("=" * 60)
    print(f"Total emails:            {stats['total']}")
    print(f"Internal to Internal:    {stats['internal_to_internal']}")
    print(f"Internal to External:    {stats['internal_to_external']}")
    print(f"External to Internal:    {stats['external_to_internal']}")
    print(f"External to External:    {stats['external_to_external']}")
    print(f"Purely Internal:         {stats['purely_internal']}")
    print()

    if not args.dry_run:
        print("Done! All emails have been classified.")


if __name__ == '__main__':
    main()
