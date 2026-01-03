#!/usr/bin/env python3
"""
Email Importer - Connect to Axigen IMAP and import emails
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

# Add project root to path for utils
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

class EmailImporter:
    def __init__(self):
        self.server = os.getenv('EMAIL_SERVER')
        self.port = int(os.getenv('EMAIL_PORT', 993))
        self.username = os.getenv('EMAIL_USERNAME')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.db_path = os.getenv('BENSLEY_DB_PATH', 'database/bensley_master.db')
        self.attachments_dir = os.getenv('ATTACHMENTS_DIR', 'files/attachments')

    def connect(self):
        """Connect to IMAP server"""
        logger.info(f"Connecting to IMAP server: {self.server}:{self.port}")
        print(f"Connecting to {self.server}:{self.port}...")
        try:
            self.imap = imaplib.IMAP4_SSL(self.server, self.port)
            self.imap.login(self.username, self.password)
            logger.info("Successfully connected to IMAP server")
            print("✅ Connected successfully!")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}", exc_info=True)
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
                            message_id = msg['Message-ID'] or f"imported-{email_id.decode()}"
                            subject = self.decode_header_value(msg['Subject'])
                            sender = self.decode_header_value(msg['From'])
                            recipients = self.decode_header_value(msg['To'])
                            date_str = msg['Date']

                            # Parse date
                            try:
                                date = email.utils.parsedate_to_datetime(date_str)
                            except (ValueError, TypeError):
                                date = datetime.now()

                            # Get body
                            body = self.get_email_body(msg)
                            snippet = body[:500] if body else ""

                            # Check if already exists
                            cursor.execute("""
                                SELECT email_id FROM emails
                                WHERE message_id = ?
                            """, (message_id,))

                            if cursor.fetchone():
                                skipped += 1
                                continue

                            # Insert into database FIRST to get email_id
                            cursor.execute("""
                                INSERT INTO emails
                                (message_id, sender_email, recipient_emails, subject, snippet, body_full, date, date_normalized, processed, has_attachments, folder)
                                VALUES (?, ?, ?, ?, ?, ?, ?, datetime(?), 0, 0, ?)
                            """, (message_id, sender, recipients, subject, snippet, body, date, date, folder))

                            email_id = cursor.lastrowid

                            # Now save attachments with email_id
                            attachments = self.save_attachments(msg, date, email_id, cursor)

                            # Update has_attachments flag if we saved any
                            if attachments:
                                cursor.execute("""
                                    UPDATE emails SET has_attachments = 1 WHERE email_id = ?
                                """, (email_id,))

                            imported += 1

                except Exception as e:
                    logger.warning(f"Error processing email {email_id}: {e}")
                    print(f"   ⚠️  Error processing email {email_id}: {e}")
                    continue

            conn.commit()
            conn.close()

            logger.info(f"Email import complete: imported={imported}, skipped={skipped}")
            print(f"\n✅ Import complete!")
            print(f"   Imported: {imported}")
            print(f"   Skipped (duplicates): {skipped}")
            print(f"   Total in database: {imported + skipped}")

            return imported

        except Exception as e:
            logger.error(f"Failed to import emails: {e}", exc_info=True)
            print(f"❌ Error importing emails: {e}")
            return 0

    def decode_header_value(self, header):
        """Decode email header"""
        if not header:
            return ""

        # Map encoding aliases that Python doesn't recognize
        ENCODING_ALIASES = {
            'windows-874': 'cp874',      # Thai
            'windows-1252': 'cp1252',    # Western European
            'windows-1251': 'cp1251',    # Cyrillic
            'windows-1250': 'cp1250',    # Central European
            'ks_c_5601-1987': 'euc_kr',  # Korean
            'gb2312': 'gbk',             # Simplified Chinese
            'iso-8859-11': 'cp874',      # Thai ISO
        }

        decoded = decode_header(header)
        header_parts = []

        for part, encoding in decoded:
            if isinstance(part, bytes):
                enc = encoding or 'utf-8'
                if encoding:
                    enc = ENCODING_ALIASES.get(encoding.lower(), encoding)
                try:
                    header_parts.append(part.decode(enc, errors='ignore'))
                except (LookupError, UnicodeDecodeError):
                    header_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                header_parts.append(part)

        return ''.join(header_parts)

    def get_email_body(self, msg):
        """Extract email body - prefer plain text, fall back to HTML"""
        import re
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

    def save_attachments(self, msg, email_date, email_id, cursor):
        """
        Extract and save email attachments to BY_DATE folder structure
        AND track in database

        Args:
            msg: Email message object
            email_date: datetime object of email date
            email_id: Database email_id for linking
            cursor: Database cursor for inserting attachment records

        Returns:
            list: List of saved attachment metadata
        """
        attachments = []

        if not msg.is_multipart():
            return attachments

        # Create date-based subdirectory (YYYY-MM format)
        date_folder = email_date.strftime('%Y-%m')
        save_dir = os.path.join(self.attachments_dir, date_folder)

        # Ensure directory exists
        os.makedirs(save_dir, exist_ok=True)

        # Walk through all parts of the email
        for part in msg.walk():
            # Skip multipart containers
            if part.get_content_maintype() == 'multipart':
                continue

            # Check if this part is an attachment
            content_disposition = part.get_content_disposition()
            if content_disposition != 'attachment':
                continue

            # Get filename
            filename = part.get_filename()
            if not filename:
                continue

            # Decode filename (handles MIME-encoded headers like =?utf-8?Q?...?=)
            if isinstance(filename, bytes):
                filename = filename.decode('utf-8', errors='ignore')

            # Decode MIME-encoded header
            try:
                from email.header import decode_header
                decoded_parts = decode_header(filename)
                decoded_filename = ''
                for part_data, encoding in decoded_parts:
                    if isinstance(part_data, bytes):
                        decoded_filename += part_data.decode(encoding or 'utf-8', errors='ignore')
                    else:
                        decoded_filename += part_data
                filename = decoded_filename
            except (UnicodeDecodeError, LookupError):
                pass  # If decoding fails, use original filename

            # Clean filename (remove path separators)
            filename = filename.replace('/', '_').replace('\\', '_')

            # FILTER OUT EMAIL SIGNATURE/BANNER IMAGES
            # Skip common inline image patterns
            filename_lower = filename.lower()
            skip_patterns = [
                'image001', 'image002', 'image003', 'image004', 'image005',
                'image.png', 'image.jpg', 'image.gif', 'image.jpeg',
                'outlook-', 'facebook', 'linkedin', 'twitter', 'instagram',
                'logo.png', 'logo.jpg', 'signature', 'banner',
                'icon.png', 'icon.jpg', 'spacer.gif', 'pixel.gif',
                'attachment-', 'pastedimage',  # Common inline paste names
                'bensley logo', 'bds logo', 'company logo'  # Company signatures
            ]

            # Skip if matches any pattern
            if any(pattern in filename_lower for pattern in skip_patterns):
                continue

            # Skip all-numeric filenames (e.g., "1762867487977.png") - usually inline images
            import re
            if re.match(r'^\d+\.(png|jpg|jpeg|gif)$', filename_lower):
                continue

            # Get MIME type
            mime_type = part.get_content_type()

            # Get binary data
            try:
                payload = part.get_payload(decode=True)
            except Exception as e:
                print(f"      ⚠️  Error getting payload for {filename}: {e}")
                continue

            if not payload:
                continue

            # Skip very small images (likely logos/icons) - under 50KB
            if len(payload) < 50000:  # 50KB
                # If it's an image and small, skip it
                if any(ext in filename_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                    continue

            # Classify document type based on filename
            document_type = self.classify_document(filename, mime_type)

            # Full path to save
            filepath = os.path.join(save_dir, filename)

            # Handle duplicate filenames
            counter = 1
            base_name, ext = os.path.splitext(filename)
            original_filename = filename
            while os.path.exists(filepath):
                filename = f"{base_name}_{counter}{ext}"
                filepath = os.path.join(save_dir, filename)
                counter += 1

            # Save file
            try:
                if payload:
                    filesize = len(payload)

                    with open(filepath, 'wb') as f:
                        f.write(payload)

                    print(f"      📎 Saved: {filename} ({document_type})")

                    # Extract file type (extension without dot)
                    file_ext = os.path.splitext(filename)[1].lower().lstrip('.')

                    # Insert into database (corrected table and column names)
                    cursor.execute("""
                        INSERT INTO attachments
                        (email_id, filename, stored_path, file_size, file_type, mime_type, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (email_id, filename, filepath, filesize, file_ext, mime_type, document_type))

                    attachments.append({
                        'filename': filename,
                        'filepath': filepath,
                        'filesize': filesize,
                        'mime_type': mime_type,
                        'document_type': document_type
                    })

            except Exception as e:
                print(f"      ⚠️  Error saving {filename}: {e}")
                continue

        return attachments

    def classify_document(self, filename, mime_type):
        """
        Classify document type based on filename and MIME type

        Returns: document_type string
        """
        filename_lower = filename.lower()

        # Contract patterns
        if any(x in filename_lower for x in ['contract', 'agreement', 'sow', 'mou', 'nda', 'fidic']):
            return 'external_contract'  # Default to external, can be updated later

        # Proposal patterns
        if any(x in filename_lower for x in ['proposal', 'quotation', 'quote']):
            return 'proposal'

        # Invoice patterns
        if any(x in filename_lower for x in ['invoice', 'receipt', 'payment']):
            return 'invoice'

        # Design patterns
        if any(x in filename_lower for x in ['.dwg', '.skp', '.3dm', '.rvt']) or \
           any(x in filename_lower for x in ['design', 'drawing', 'plan', 'elevation', 'section']):
            return 'design_document'

        # Presentation patterns
        if any(x in filename_lower for x in ['.ppt', '.key']) or 'presentation' in filename_lower:
            return 'presentation'

        # Financial patterns
        if any(x in filename_lower for x in ['financial', 'budget', 'cost', 'estimate']):
            return 'financial'

        # Default
        return 'correspondence'

    def close(self):
        """Close IMAP connection"""
        try:
            self.imap.close()
            self.imap.logout()
            print("✅ Connection closed")
        except Exception:
            pass  # Connection may already be closed

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
