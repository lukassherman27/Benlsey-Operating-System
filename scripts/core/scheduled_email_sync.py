#!/usr/bin/env python3
"""
Scheduled Email Sync - Import new emails and run project linker

This script:
1. Connects to IMAP server
2. Imports new emails (skips duplicates by message_id)
3. Runs the fixed email_project_linker
4. Logs results

Designed for cron/scheduled execution:
    */15 * * * * cd /path/to/project && python scripts/core/scheduled_email_sync.py

Environment Variables Required:
    DATABASE_PATH - Path to SQLite database
    EMAIL_SERVER - IMAP server hostname
    EMAIL_PORT - IMAP port (default 993)
    EMAIL_USERNAME - Email username
    EMAIL_PASSWORD - Email password

Created: 2025-11-30
"""

import imaplib
import email
from email.header import decode_header
import sqlite3
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the linker
from scripts.core.email_project_linker import EmailProjectLinker

# Import the orchestrator for categorization and suggestion generation
from backend.services.email_orchestrator import EmailOrchestrator

# Configuration
DB_PATH = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'database' / 'bensley_master.db'))
LOG_PATH = str(PROJECT_ROOT / 'logs' / 'email_sync.log')

# IMAP Configuration
IMAP_SERVER = os.getenv('EMAIL_SERVER', 'tmail.bensley.com')
IMAP_PORT = int(os.getenv('EMAIL_PORT', '993'))
EMAIL_USER = os.getenv('EMAIL_USERNAME', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')

# Safety settings
MAX_EMAILS_PER_RUN = int(os.getenv('MAX_EMAILS_PER_RUN', '100'))
DELAY_BETWEEN_EMAILS = 0.2  # 200ms delay
FOLDERS_TO_SYNC = ['INBOX', 'Sent']


def log(message: str, level: str = 'INFO'):
    """Log to file and stdout"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)

    # Ensure log directory exists
    log_dir = Path(LOG_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    with open(LOG_PATH, 'a') as f:
        f.write(log_line + '\n')


def decode_header_value(value) -> str:
    """Decode email header value"""
    if value is None:
        return ""
    decoded = decode_header(value)
    parts = []
    for content, encoding in decoded:
        if isinstance(content, bytes):
            parts.append(content.decode(encoding or 'utf-8', errors='ignore'))
        else:
            parts.append(str(content))
    return ' '.join(parts)


def get_email_body(msg) -> str:
    """Extract email body"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/plain':
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
    return body


def sync_folder(imap_conn, folder: str, db_cursor, db_conn) -> dict:
    """Sync emails from a single folder"""
    stats = {'imported': 0, 'skipped': 0, 'errors': 0}

    try:
        # Select folder
        status, _ = imap_conn.select(f'"{folder}"', readonly=True)
        if status != 'OK':
            log(f"Failed to select folder: {folder}", 'ERROR')
            return stats

        # Search for all emails
        status, messages = imap_conn.search(None, 'ALL')
        if status != 'OK':
            log(f"Failed to search folder: {folder}", 'ERROR')
            return stats

        email_ids = messages[0].split()
        total = len(email_ids)
        log(f"  Found {total} emails in {folder}")

        # Limit for safety
        if total > MAX_EMAILS_PER_RUN:
            email_ids = email_ids[-MAX_EMAILS_PER_RUN:]  # Most recent
            log(f"  Limiting to last {MAX_EMAILS_PER_RUN} emails")

        for i, email_id in enumerate(email_ids, 1):
            try:
                # Fetch email
                status, msg_data = imap_conn.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    stats['errors'] += 1
                    continue

                msg = email.message_from_bytes(msg_data[0][1])

                # Extract fields
                message_id = msg.get('Message-ID', f"<sync-{email_id.decode()}-{datetime.now().timestamp()}>")
                subject = decode_header_value(msg.get('Subject', ''))
                sender = decode_header_value(msg.get('From', ''))
                recipients = decode_header_value(msg.get('To', ''))
                date_str = msg.get('Date', '')
                thread_id = msg.get('References', '') or msg.get('In-Reply-To', '')

                # Parse date
                try:
                    email_date = email.utils.parsedate_to_datetime(date_str)
                except:
                    email_date = datetime.now()

                # Check if already exists
                db_cursor.execute("SELECT email_id FROM emails WHERE message_id = ?", (message_id,))
                if db_cursor.fetchone():
                    stats['skipped'] += 1
                    continue

                # Get body
                body = get_email_body(msg)
                snippet = body[:500] if body else ""

                # Insert email
                db_cursor.execute("""
                    INSERT INTO emails
                    (message_id, sender_email, recipient_emails, subject, snippet, body_full,
                     date_normalized, processed, folder, thread_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """, (
                    message_id, sender, recipients, subject, snippet, body,
                    email_date.isoformat(), folder, thread_id
                ))

                stats['imported'] += 1

                # Rate limiting
                time.sleep(DELAY_BETWEEN_EMAILS)

                # Progress logging
                if i % 25 == 0:
                    log(f"  Progress: {i}/{len(email_ids)} ({stats['imported']} new)")
                    db_conn.commit()

            except Exception as e:
                log(f"  Error processing email {i}: {e}", 'ERROR')
                stats['errors'] += 1
                continue

        db_conn.commit()

    except Exception as e:
        log(f"Error syncing folder {folder}: {e}", 'ERROR')

    return stats


def run_sync():
    """Run the full sync process"""
    log("=" * 60)
    log("BENSLEY EMAIL SYNC - Starting")
    log("=" * 60)

    # Check credentials
    if not EMAIL_USER or not EMAIL_PASSWORD:
        log("EMAIL_USER and EMAIL_PASSWORD environment variables required", 'ERROR')
        log("Set them before running:")
        log("  export EMAIL_USER='your@email.com'")
        log("  export EMAIL_PASSWORD='your_password'")
        return None

    # Connect to database
    try:
        db_conn = sqlite3.connect(DB_PATH)
        db_cursor = db_conn.cursor()
        log(f"Connected to database: {DB_PATH}")
    except Exception as e:
        log(f"Database connection failed: {e}", 'ERROR')
        return None

    # Get initial email count
    db_cursor.execute("SELECT COUNT(*) FROM emails")
    initial_count = db_cursor.fetchone()[0]

    # Connect to IMAP
    try:
        log(f"Connecting to IMAP: {IMAP_SERVER}:{IMAP_PORT}")
        imap_conn = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        imap_conn.login(EMAIL_USER, EMAIL_PASSWORD)
        log("IMAP connection successful")
    except Exception as e:
        log(f"IMAP connection failed: {e}", 'ERROR')
        db_conn.close()
        return None

    # Sync each folder
    total_stats = {'imported': 0, 'skipped': 0, 'errors': 0}

    for folder in FOLDERS_TO_SYNC:
        log(f"\nSyncing folder: {folder}")
        stats = sync_folder(imap_conn, folder, db_cursor, db_conn)
        total_stats['imported'] += stats['imported']
        total_stats['skipped'] += stats['skipped']
        total_stats['errors'] += stats['errors']

    # Close IMAP
    try:
        imap_conn.close()
        imap_conn.logout()
    except:
        pass

    # Get final count
    db_cursor.execute("SELECT COUNT(*) FROM emails")
    final_count = db_cursor.fetchone()[0]

    # Close database
    db_conn.close()

    # Summary of import
    log("\n" + "-" * 60)
    log("EMAIL IMPORT SUMMARY")
    log("-" * 60)
    log(f"Imported: {total_stats['imported']}")
    log(f"Skipped (duplicates): {total_stats['skipped']}")
    log(f"Errors: {total_stats['errors']}")
    log(f"Total emails: {initial_count} -> {final_count}")

    # Run the linker if new emails were imported
    if total_stats['imported'] > 0:
        log("\n" + "-" * 60)
        log("RUNNING EMAIL PROJECT LINKER")
        log("-" * 60)

        linker = EmailProjectLinker(DB_PATH)
        link_result = linker.run(dry_run=False)

        log(f"New links created: {link_result['final']['linked'] - link_result['initial']['linked']}")
    else:
        log("\nNo new emails imported - skipping linker")

    # ALWAYS run orchestrator for categorization (catches uncategorized backlog)
    log("\n" + "-" * 60)
    log("RUNNING EMAIL ORCHESTRATOR (Categorization + Suggestions)")
    log("-" * 60)

    orchestrator = EmailOrchestrator(DB_PATH)
    # Use higher limit (500) to process backlog of uncategorized emails
    orch_result = orchestrator.process_new_emails(limit=500, hours=24)

    # Log categorization results
    cat_result = orch_result.get('categorization', {})
    log(f"Categorization: {cat_result.get('categorized', 0)} emails categorized, {cat_result.get('uncategorized', 0)} need review")

    # Log suggestion results
    sugg_result = orch_result.get('suggestions', {})
    log(f"Suggestions: {sugg_result.get('created', 0)} new suggestions generated")

    # Log any errors
    if orch_result.get('errors'):
        for error in orch_result['errors']:
            log(f"Orchestrator error: {error}", 'WARNING')

    # Final summary
    log("\n" + "=" * 60)
    log("SYNC COMPLETE")
    log("=" * 60)

    return total_stats


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='Sync emails and run project linker')
    parser.add_argument('--dry-run', action='store_true', help='Test IMAP connection only')
    parser.add_argument('--link-only', action='store_true', help='Run linker without importing')
    args = parser.parse_args()

    if args.link_only:
        log("Running linker only (no import)")
        linker = EmailProjectLinker(DB_PATH)
        linker.run(dry_run=False)
        return

    if args.dry_run:
        log("Testing IMAP connection...")
        if not EMAIL_USER or not EMAIL_PASSWORD:
            log("Set EMAIL_USER and EMAIL_PASSWORD first", 'ERROR')
            return
        try:
            imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            imap.login(EMAIL_USER, EMAIL_PASSWORD)
            log("IMAP connection successful!")
            status, folders = imap.list()
            log(f"Available folders: {len(folders)}")
            imap.logout()
        except Exception as e:
            log(f"Connection failed: {e}", 'ERROR')
        return

    run_sync()


if __name__ == '__main__':
    main()
