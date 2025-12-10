#!/usr/bin/env python3
"""
Backfill Attachments - Download and link attachments for emails that are flagged
but don't have attachment records in the database.
"""

import imaplib
import email
from email.header import decode_header
import sqlite3
import os
import sys
import re
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Config
DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
EMAIL_SERVER = os.getenv('EMAIL_SERVER')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 993))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
ATTACHMENTS_DIR = '/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE'


def decode_header_value(header):
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


def classify_document(filename, mime_type):
    """Classify document type based on filename"""
    filename_lower = filename.lower()

    if any(x in filename_lower for x in ['contract', 'agreement', 'sow', 'mou', 'nda', 'fidic']):
        return 'external_contract'
    if any(x in filename_lower for x in ['proposal', 'quotation', 'quote']):
        return 'proposal'
    if any(x in filename_lower for x in ['invoice', 'receipt', 'payment']):
        return 'invoice'
    if any(x in filename_lower for x in ['.dwg', '.skp', '.3dm', '.rvt', 'design', 'drawing', 'plan', 'elevation', 'section']):
        return 'design_document'
    if any(x in filename_lower for x in ['.ppt', '.key', 'presentation']):
        return 'presentation'
    if any(x in filename_lower for x in ['financial', 'budget', 'cost', 'estimate']):
        return 'financial'
    return 'correspondence'


def save_attachments(msg, email_date, email_id, cursor):
    """Extract and save email attachments"""
    attachments = []

    if not msg.is_multipart():
        return attachments

    # Create date-based subdirectory
    date_folder = email_date.strftime('%Y-%m')
    save_dir = os.path.join(ATTACHMENTS_DIR, date_folder)
    os.makedirs(save_dir, exist_ok=True)

    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue

        content_disposition = part.get_content_disposition()
        if content_disposition != 'attachment':
            continue

        filename = part.get_filename()
        if not filename:
            continue

        # Decode filename
        if isinstance(filename, bytes):
            filename = filename.decode('utf-8', errors='ignore')

        try:
            decoded_parts = decode_header(filename)
            decoded_filename = ''
            for part_data, encoding in decoded_parts:
                if isinstance(part_data, bytes):
                    decoded_filename += part_data.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_filename += part_data
            filename = decoded_filename
        except:
            pass

        filename = filename.replace('/', '_').replace('\\', '_')

        # Skip signature images
        filename_lower = filename.lower()
        skip_patterns = [
            'image001', 'image002', 'image003', 'image004', 'image005',
            'image.png', 'image.jpg', 'image.gif', 'image.jpeg',
            'outlook-', 'facebook', 'linkedin', 'twitter', 'instagram',
            'logo.png', 'logo.jpg', 'signature', 'banner',
            'icon.png', 'icon.jpg', 'spacer.gif', 'pixel.gif',
            'attachment-', 'pastedimage', 'bensley logo', 'bds logo', 'company logo'
        ]

        if any(pattern in filename_lower for pattern in skip_patterns):
            continue

        if re.match(r'^\d+\.(png|jpg|jpeg|gif)$', filename_lower):
            continue

        mime_type = part.get_content_type()

        try:
            payload = part.get_payload(decode=True)
        except Exception as e:
            continue

        if not payload:
            continue

        # Skip small images (likely logos)
        if len(payload) < 50000:
            if any(ext in filename_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                continue

        document_type = classify_document(filename, mime_type)
        filepath = os.path.join(save_dir, filename)

        # Handle duplicates
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(filepath):
            filename = f"{base_name}_{counter}{ext}"
            filepath = os.path.join(save_dir, filename)
            counter += 1

        try:
            filesize = len(payload)
            with open(filepath, 'wb') as f:
                f.write(payload)

            file_ext = os.path.splitext(filename)[1].lower().lstrip('.')

            cursor.execute("""
                INSERT INTO email_attachments
                (email_id, filename, filepath, filesize, mime_type, document_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (email_id, filename, filepath, filesize, mime_type, document_type))

            attachments.append({
                'filename': filename,
                'filepath': filepath,
                'filesize': filesize,
                'document_type': document_type
            })

            print(f"      📎 {filename} ({document_type}, {filesize//1024}KB)")

        except Exception as e:
            print(f"      ⚠️ Error: {e}")
            continue

    return attachments


def main():
    print("="*70)
    print("ATTACHMENT BACKFILL")
    print("="*70)

    # Get emails missing attachments
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.email_id, e.message_id, e.subject, e.date, e.folder
        FROM emails e
        WHERE e.has_attachments = 1
        AND e.email_id NOT IN (SELECT DISTINCT email_id FROM email_attachments)
        ORDER BY e.date DESC
    """)

    missing = cursor.fetchall()
    print(f"\n📧 Found {len(missing)} emails with attachments but no records\n")

    if not missing:
        print("Nothing to do!")
        return

    # Connect to IMAP
    print(f"Connecting to {EMAIL_SERVER}:{EMAIL_PORT}...")
    try:
        imap = imaplib.IMAP4_SSL(EMAIL_SERVER, EMAIL_PORT)
        imap.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        print("✅ Connected\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    processed = 0
    attachments_saved = 0

    # Group by folder
    by_folder = {}
    for email_id, message_id, subject, date_str, folder in missing:
        if folder not in by_folder:
            by_folder[folder] = []
        by_folder[folder].append((email_id, message_id, subject, date_str))

    for folder, emails in by_folder.items():
        print(f"\n📁 Processing {folder} ({len(emails)} emails)...")

        try:
            imap.select(folder)
        except Exception as e:
            print(f"   ⚠️ Can't select folder: {e}")
            continue

        for email_id, message_id, subject, date_str in emails:
            if processed >= 100:  # Batch limit
                print("\n⚠️ Reached batch limit of 100, run again for more")
                break

            print(f"\n   [{processed+1}] {subject[:50]}...")

            # Search by message ID
            search_criteria = f'HEADER Message-ID "{message_id}"'
            try:
                status, data = imap.search(None, search_criteria)
                if status != 'OK' or not data[0]:
                    # Try without quotes
                    status, data = imap.search(None, f'HEADER Message-ID {message_id}')
                    if status != 'OK' or not data[0]:
                        print(f"      ⚠️ Not found on server")
                        continue

                imap_id = data[0].split()[0]
                status, msg_data = imap.fetch(imap_id, '(RFC822)')

                if status != 'OK':
                    print(f"      ⚠️ Fetch failed")
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        # Parse date
                        try:
                            email_date = email.utils.parsedate_to_datetime(date_str)
                        except:
                            email_date = datetime.now()

                        # Save attachments
                        saved = save_attachments(msg, email_date, email_id, cursor)
                        attachments_saved += len(saved)

                        if not saved:
                            # Clear the flag if no real attachments
                            cursor.execute("UPDATE emails SET has_attachments = 0 WHERE email_id = ?", (email_id,))
                            print(f"      (no real attachments, cleared flag)")

                        processed += 1

            except Exception as e:
                print(f"      ⚠️ Error: {e}")
                continue

            # Commit every 10 emails
            if processed % 10 == 0:
                conn.commit()

    conn.commit()
    conn.close()

    try:
        imap.close()
        imap.logout()
    except:
        pass

    print(f"\n{'='*70}")
    print(f"✅ COMPLETE")
    print(f"   Processed: {processed} emails")
    print(f"   Attachments saved: {attachments_saved}")
    print(f"   Run again if more remain")
    print(f"{'='*70}")


if __name__ == '__main__':
    main()
