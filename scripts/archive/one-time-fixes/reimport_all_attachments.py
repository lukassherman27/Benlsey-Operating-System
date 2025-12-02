#!/usr/bin/env python3
"""
Re-import ALL email attachments with proper classification and database tracking

This script:
1. Connects to IMAP
2. For each email in the database, fetches attachments from IMAP
3. Saves only TRUE attachments (not inline images)
4. Classifies documents (contract, proposal, invoice, etc.)
5. Saves to email_attachments table with full metadata
6. Updates has_attachments flag

Run time: Expect ~30-60 minutes for ~2000 emails
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from backend.services.email_importer import EmailImporter
import sqlite3
import os
import email
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def main():
    print("=" * 80)
    print("RE-IMPORTING ALL EMAIL ATTACHMENTS WITH PROPER CLASSIFICATION")
    print("=" * 80)

    db_path = os.getenv('DATABASE_PATH')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all emails that we want to check for attachments
    cursor.execute("""
        SELECT email_id, message_id, subject, date
        FROM emails
        ORDER BY date DESC
    """)
    all_emails = cursor.fetchall()

    total_emails = len(all_emails)
    print(f"\n📊 Found {total_emails} emails in database")
    print(f"   Will check each for attachments and download any found\n")

    # Connect to IMAP
    importer = EmailImporter()
    if not importer.connect():
        print("❌ Failed to connect to email server")
        return

    # Select INBOX
    importer.imap.select('INBOX')

    # Statistics
    emails_processed = 0
    emails_with_attachments = 0
    total_attachments = 0
    total_contracts = 0
    total_proposals = 0
    total_invoices = 0

    # Process each email
    for idx, email_row in enumerate(all_emails, 1):
        email_id = email_row['email_id']
        message_id = email_row['message_id']
        subject = email_row['subject'] or "(no subject)"

        # Parse email date
        try:
            if email_row['date']:
                email_date = email.utils.parsedate_to_datetime(email_row['date'])
            else:
                email_date = datetime.now()
        except:
            email_date = datetime.now()

        if idx % 100 == 0:
            print(f"\n📈 Progress: {idx}/{total_emails} emails processed")
            print(f"   Attachments found so far: {total_attachments}")

        try:
            # Search for this specific email by Message-ID header
            # Note: Message-ID search may not work on all IMAP servers
            # So we'll use UID search as backup

            # Try searching by subject (more reliable than Message-ID)
            search_subject = subject[:50].replace('"', '').replace('\\', '')
            status, messages = importer.imap.search(None, f'SUBJECT "{search_subject}"')

            if status != 'OK' or not messages[0]:
                continue

            email_uids = messages[0].split()

            # Try to find the exact match by comparing message-id
            found_match = False
            for uid in email_uids:
                status, msg_data = importer.imap.fetch(uid, '(RFC822)')

                if status != 'OK':
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        msg_id = msg['Message-ID']

                        if msg_id == message_id:
                            found_match = True

                            # Extract attachments
                            attachments = importer.save_attachments(msg, email_date, email_id, cursor)

                            if attachments:
                                emails_with_attachments += 1
                                total_attachments += len(attachments)

                                # Count by type
                                for att in attachments:
                                    if att['document_type'] == 'external_contract':
                                        total_contracts += 1
                                    elif att['document_type'] == 'proposal':
                                        total_proposals += 1
                                    elif att['document_type'] == 'invoice':
                                        total_invoices += 1

                                # Update has_attachments flag
                                cursor.execute("""
                                    UPDATE emails SET has_attachments = 1
                                    WHERE email_id = ?
                                """, (email_id,))

                                print(f"   ✅ {subject[:60]}: {len(attachments)} attachment(s)")

                            break

                if found_match:
                    break

            emails_processed += 1

        except Exception as e:
            print(f"   ⚠️  Error processing email_id {email_id}: {e}")
            continue

        # Commit every 50 emails
        if idx % 50 == 0:
            conn.commit()

    # Final commit
    conn.commit()
    conn.close()
    importer.close()

    # Print summary
    print("\n" + "=" * 80)
    print("✅ ATTACHMENT IMPORT COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Statistics:")
    print(f"   Total emails processed: {emails_processed}")
    print(f"   Emails with attachments: {emails_with_attachments}")
    print(f"   Total attachments saved: {total_attachments}")
    print(f"\n📁 By Type:")
    print(f"   Contracts: {total_contracts}")
    print(f"   Proposals: {total_proposals}")
    print(f"   Invoices: {total_invoices}")
    print(f"   Other: {total_attachments - total_contracts - total_proposals - total_invoices}")
    print(f"\n💾 Files saved to: /Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/")
    print(f"📊 Database updated: {db_path}")
    print("\n")

if __name__ == '__main__':
    main()
