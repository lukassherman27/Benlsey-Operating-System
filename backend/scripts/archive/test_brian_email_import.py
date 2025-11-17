#!/usr/bin/env python3
"""
Test Import - First 100 Emails from Brian's Account
Imports emails, extracts attachments, logs progress
"""

import os
import sys
import sqlite3
import imaplib
import email
from email.header import decode_header
from datetime import datetime

# Configuration
DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
IMAP_SERVER = "tmail.bensley.com"
IMAP_PORT = 993
EMAIL_USER = "brian@bensley.com"  # Update if needed
EMAIL_PASS = os.environ.get("BRIAN_EMAIL_PASSWORD", "")

ATTACHMENTS_DIR = "/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/EMAIL_ATTACHMENTS"
LOG_FILE = "/tmp/brian_email_test_import.log"
TEST_LIMIT = 100  # Only import first 100 emails

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

    log("ERROR: Email password not found. Set BRIAN_EMAIL_PASSWORD environment variable")
    log("Example: export BRIAN_EMAIL_PASSWORD='your_password_here'")
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

def import_test_emails(mail, cursor, conn):
    """Import first 100 emails from INBOX"""
    try:
        log(f"\n📂 Processing INBOX (limit: {TEST_LIMIT} emails)...")
        mail.select('"INBOX"', readonly=True)

        # Get all email IDs
        status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            log(f"  ✗ Failed to search folder")
            return 0

        email_ids = messages[0].split()
        total = len(email_ids)
        log(f"  Found {total} emails in INBOX")

        # Limit to first TEST_LIMIT emails
        email_ids = email_ids[:TEST_LIMIT]
        log(f"  Importing first {len(email_ids)} emails...")

        imported = 0
        skipped = 0

        for i, email_id in enumerate(email_ids, 1):
            try:
                # Fetch email
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue

                msg = email.message_from_bytes(msg_data[0][1])

                # Extract headers
                message_id = msg.get('Message-ID', f"<brian-import-{email_id.decode()}>")
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
                    if i % 20 == 0:
                        log(f"  [{i}/{len(email_ids)}] {imported} new, {skipped} skipped")
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
                    "INBOX",
                    has_attachments
                ))

                db_email_id = cursor.lastrowid

                # Save attachments
                attachment_count = 0
                if has_attachments and msg.is_multipart():
                    for part in msg.walk():
                        if part.get_filename():
                            if save_attachment(part, email_date, db_email_id, cursor):
                                attachment_count += 1

                imported += 1

                # Log progress
                if attachment_count > 0:
                    log(f"  [{i}/{len(email_ids)}] ✓ {subject[:50]}... ({attachment_count} attachments)")
                elif i % 20 == 0:
                    log(f"  [{i}/{len(email_ids)}] {imported} new, {skipped} skipped")

                # Commit every 25 emails
                if imported % 25 == 0:
                    conn.commit()
                    log(f"  💾 Committed {imported} emails")

            except Exception as e:
                log(f"  ⚠️ Error processing email {i}: {e}")
                continue

        conn.commit()
        log(f"\n  ✓ Import Complete:")
        log(f"    - Total in INBOX: {total}")
        log(f"    - Processed: {len(email_ids)}")
        log(f"    - New imported: {imported}")
        log(f"    - Already existed: {skipped}")
        return imported

    except Exception as e:
        log(f"  ✗ Import failed: {e}")
        return 0

def main():
    """Main test import process"""
    log("=" * 70)
    log("BENSLEY TEST EMAIL IMPORT - BRIAN'S ACCOUNT")
    log("=" * 70)
    log(f"Email: {EMAIL_USER}")
    log(f"Limit: {TEST_LIMIT} emails")
    log(f"Database: {DB_PATH}")
    log(f"Log: {LOG_FILE}")

    # Create attachments directory
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

    # Connect to database
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        log(f"✓ Connected to database")
    except Exception as e:
        log(f"✗ Database connection failed: {e}")
        sys.exit(1)

    # Connect to IMAP
    mail = connect_imap()

    # Import emails
    total_imported = import_test_emails(mail, cursor, conn)

    # Close connections
    mail.logout()
    conn.close()

    log("\n" + "=" * 70)
    log(f"TEST IMPORT COMPLETE: {total_imported} new emails imported")
    log(f"Next steps:")
    log(f"  1. Review log: cat {LOG_FILE}")
    log(f"  2. Check database: sqlite3 {DB_PATH}")
    log(f"  3. Run email categorization: python3 backend/services/email_content_processor.py")
    log(f"  4. Run smart matcher: python3 smart_email_matcher.py")
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
        import traceback
        traceback.print_exc()
        sys.exit(1)
