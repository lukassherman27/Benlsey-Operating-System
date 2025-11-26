#!/usr/bin/env python3
"""
Re-import October 31st SDC contract email with attachments
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from backend.services.email_importer import EmailImporter
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("=" * 70)
    print("RE-IMPORTING OCTOBER 31ST SDC CONTRACT EMAIL WITH ATTACHMENTS")
    print("=" * 70)

    # Connect to database
    db_path = os.getenv('DATABASE_PATH')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get the message_id from the existing email
    cursor.execute("""
        SELECT message_id, subject
        FROM emails
        WHERE email_id = 2024715
    """)
    result = cursor.fetchone()

    if not result:
        print("❌ Email 2024715 not found!")
        return

    message_id, subject = result
    print(f"\n📧 Target Email:")
    print(f"   Message ID: {message_id}")
    print(f"   Subject: {subject}")

    # Delete the existing email so we can re-import with attachments
    print(f"\n🗑️  Deleting existing email record...")
    cursor.execute("DELETE FROM emails WHERE email_id = 2024715")
    cursor.execute("DELETE FROM email_content WHERE email_id = 2024715")
    cursor.execute("DELETE FROM email_proposal_links WHERE email_id = 2024715")
    conn.commit()
    conn.close()
    print("   ✅ Deleted")

    # Now re-import using the email importer
    print(f"\n📥 Re-importing with attachments...")
    importer = EmailImporter()

    if not importer.connect():
        print("❌ Failed to connect to email server")
        return

    # Select INBOX
    importer.imap.select('INBOX')

    # Search for the specific message by Message-ID
    print(f"\n🔍 Searching for message: {message_id}")

    # Try searching by subject instead (more reliable)
    search_term = "SDC-CON-25-42"
    status, messages = importer.imap.search(None, f'SUBJECT "{search_term}"')

    if status != 'OK' or not messages[0]:
        print(f"❌ Could not find email with subject containing: {search_term}")
        importer.close()
        return

    email_ids = messages[0].split()
    print(f"   Found {len(email_ids)} matching emails")

    # Reconnect to database for import
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    imported = 0
    for email_id in email_ids:
        try:
            # Fetch email
            status, msg_data = importer.imap.fetch(email_id, '(RFC822)')

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    import email
                    from email.header import decode_header
                    from datetime import datetime

                    # Parse email
                    msg = email.message_from_bytes(response_part[1])

                    # Extract fields
                    msg_id = msg['Message-ID'] or f"imported-{email_id.decode()}"
                    msg_subject = importer.decode_header_value(msg['Subject'])
                    sender = msg['From']
                    recipients = msg['To']
                    date_str = msg['Date']

                    # Parse date
                    try:
                        date = email.utils.parsedate_to_datetime(date_str)
                    except:
                        date = datetime.now()

                    # Get body
                    body = importer.get_email_body(msg)
                    snippet = body[:500] if body else ""

                    # Save attachments and count them
                    print(f"\n📎 Processing attachments for email {email_id.decode()}...")
                    attachment_count = importer.save_attachments(msg, date)
                    print(f"   Total attachments saved: {attachment_count}")

                    # Insert into database
                    cursor.execute("""
                        INSERT INTO emails
                        (message_id, sender_email, recipient_emails, subject, snippet, body_full, date, processed, has_attachments)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """, (msg_id, sender, recipients, msg_subject, snippet, body, date, 1 if attachment_count > 0 else 0))

                    imported += 1
                    print(f"\n✅ Re-imported: {msg_subject}")

        except Exception as e:
            print(f"⚠️  Error processing email {email_id}: {e}")
            continue

    conn.commit()
    conn.close()
    importer.close()

    print(f"\n🎉 Done! Re-imported {imported} email(s) with attachments")
    print(f"   Check: /Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/2025-10/")

if __name__ == '__main__':
    main()
