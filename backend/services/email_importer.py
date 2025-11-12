#!/usr/bin/env python3
"""
Email Importer - Connect to Axigen IMAP and import emails
"""

import imaplib
import email
from email.header import decode_header
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class EmailImporter:
    def __init__(self):
        self.server = os.getenv('EMAIL_SERVER')
        self.port = int(os.getenv('EMAIL_PORT', 993))
        self.username = os.getenv('EMAIL_USER')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.db_path = os.getenv('DATABASE_PATH')

    def connect(self):
        """Connect to IMAP server"""
        print(f"Connecting to {self.server}:{self.port}...")
        try:
            self.imap = imaplib.IMAP4_SSL(self.server, self.port)
            self.imap.login(self.username, self.password)
            print("✅ Connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def get_folders(self):
        """List all email folders"""
        try:
            status, folders = self.imap.list()
            print(f"\n📁 Available folders:")
            for folder in folders:
                print(f"   {folder.decode()}")
            return folders
        except Exception as e:
            print(f"❌ Error listing folders: {e}")
            return []

    def import_emails(self, folder='INBOX', limit=100):
        """Import emails from a folder"""
        print(f"\n📧 Importing emails from {folder}...")

        try:
            # Select folder
            self.imap.select(folder)

            # Search for all emails
            status, messages = self.imap.search(None, 'ALL')
            email_ids = messages[0].split()

            total = len(email_ids)
            print(f"   Found {total} emails")

            # Limit if specified
            if limit:
                email_ids = email_ids[-limit:]  # Get most recent
                print(f"   Importing last {len(email_ids)} emails...")

            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            imported = 0
            skipped = 0

            for i, email_id in enumerate(email_ids, 1):
                if i % 10 == 0:
                    print(f"   Processing {i}/{len(email_ids)}...")

                try:
                    # Fetch email
                    status, msg_data = self.imap.fetch(email_id, '(RFC822)')

                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            # Parse email
                            msg = email.message_from_bytes(response_part[1])

                            # Extract fields
                            subject = self.decode_header_value(msg['Subject'])
                            sender = msg['From']
                            recipients = msg['To']
                            date_str = msg['Date']

                            # Parse date
                            try:
                                date = email.utils.parsedate_to_datetime(date_str)
                            except:
                                date = datetime.now()

                            # Get body
                            body = self.get_email_body(msg)
                            snippet = body[:500] if body else ""

                            # Check if already exists
                            cursor.execute("""
                                SELECT email_id FROM emails
                                WHERE subject = ? AND sender_email = ? AND date = ?
                            """, (subject, sender, date))

                            if cursor.fetchone():
                                skipped += 1
                                continue

                            # Insert into database
                            cursor.execute("""
                                INSERT INTO emails
                                (sender_email, recipients, subject, snippet, body, date, processed)
                                VALUES (?, ?, ?, ?, ?, ?, 0)
                            """, (sender, recipients, subject, snippet, body, date))

                            imported += 1

                except Exception as e:
                    print(f"   ⚠️  Error processing email {email_id}: {e}")
                    continue

            conn.commit()
            conn.close()

            print(f"\n✅ Import complete!")
            print(f"   Imported: {imported}")
            print(f"   Skipped (duplicates): {skipped}")
            print(f"   Total in database: {imported + skipped}")

            return imported

        except Exception as e:
            print(f"❌ Error importing emails: {e}")
            return 0

    def decode_header_value(self, header):
        """Decode email header"""
        if not header:
            return ""

        decoded = decode_header(header)
        header_parts = []

        for part, encoding in decoded:
            if isinstance(part, bytes):
                header_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                header_parts.append(part)

        return ''.join(header_parts)

    def get_email_body(self, msg):
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

    def close(self):
        """Close IMAP connection"""
        try:
            self.imap.close()
            self.imap.logout()
            print("✅ Connection closed")
        except:
            pass

def main():
    print("="*70)
    print("BENSLEY EMAIL IMPORTER")
    print("="*70)

    importer = EmailImporter()

    # Connect
    if not importer.connect():
        return

    # Show folders
    importer.get_folders()

    # Ask which folder to import
    print("\nWhich folder do you want to import?")
    folder = input("Folder name (or press Enter for INBOX): ").strip() or "INBOX"

    # Ask how many emails
    print("\nHow many emails to import?")
    limit_input = input("Number (or press Enter for last 100): ").strip()
    limit = int(limit_input) if limit_input else 100

    # Import
    imported = importer.import_emails(folder, limit)

    # Close
    importer.close()

    print(f"\n🎉 Done! {imported} emails imported")
    print(f"   Check them at: http://localhost:8000/emails/unprocessed")

if __name__ == '__main__':
    main()
