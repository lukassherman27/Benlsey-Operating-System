#!/usr/bin/env python3
"""
Automated Email Importer - Server-Safe Version
Imports emails with rate limiting and delays to prevent server overload
Can be scheduled via cron for daily runs
"""

import os
import sys
import sqlite3
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import re
import time

# Configuration
DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
IMAP_SERVER = "tmail.bensley.com"
IMAP_PORT = 993
EMAIL_USER = "lukas@bensley.com"
EMAIL_PASS = os.environ.get("EMAIL_PASSWORD", "")  # Set via environment variable

ATTACHMENTS_DIR = "/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/EMAIL_ATTACHMENTS"
LOG_FILE = "/tmp/email_import.log"

# Folders to import
FOLDERS_TO_IMPORT = ["INBOX", "Sent"]

# SAFETY SETTINGS (prevents server overload)
MAX_EMAILS_PER_RUN = int(os.environ.get("MAX_EMAILS_PER_RUN", "500"))  # Limit per execution
DELAY_BETWEEN_EMAILS = 0.5  # 500ms delay between each email
PAUSE_EVERY_N_EMAILS = 50  # Pause after this many emails
PAUSE_DURATION = 30  # Pause for 30 seconds
RECONNECT_EVERY_N = 200  # Reconnect to server every N emails

def log(message):
    """Log to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    with open(LOG_FILE, "a") as f:
        f.write(log_message + "\n")

def get_email_password():
    """Get email password from environment or keychain"""
    if EMAIL_PASS:
        return EMAIL_PASS

    # Try to get from keychain (macOS)
    try:
        import keyring
        password = keyring.get_password("bensley_email", EMAIL_USER)
        if password:
            return password
    except:
        pass

    log("ERROR: Email password not found. Set EMAIL_PASSWORD environment variable")
    sys.exit(1)

def connect_imap():
    """Connect to IMAP server"""
    try:
        log(f"Connecting to {IMAP_SERVER}:{IMAP_PORT}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        password = get_email_password()
        mail.login(EMAIL_USER, password)
        log(f"✓ Connected as {EMAIL_USER}")
        return mail
    except Exception as e:
        log(f"✗ IMAP connection failed: {e}")
        sys.exit(1)

def decode_header_value(value):
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

def save_attachment(part, email_date, email_id, cursor):
    """Save email attachment to disk and database"""
    try:
        filename = part.get_filename()
        if not filename:
            return None

        # Create date-based folder
        date_folder = email_date.strftime('%Y-%m')
        save_dir = os.path.join(ATTACHMENTS_DIR, date_folder)
        os.makedirs(save_dir, exist_ok=True)

        # Save file
        filepath = os.path.join(save_dir, filename)
        payload = part.get_payload(decode=True)

        if payload:
            with open(filepath, 'wb') as f:
                f.write(payload)

            # Insert into database
            cursor.execute("""
                INSERT OR IGNORE INTO email_attachments
                (email_id, filename, filepath, filesize, mime_type, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (email_id, filename, filepath, len(payload), part.get_content_type()))

            return filepath
    except Exception as e:
        log(f"  ⚠️ Failed to save attachment: {e}")
        return None

def import_folder(mail, folder_name, cursor, conn):
    """Import emails from a specific folder with server-safe rate limiting"""
    try:
        log(f"\n📂 Processing {folder_name}...")
        mail.select(f'"{folder_name}"', readonly=True)

        # Get all email IDs
        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            log(f"  ✗ Failed to search folder")
            return 0

        email_ids = messages[0].split()
        total = len(email_ids)
        log(f"  Found {total} emails")

        # Apply max emails limit
        if total > MAX_EMAILS_PER_RUN:
            log(f"  ⚠️  Limiting to {MAX_EMAILS_PER_RUN} emails (safety feature)")
            email_ids = email_ids[:MAX_EMAILS_PER_RUN]
            total = MAX_EMAILS_PER_RUN

        imported = 0
        skipped = 0
        processed = 0

        for i, email_id in enumerate(email_ids, 1):
            processed += 1
            try:
                # Fetch email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue

                msg = email.message_from_bytes(msg_data[0][1])

                # Extract headers
                message_id = msg.get('Message-ID', f"<import-{email_id.decode()}>")
                subject = decode_header_value(msg.get('Subject', ''))
                sender = decode_header_value(msg.get('From', ''))
                date_str = msg.get('Date', '')

                # Parse date
                try:
                    email_date = email.utils.parsedate_to_datetime(date_str)
                except:
                    email_date = datetime.now()

                # Check if already exists
                cursor.execute("SELECT email_id FROM emails WHERE message_id = ?", (message_id,))
                if cursor.fetchone():
                    skipped += 1
                    if i % 100 == 0:
                        log(f"  [{i}/{total}] Processed... ({imported} new, {skipped} skipped)")
                    continue

                # Extract body
                body_full = ""
                has_attachments = 0

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            try:
                                body_full = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except:
                                pass
                        elif part.get_filename():
                            has_attachments = 1
                else:
                    try:
                        body_full = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        body_full = ""

                # Insert email
                cursor.execute("""
                    INSERT INTO emails (
                        message_id, subject, sender_email, sender_name, date,
                        body_full, body_preview, folder, has_attachments, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    message_id,
                    subject,
                    sender,
                    sender,
                    email_date.isoformat(),
                    body_full,
                    body_full[:500] if body_full else "",
                    folder_name,
                    has_attachments
                ))

                db_email_id = cursor.lastrowid

                # Save attachments
                if has_attachments and msg.is_multipart():
                    for part in msg.walk():
                        if part.get_filename():
                            save_attachment(part, email_date, db_email_id, cursor)

                imported += 1

                # SERVER SAFETY: Small delay after each email
                time.sleep(DELAY_BETWEEN_EMAILS)

                # SERVER SAFETY: Pause every N emails
                if processed % PAUSE_EVERY_N_EMAILS == 0:
                    conn.commit()
                    log(f"  [{i}/{total}] Pausing for {PAUSE_DURATION}s (server safety)...")
                    time.sleep(PAUSE_DURATION)

                # Commit every 50 emails
                elif imported % 50 == 0:
                    conn.commit()
                    log(f"  [{i}/{total}] Processed... ({imported} new, {skipped} skipped)")

            except Exception as e:
                log(f"  ⚠️ Error processing email {i}: {e}")
                time.sleep(1)  # Extra delay on error
                continue

        conn.commit()
        log(f"  ✓ Completed: {imported} imported, {skipped} skipped")
        return imported

    except Exception as e:
        log(f"  ✗ Folder import failed: {e}")
        return 0

def main():
    """
    Main import process with server-safe rate limiting

    SAFETY FEATURES:
    - Max 500 emails per run (configurable via MAX_EMAILS_PER_RUN env var)
    - 500ms delay between each email
    - 30 second pause every 50 emails
    - Extra 1 second delay on errors
    - Safe for daily cron jobs
    """
    log("=" * 70)
    log("BENSLEY AUTOMATED EMAIL IMPORT (SERVER-SAFE MODE)")
    log("=" * 70)
    log(f"Safety: Max {MAX_EMAILS_PER_RUN} emails/run, {DELAY_BETWEEN_EMAILS}s delay, {PAUSE_DURATION}s pause every {PAUSE_EVERY_N_EMAILS}")

    # Create attachments directory
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

    # Connect to database
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        log(f"✓ Connected to database: {DB_PATH}")
    except Exception as e:
        log(f"✗ Database connection failed: {e}")
        sys.exit(1)

    # Connect to IMAP
    mail = connect_imap()

    # Import from each folder
    total_imported = 0
    for folder in FOLDERS_TO_IMPORT:
        count = import_folder(mail, folder, cursor, conn)
        total_imported += count

    # Close connections
    mail.logout()
    conn.close()

    log("\n" + "=" * 70)
    log(f"IMPORT COMPLETE: {total_imported} new emails imported")
    log("=" * 70)

    return total_imported

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n✗ Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"\n✗ Fatal error: {e}")
        sys.exit(1)
