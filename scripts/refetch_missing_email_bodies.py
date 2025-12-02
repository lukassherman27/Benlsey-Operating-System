#!/usr/bin/env python3
"""
Re-fetch Missing Email Bodies
Connects to IMAP and updates emails that have empty body_full
"""

import imaplib
import email
from email.header import decode_header
import sqlite3
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Configuration
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
EMAIL_SERVER = os.getenv('EMAIL_SERVER')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 993))
EMAIL_USER = os.getenv('EMAIL_USERNAME') or os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

class EmailBodyRefetcher:
    def __init__(self):
        self.imap = None
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def connect_imap(self):
        """Connect to IMAP server"""
        print(f"Connecting to {EMAIL_SERVER}:{EMAIL_PORT}...")
        try:
            self.imap = imaplib.IMAP4_SSL(EMAIL_SERVER, EMAIL_PORT)
            self.imap.login(EMAIL_USER, EMAIL_PASSWORD)
            print("✅ Connected to IMAP server")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def get_emails_with_missing_body(self, folder=None):
        """Get emails from database that have empty body_full"""
        cursor = self.conn.cursor()

        query = """
            SELECT email_id, message_id, subject, folder, date
            FROM emails
            WHERE (body_full IS NULL OR body_full = '' OR LENGTH(body_full) < 10)
        """

        if folder:
            query += f" AND folder = '{folder}'"

        query += " ORDER BY date DESC"

        cursor.execute(query)
        return cursor.fetchall()

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
        """Extract email body - try text/plain first, then text/html"""
        body = ""

        if msg.is_multipart():
            # Try to find text/plain first
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                if content_type == 'text/plain':
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                            if body.strip():
                                return body
                    except:
                        pass

            # If no text/plain, try text/html
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if "attachment" in content_disposition:
                    continue

                if content_type == 'text/html':
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                            # Strip HTML tags for cleaner storage
                            import re
                            body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
                            body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
                            body = re.sub(r'<[^>]+>', ' ', body)
                            body = re.sub(r'\s+', ' ', body).strip()
                            if body:
                                return body
                    except:
                        pass
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
            except:
                pass

        return body

    def refetch_by_message_id(self, folder, message_id):
        """Search for email in folder by Message-ID and get body"""
        try:
            self.imap.select(folder)

            # Search by Message-ID header
            search_criteria = f'HEADER Message-ID "{message_id}"'
            status, messages = self.imap.search(None, search_criteria)

            if status != 'OK' or not messages[0]:
                return None

            email_ids = messages[0].split()
            if not email_ids:
                return None

            # Fetch the email
            status, msg_data = self.imap.fetch(email_ids[0], '(RFC822)')

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    body = self.get_email_body(msg)
                    return body

        except Exception as e:
            print(f"    Error fetching: {e}")

        return None

    def refetch_by_subject_date(self, folder, subject, date_str):
        """Search for email by subject and date as fallback"""
        try:
            self.imap.select(folder)

            # Parse date for IMAP search
            try:
                if date_str:
                    # Handle various date formats
                    date_obj = None
                    for fmt in ['%Y-%m-%d %H:%M:%S%z', '%Y-%m-%d', '%a, %d %b %Y %H:%M:%S %z']:
                        try:
                            date_obj = datetime.strptime(date_str[:25], fmt[:len(date_str[:25])])
                            break
                        except:
                            continue

                    if date_obj:
                        imap_date = date_obj.strftime('%d-%b-%Y')
                        search_criteria = f'ON {imap_date}'
                        status, messages = self.imap.search(None, search_criteria)

                        if status == 'OK' and messages[0]:
                            email_ids = messages[0].split()

                            # Search through emails on that date for matching subject
                            for eid in email_ids[:50]:  # Limit to prevent too much searching
                                status, msg_data = self.imap.fetch(eid, '(RFC822)')

                                for response_part in msg_data:
                                    if isinstance(response_part, tuple):
                                        msg = email.message_from_bytes(response_part[1])
                                        fetched_subject = self.decode_header_value(msg['Subject'])

                                        # Check if subjects match (approximate)
                                        if subject and fetched_subject:
                                            # Normalize both subjects
                                            norm_subject = subject.lower().strip()[:50]
                                            norm_fetched = fetched_subject.lower().strip()[:50]

                                            if norm_subject in norm_fetched or norm_fetched in norm_subject:
                                                body = self.get_email_body(msg)
                                                if body and len(body) > 10:
                                                    return body
            except Exception as e:
                pass

        except Exception as e:
            pass

        return None

    def update_email_body(self, email_id, body):
        """Update email body in database"""
        cursor = self.conn.cursor()
        snippet = body[:500] if body else ""

        cursor.execute("""
            UPDATE emails
            SET body_full = ?, snippet = ?, body_preview = ?
            WHERE email_id = ?
        """, (body, snippet, snippet, email_id))

        self.conn.commit()

    def run(self, folder='Sent', limit=None, dry_run=False):
        """Re-fetch missing bodies for specified folder"""
        print("=" * 70)
        print("EMAIL BODY RE-FETCHER")
        print("=" * 70)

        # Connect to IMAP
        if not self.connect_imap():
            return

        # Get emails with missing bodies
        emails = self.get_emails_with_missing_body(folder)
        total = len(emails)

        print(f"\n📧 Found {total} emails with missing bodies in {folder or 'ALL'} folder(s)")

        if limit:
            emails = emails[:limit]
            print(f"   Processing first {limit} emails...")

        if dry_run:
            print("\n🔍 DRY RUN - Not updating database")
            for email in emails[:20]:
                print(f"   Would refetch: {email['subject'][:60]}...")
            return

        # Process each email
        updated = 0
        failed = 0

        for i, email_row in enumerate(emails, 1):
            email_id = email_row['email_id']
            message_id = email_row['message_id']
            subject = email_row['subject']
            email_folder = email_row['folder'] or folder
            date = email_row['date']

            print(f"\n[{i}/{len(emails)}] {subject[:50]}...")

            # Try to refetch body
            body = None

            # Method 1: By Message-ID
            if message_id and not message_id.startswith('imported-'):
                body = self.refetch_by_message_id(email_folder, message_id)
                if body:
                    print(f"   ✅ Found by Message-ID ({len(body)} chars)")

            # Method 2: By subject and date (fallback)
            if not body:
                body = self.refetch_by_subject_date(email_folder, subject, date)
                if body:
                    print(f"   ✅ Found by subject/date ({len(body)} chars)")

            if body and len(body) > 10:
                self.update_email_body(email_id, body)
                updated += 1
            else:
                print(f"   ❌ Could not fetch body")
                failed += 1

        # Summary
        print("\n" + "=" * 70)
        print("✅ RE-FETCH COMPLETE")
        print("=" * 70)
        print(f"Updated: {updated}")
        print(f"Failed: {failed}")
        print(f"Total processed: {len(emails)}")

        # Close connections
        try:
            self.imap.close()
            self.imap.logout()
        except:
            pass

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Re-fetch missing email bodies from IMAP')
    parser.add_argument('--folder', default='Sent', help='IMAP folder to fetch from (default: Sent)')
    parser.add_argument('--limit', type=int, help='Limit number of emails to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without updating')
    parser.add_argument('--all-folders', action='store_true', help='Process all folders, not just Sent')
    args = parser.parse_args()

    refetcher = EmailBodyRefetcher()

    if args.all_folders:
        refetcher.run(folder=None, limit=args.limit, dry_run=args.dry_run)
    else:
        refetcher.run(folder=args.folder, limit=args.limit, dry_run=args.dry_run)

if __name__ == '__main__':
    main()
