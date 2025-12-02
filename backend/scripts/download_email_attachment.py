#!/usr/bin/env python3
"""
Download attachment from a specific email by message_id
"""

import imaplib
import email
from email.header import decode_header
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Email credentials
EMAIL_SERVER = os.getenv('EMAIL_SERVER')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 993))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
DB_PATH = os.getenv('DATABASE_PATH')
ATTACHMENTS_DIR = '/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE'

TARGET_MESSAGE_ID = '<A9B966B3-B03D-4AFD-B980-95FBDC0E76B0@bensley.com>'
TARGET_EMAIL_ID = 2024966

def connect_imap():
    """Connect to IMAP server"""
    print(f"Connecting to {EMAIL_SERVER}:{EMAIL_PORT}...")
    imap = imaplib.IMAP4_SSL(EMAIL_SERVER, EMAIL_PORT)
    imap.login(EMAIL_USER, EMAIL_PASSWORD)
    print("✅ Connected successfully!")
    return imap

def save_all_parts(msg, email_date, email_id, cursor, prefix=""):
    """
    Recursively save ALL parts of an email, including nested parts in forwarded messages
    """
    attachments = []

    # Create date-based subdirectory
    date_folder = email_date.strftime('%Y-%m')
    save_dir = os.path.join(ATTACHMENTS_DIR, date_folder)
    os.makedirs(save_dir, exist_ok=True)

    part_num = 0
    for part in msg.walk():
        part_num += 1

        # Get content type and disposition
        content_type = part.get_content_type()
        content_disposition = str(part.get_content_disposition())

        print(f"  {prefix}Part {part_num}: {content_type}, disposition={content_disposition}")

        # Try to get filename from multiple sources
        filename = part.get_filename()

        # Also check Content-Type header for name parameter (some emails use this)
        if not filename:
            content_type_header = part.get('Content-Type', '')
            if 'name=' in content_type_header:
                # Extract name from Content-Type
                import re
                match = re.search(r'name="([^"]+)"', content_type_header)
                if match:
                    filename = match.group(1)

        # If we have a filename, save it
        if filename:
            # Decode filename
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

            print(f"    → Found attachment: {filename}")

            # Get payload
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    # Save file
                    filepath = os.path.join(save_dir, filename)

                    # Handle duplicate filenames
                    counter = 1
                    base_name, ext = os.path.splitext(filename)
                    while os.path.exists(filepath):
                        filename = f"{base_name}_{counter}{ext}"
                        filepath = os.path.join(save_dir, filename)
                        counter += 1

                    with open(filepath, 'wb') as f:
                        f.write(payload)

                    filesize = len(payload)
                    mime_type = part.get_content_type()

                    print(f"    ✅ Saved: {filepath} ({filesize} bytes)")

                    # Insert into database
                    cursor.execute("""
                        INSERT INTO email_attachments
                        (email_id, filename, filepath, filesize, mime_type, document_type)
                        VALUES (?, ?, ?, ?, ?, 'other')
                    """, (email_id, filename, filepath, filesize, mime_type))

                    attachments.append({
                        'filename': filename,
                        'filepath': filepath,
                        'size': filesize
                    })
            except Exception as e:
                print(f"    ❌ Error saving attachment: {e}")

    return attachments

def main():
    # Connect to IMAP
    imap = connect_imap()

    # Search for the message
    print(f"\n📧 Searching for message: {TARGET_MESSAGE_ID}")

    imap.select('INBOX')

    # Search by Message-ID
    status, messages = imap.search(None, f'HEADER Message-ID "{TARGET_MESSAGE_ID}"')

    if status != 'OK' or not messages[0]:
        print("❌ Email not found!")
        imap.logout()
        return

    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} message(s)")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get email date from database
    cursor.execute("SELECT date FROM emails WHERE email_id = ?", (TARGET_EMAIL_ID,))
    result = cursor.fetchone()
    if result:
        email_date = datetime.fromisoformat(result[0].replace('Z', '+00:00'))
    else:
        email_date = datetime.now()

    # Fetch and process the email
    for email_id in email_ids:
        print(f"\n📥 Fetching email {email_id.decode()}...")

        status, msg_data = imap.fetch(email_id, '(RFC822)')

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Parse email
                msg = email.message_from_bytes(response_part[1])

                print(f"\nEmail structure:")
                print(f"  Subject: {msg['Subject']}")
                print(f"  From: {msg['From']}")
                print(f"  Is multipart: {msg.is_multipart()}")

                # Save all parts recursively
                attachments = save_all_parts(msg, email_date, TARGET_EMAIL_ID, cursor)

                # Update has_attachments flag
                if attachments:
                    cursor.execute("""
                        UPDATE emails SET has_attachments = 1 WHERE email_id = ?
                    """, (TARGET_EMAIL_ID,))

                    print(f"\n✅ Saved {len(attachments)} attachment(s):")
                    for att in attachments:
                        print(f"   - {att['filename']} ({att['size']} bytes)")
                else:
                    print("\n⚠️  No attachments found in this email")

    conn.commit()
    conn.close()
    imap.logout()

    print("\n✅ Done!")

if __name__ == "__main__":
    main()
