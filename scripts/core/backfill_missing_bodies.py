#!/usr/bin/env python3
"""
Backfill Missing Email Bodies

This script re-fetches emails that have empty body_full fields from IMAP
and updates them in the database using improved HTML extraction logic.

Usage:
    python scripts/core/backfill_missing_bodies.py

Reads credentials from .env file automatically.

Created: 2025-12-07
"""

import imaplib
import email
from email.header import decode_header
import sqlite3
import os
import sys
import re
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
load_dotenv(PROJECT_ROOT / '.env')

# Configuration
DB_PATH = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'database' / 'bensley_master.db'))

# IMAP Configuration
IMAP_SERVER = os.getenv('EMAIL_SERVER', 'tmail.bensley.com')
IMAP_PORT = int(os.getenv('EMAIL_PORT', '993'))
EMAIL_USER = os.getenv('EMAIL_USERNAME', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')

# Rate limiting
DELAY_BETWEEN_EMAILS = 0.3  # 300ms delay


def log(message: str, level: str = 'INFO'):
    """Log to stdout"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")


def get_email_body(msg) -> str:
    """Extract email body - prefer plain text, fall back to HTML"""
    body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    text = payload.decode('utf-8', errors='ignore')
                    if content_type == 'text/plain' and not body:
                        body = text
                    elif content_type == 'text/html' and not html_body:
                        html_body = text
            except Exception:
                pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        except Exception:
            pass

    # Fall back to HTML if no plain text
    if not body and html_body:
        body = re.sub(r'<style[^>]*>.*?</style>', '', html_body, flags=re.DOTALL)
        body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
        body = re.sub(r'<[^>]+>', ' ', body)
        body = re.sub(r'&nbsp;', ' ', body)
        body = re.sub(r'\s+', ' ', body).strip()

    return body


def search_email_by_message_id(imap_conn, folder: str, message_id: str):
    """Search for an email by Message-ID in a folder"""
    try:
        status, _ = imap_conn.select(f'"{folder}"', readonly=True)
        if status != 'OK':
            return None

        # Search by Message-ID header
        # Clean up message_id - remove angle brackets for search
        clean_id = message_id.strip('<>').replace('"', '\\"')

        # Try HEADER search
        status, messages = imap_conn.search(None, f'HEADER Message-ID "<{clean_id}>"')
        if status == 'OK' and messages[0]:
            email_ids = messages[0].split()
            if email_ids:
                return email_ids[0]

        # Fallback: try without angle brackets
        status, messages = imap_conn.search(None, f'HEADER Message-ID "{clean_id}"')
        if status == 'OK' and messages[0]:
            email_ids = messages[0].split()
            if email_ids:
                return email_ids[0]

    except Exception as e:
        log(f"Search error in {folder}: {e}", 'WARNING')

    return None


def fetch_and_extract_body(imap_conn, email_id) -> str:
    """Fetch an email by ID and extract its body"""
    try:
        status, msg_data = imap_conn.fetch(email_id, '(RFC822)')
        if status != 'OK':
            return ""

        msg = email.message_from_bytes(msg_data[0][1])
        return get_email_body(msg)
    except Exception as e:
        log(f"Fetch error: {e}", 'WARNING')
        return ""


def run_backfill():
    """Run the backfill process"""
    log("=" * 60)
    log("BACKFILL MISSING EMAIL BODIES")
    log("=" * 60)

    # Check credentials
    if not EMAIL_USER or not EMAIL_PASSWORD:
        log("EMAIL_USERNAME and EMAIL_PASSWORD environment variables required", 'ERROR')
        log("Set them before running:")
        log("  export EMAIL_USERNAME='your@email.com'")
        log("  export EMAIL_PASSWORD='your_password'")
        return

    # Connect to database
    try:
        db_conn = sqlite3.connect(DB_PATH)
        db_cursor = db_conn.cursor()
        log(f"Connected to database: {DB_PATH}")
    except Exception as e:
        log(f"Database connection failed: {e}", 'ERROR')
        return

    # Get emails with missing bodies
    db_cursor.execute("""
        SELECT email_id, message_id, subject, folder
        FROM emails
        WHERE body_full IS NULL OR body_full = ''
        ORDER BY email_id DESC
    """)
    missing_emails = db_cursor.fetchall()

    log(f"Found {len(missing_emails)} emails with missing bodies")

    if not missing_emails:
        log("No emails to backfill!")
        db_conn.close()
        return

    # Connect to IMAP
    try:
        log(f"Connecting to IMAP: {IMAP_SERVER}:{IMAP_PORT}")
        imap_conn = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        imap_conn.login(EMAIL_USER, EMAIL_PASSWORD)
        log("IMAP connection successful")
    except Exception as e:
        log(f"IMAP connection failed: {e}", 'ERROR')
        db_conn.close()
        return

    # Process each email
    stats = {'updated': 0, 'not_found': 0, 'still_empty': 0, 'errors': 0}

    for i, (email_id, message_id, subject, folder) in enumerate(missing_emails, 1):
        try:
            # Show progress
            short_subject = (subject[:40] + '...') if subject and len(subject) > 40 else subject
            log(f"[{i}/{len(missing_emails)}] Processing: {short_subject}")

            # Determine which folder to search
            folders_to_try = [folder] if folder else ['Sent', 'INBOX']

            imap_email_id = None
            search_folder = None

            for try_folder in folders_to_try:
                imap_email_id = search_email_by_message_id(imap_conn, try_folder, message_id)
                if imap_email_id:
                    search_folder = try_folder
                    break

            if not imap_email_id:
                log(f"  -> Not found in IMAP", 'WARNING')
                stats['not_found'] += 1
                continue

            # Select the folder and fetch body
            imap_conn.select(f'"{search_folder}"', readonly=True)
            body = fetch_and_extract_body(imap_conn, imap_email_id)

            if not body:
                log(f"  -> Body still empty after extraction", 'WARNING')
                stats['still_empty'] += 1
                continue

            # Update database
            snippet = body[:500] if body else ""
            db_cursor.execute("""
                UPDATE emails
                SET body_full = ?, snippet = ?
                WHERE email_id = ?
            """, (body, snippet, email_id))

            stats['updated'] += 1
            log(f"  -> Updated ({len(body)} chars)")

            # Commit every 10 emails
            if i % 10 == 0:
                db_conn.commit()

            # Rate limiting
            time.sleep(DELAY_BETWEEN_EMAILS)

        except Exception as e:
            log(f"  -> Error: {e}", 'ERROR')
            stats['errors'] += 1
            continue

    # Final commit
    db_conn.commit()

    # Close connections
    try:
        imap_conn.close()
        imap_conn.logout()
    except:
        pass

    db_conn.close()

    # Summary
    log("\n" + "=" * 60)
    log("BACKFILL COMPLETE")
    log("=" * 60)
    log(f"Updated:     {stats['updated']}")
    log(f"Not found:   {stats['not_found']}")
    log(f"Still empty: {stats['still_empty']}")
    log(f"Errors:      {stats['errors']}")


if __name__ == '__main__':
    run_backfill()
