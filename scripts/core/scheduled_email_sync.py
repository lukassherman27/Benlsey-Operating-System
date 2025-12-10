#!/usr/bin/env python3
"""
Scheduled Email Sync - Import new emails and run project linker

This script:
1. Connects to IMAP server(s)
2. Imports new emails (skips duplicates by message_id)
3. Runs the fixed email_project_linker
4. Logs results

Supports MULTIPLE email accounts via:
1. EMAIL_ACCOUNTS env var (JSON array) - preferred for multiple accounts
2. EMAIL_USERNAME/EMAIL_PASSWORD env vars - single account (backwards compatible)

Designed for cron/launchd scheduled execution:
    # macOS launchd (preferred - survives restarts)
    See: ~/Library/LaunchAgents/com.bensley.email-sync.plist

    # cron fallback
    */15 * * * * cd /path/to/project && python scripts/core/scheduled_email_sync.py

Environment Variables:
    DATABASE_PATH - Path to SQLite database
    EMAIL_SERVER - IMAP server hostname (default: tmail.bensley.com)
    EMAIL_PORT - IMAP port (default: 993)

    # Option 1: Multiple accounts (JSON array)
    EMAIL_ACCOUNTS=[{"email":"lukas@bensley.com","password":"xxx"},{"email":"projects@bensley.com","password":"yyy"}]

    # Option 2: Single account (backwards compatible)
    EMAIL_USERNAME - Email username
    EMAIL_PASSWORD - Email password

Created: 2025-11-30
Updated: 2025-12-08 - Added multi-account support
"""

import imaplib
import email
from email.header import decode_header
import sqlite3
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the orchestrator for categorization and suggestion generation
from backend.services.email_orchestrator import EmailOrchestrator
# Import the batch suggestion service for grouped email suggestions
from backend.services.batch_suggestion_service import get_batch_service

# Note: email_project_linker was disabled 2025-12-02 due to flawed logic
# All linking is now handled by the orchestrator's suggestion pipeline

# Configuration
DB_PATH = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'database' / 'bensley_master.db'))
LOG_PATH = str(PROJECT_ROOT / 'logs' / 'email_sync.log')

# IMAP Configuration
IMAP_SERVER = os.getenv('EMAIL_SERVER', 'tmail.bensley.com')
IMAP_PORT = int(os.getenv('EMAIL_PORT', '993'))

# Safety settings
MAX_EMAILS_PER_RUN = int(os.getenv('MAX_EMAILS_PER_RUN', '100'))
DELAY_BETWEEN_EMAILS = 0.2  # 200ms delay
FOLDERS_TO_SYNC = ['INBOX', 'Sent']


def get_email_accounts() -> List[Dict[str, str]]:
    """
    Get list of email accounts to sync.

    Supports two configuration methods:
    1. EMAIL_ACCOUNTS env var (JSON array) - for multiple accounts
    2. EMAIL_USERNAME/EMAIL_PASSWORD env vars - single account (backwards compatible)

    Returns:
        List of dicts with 'email' and 'password' keys
    """
    accounts = []

    # Method 1: Check for JSON array of accounts
    accounts_json = os.getenv('EMAIL_ACCOUNTS', '')
    if accounts_json:
        try:
            parsed = json.loads(accounts_json)
            if isinstance(parsed, list):
                for acc in parsed:
                    if 'email' in acc and 'password' in acc:
                        accounts.append({
                            'email': acc['email'],
                            'password': acc['password'],
                            'folders': acc.get('folders', FOLDERS_TO_SYNC)
                        })
            log(f"Loaded {len(accounts)} accounts from EMAIL_ACCOUNTS")
        except json.JSONDecodeError as e:
            log(f"Failed to parse EMAIL_ACCOUNTS JSON: {e}", 'ERROR')

    # Method 2: Fall back to single account env vars
    if not accounts:
        username = os.getenv('EMAIL_USERNAME', '')
        password = os.getenv('EMAIL_PASSWORD', '')
        if username and password:
            accounts.append({
                'email': username,
                'password': password,
                'folders': FOLDERS_TO_SYNC
            })
            log(f"Using single account: {username}")

    return accounts


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
        import re
        body = re.sub(r'<style[^>]*>.*?</style>', '', html_body, flags=re.DOTALL)
        body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
        body = re.sub(r'<[^>]+>', ' ', body)
        body = re.sub(r'&nbsp;', ' ', body)
        body = re.sub(r'\s+', ' ', body).strip()

    return body


def sync_folder(imap_conn, folder: str, db_cursor, db_conn, account_email: str = '') -> dict:
    """Sync emails from a single folder

    Args:
        imap_conn: IMAP connection
        folder: Folder name to sync
        db_cursor: Database cursor
        db_conn: Database connection
        account_email: Email address of the account being synced (for tracking)

    Returns:
        dict with 'imported', 'skipped', 'errors' counts
    """
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

                # Build folder with account prefix for multi-account tracking
                folder_with_account = f"{account_email}:{folder}" if account_email else folder

                # Insert email
                db_cursor.execute("""
                    INSERT INTO emails
                    (message_id, sender_email, recipient_emails, subject, snippet, body_full,
                     date_normalized, processed, folder, thread_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                """, (
                    message_id, sender, recipients, subject, snippet, body,
                    email_date.isoformat(), folder_with_account, thread_id
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


def sync_account(account: Dict[str, any], db_cursor, db_conn) -> dict:
    """Sync all folders for a single email account

    Args:
        account: Dict with 'email', 'password', 'folders' keys
        db_cursor: Database cursor
        db_conn: Database connection

    Returns:
        dict with 'imported', 'skipped', 'errors' counts
    """
    account_email = account['email']
    account_password = account['password']
    folders = account.get('folders', FOLDERS_TO_SYNC)

    log(f"\n{'='*60}")
    log(f"SYNCING ACCOUNT: {account_email}")
    log(f"{'='*60}")

    total_stats = {'imported': 0, 'skipped': 0, 'errors': 0}

    # Connect to IMAP
    try:
        log(f"Connecting to IMAP: {IMAP_SERVER}:{IMAP_PORT}")
        imap_conn = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        imap_conn.login(account_email, account_password)
        log("IMAP connection successful")
    except Exception as e:
        log(f"IMAP connection failed for {account_email}: {e}", 'ERROR')
        return total_stats

    # Sync each folder
    for folder in folders:
        log(f"\nSyncing folder: {folder}")
        stats = sync_folder(imap_conn, folder, db_cursor, db_conn, account_email)
        total_stats['imported'] += stats['imported']
        total_stats['skipped'] += stats['skipped']
        total_stats['errors'] += stats['errors']

    # Close IMAP
    try:
        imap_conn.close()
        imap_conn.logout()
    except:
        pass

    log(f"\nAccount {account_email} complete: {total_stats['imported']} imported, {total_stats['skipped']} skipped")
    return total_stats


def run_sync():
    """Run the full sync process for all configured accounts"""
    log("=" * 60)
    log("BENSLEY EMAIL SYNC - Starting")
    log(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)

    # Get email accounts
    accounts = get_email_accounts()
    if not accounts:
        log("No email accounts configured!", 'ERROR')
        log("Set EMAIL_ACCOUNTS (JSON) or EMAIL_USERNAME/EMAIL_PASSWORD env vars")
        log("Example:")
        log('  export EMAIL_ACCOUNTS=\'[{"email":"lukas@bensley.com","password":"xxx"}]\'')
        log("  OR")
        log("  export EMAIL_USERNAME='lukas@bensley.com'")
        log("  export EMAIL_PASSWORD='xxx'")
        return None

    log(f"Found {len(accounts)} account(s) to sync")
    for acc in accounts:
        log(f"  - {acc['email']} (folders: {', '.join(acc.get('folders', FOLDERS_TO_SYNC))})")

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

    # Sync each account
    total_stats = {'imported': 0, 'skipped': 0, 'errors': 0}
    account_results = []

    for account in accounts:
        stats = sync_account(account, db_cursor, db_conn)
        total_stats['imported'] += stats['imported']
        total_stats['skipped'] += stats['skipped']
        total_stats['errors'] += stats['errors']
        account_results.append({
            'email': account['email'],
            'stats': stats
        })

    # Get final count
    db_cursor.execute("SELECT COUNT(*) FROM emails")
    final_count = db_cursor.fetchone()[0]

    # Close database
    db_conn.close()

    # Summary of import
    log("\n" + "-" * 60)
    log("EMAIL IMPORT SUMMARY")
    log("-" * 60)
    for result in account_results:
        s = result['stats']
        log(f"  {result['email']}: {s['imported']} imported, {s['skipped']} skipped, {s['errors']} errors")
    log("-" * 60)
    log(f"TOTAL Imported: {total_stats['imported']}")
    log(f"TOTAL Skipped (duplicates): {total_stats['skipped']}")
    log(f"TOTAL Errors: {total_stats['errors']}")
    log(f"Database emails: {initial_count} -> {final_count}")

    # Note: The old email_project_linker was disabled 2025-12-02
    # All linking is now handled via the orchestrator's AI suggestion pipeline

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

    # Run batch suggestion service for grouped email-project linking
    # This groups emails by sender for efficient batch review instead of per-email suggestions
    log("\n" + "-" * 60)
    log("RUNNING BATCH SUGGESTION SERVICE (Grouped Email Links)")
    log("-" * 60)

    try:
        batch_service = get_batch_service(DB_PATH)
        batch_result = batch_service.process_emails_for_batches(hours=24, limit=500)

        log(f"Batch Processing:")
        log(f"  Emails processed: {batch_result.get('emails_processed', 0)}")
        log(f"  Batches created: {batch_result.get('batches_created', 0)}")
        log(f"  Auto-approved (high confidence): {batch_result.get('auto_approved', 0)}")
        log(f"  Pending batch review: {batch_result.get('batch_review', 0)}")
        log(f"  Low confidence logged: {batch_result.get('low_confidence_logged', 0)}")
        log(f"  Skipped internal: {batch_result.get('skipped_internal', 0)}")

        # Get batch stats
        batch_stats = batch_service.get_batch_stats()
        pending_batches = batch_stats.get('pending_by_tier', {})
        if pending_batches:
            log(f"  Pending batches by tier: {pending_batches}")

    except Exception as e:
        log(f"Batch suggestion service error: {e}", 'ERROR')

    # Final summary
    log("\n" + "=" * 60)
    log("SYNC COMPLETE")
    log("=" * 60)

    return total_stats


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='Sync emails from multiple accounts')
    parser.add_argument('--dry-run', action='store_true', help='Test IMAP connection only')
    parser.add_argument('--orchestrate-only', action='store_true', help='Run orchestrator only (no email import)')
    parser.add_argument('--list-accounts', action='store_true', help='List configured accounts')
    args = parser.parse_args()

    if args.list_accounts:
        accounts = get_email_accounts()
        if not accounts:
            print("No accounts configured!")
            print("\nConfigure accounts using one of these methods:")
            print("  1. Set EMAIL_ACCOUNTS env var (JSON array):")
            print('     export EMAIL_ACCOUNTS=\'[{"email":"lukas@bensley.com","password":"xxx"}]\'')
            print("\n  2. Set EMAIL_USERNAME and EMAIL_PASSWORD:")
            print('     export EMAIL_USERNAME="lukas@bensley.com"')
            print('     export EMAIL_PASSWORD="xxx"')
        else:
            print(f"Configured accounts ({len(accounts)}):")
            for acc in accounts:
                folders = ', '.join(acc.get('folders', FOLDERS_TO_SYNC))
                print(f"  - {acc['email']} (folders: {folders})")
        return

    if args.orchestrate_only:
        log("Running orchestrator only (no email import)")
        log("This will categorize uncategorized emails and generate suggestions")
        orchestrator = EmailOrchestrator(DB_PATH)
        orch_result = orchestrator.process_new_emails(limit=500, hours=24)
        cat_result = orch_result.get('categorization', {})
        log(f"Categorization: {cat_result.get('categorized', 0)} emails categorized")
        sugg_result = orch_result.get('suggestions', {})
        log(f"Suggestions: {sugg_result.get('created', 0)} new suggestions generated")

        # Also run batch suggestion service
        log("\nRunning batch suggestion service...")
        try:
            batch_service = get_batch_service(DB_PATH)
            batch_result = batch_service.process_emails_for_batches(hours=24, limit=500)
            log(f"Batch: {batch_result.get('batches_created', 0)} batches, {batch_result.get('auto_approved', 0)} auto-approved")
        except Exception as e:
            log(f"Batch service error: {e}", 'ERROR')
        return

    if args.dry_run:
        log("Testing IMAP connections...")
        accounts = get_email_accounts()
        if not accounts:
            log("No accounts configured! Set EMAIL_ACCOUNTS or EMAIL_USERNAME/EMAIL_PASSWORD", 'ERROR')
            return

        for account in accounts:
            account_email = account['email']
            account_password = account['password']
            log(f"\nTesting: {account_email}")
            try:
                imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
                imap.login(account_email, account_password)
                log(f"  ✅ Connection successful!")
                status, folders = imap.list()
                log(f"  Available folders: {len(folders)}")
                for folder in folders[:5]:  # Show first 5
                    log(f"    - {folder.decode()}")
                if len(folders) > 5:
                    log(f"    ... and {len(folders) - 5} more")
                imap.logout()
            except Exception as e:
                log(f"  ❌ Connection failed: {e}", 'ERROR')
        return

    run_sync()


if __name__ == '__main__':
    main()
