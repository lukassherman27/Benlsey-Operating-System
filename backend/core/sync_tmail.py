#!/usr/bin/env python3
"""
sync_tmail.py

Syncs emails from Tmail IMAP server to emails.db
"""

import imaplib
import email
from email.header import decode_header
import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

# Paths
DESKTOP = Path.home() / "Desktop"
BDS_DIR = DESKTOP / "BDS_SYSTEM"
DB_DIR = BDS_DIR / "01_DATABASES"
SCRIPTS_DIR = BDS_DIR / "02_SCRIPTS"

EMAILS_DB = DB_DIR / "emails.db"
CONFIG_FILE = BDS_DIR / "OLD_SCRIPTS" / "email_config.json"

def load_config():
    """Load email configuration"""
    if not CONFIG_FILE.exists():
        # Try alternate location
        alt_config = SCRIPTS_DIR / "email_config.json"
        if alt_config.exists():
            config_path = alt_config
        else:
            raise FileNotFoundError(f"Config not found at {CONFIG_FILE} or {alt_config}")
    else:
        config_path = CONFIG_FILE
    
    with open(config_path, 'r') as f:
        return json.load(f)

def connect_to_imap(config):
    """Connect to IMAP server"""
    print(f"\n🔗 Connecting to {config['email_server']}...")
    
    if config['use_ssl']:
        mail = imaplib.IMAP4_SSL(config['email_server'], config['email_port'])
    else:
        mail = imaplib.IMAP4(config['email_server'], config['email_port'])
    
    mail.login(config['email_username'], config['email_password'])
    print("✅ Connected successfully")
    
    return mail

def decode_mime_words(s):
    """Decode MIME encoded strings"""
    if s is None:
        return ""
    decoded_parts = decode_header(s)
    decoded_string = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
        else:
            decoded_string += part
    return decoded_string

def get_existing_message_ids(conn):
    """Get all existing message IDs from database"""
    cursor = conn.cursor()
    cursor.execute("SELECT message_id FROM emails")
    return set(row[0] for row in cursor.fetchall())

def fetch_and_store_emails(mail, db_conn):
    """Fetch NEW emails from IMAP and store in database"""
    
    # Select inbox
    mail.select('INBOX')
    
    # Get existing message IDs
    existing_ids = get_existing_message_ids(db_conn)
    print(f"📊 Found {len(existing_ids)} existing emails in database")
    
    # Search for emails from last 7 days
    from datetime import datetime, timedelta
    since_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    
    status, messages = mail.search(None, f'(SINCE {since_date})')
    email_ids = messages[0].split()
    
    if not email_ids or email_ids == [b'']:
        print("✅ No emails found from last 7 days")
        return 0
    
    print(f"📧 Found {len(email_ids)} emails from last 7 days on server")
    print(f"🔄 Checking for new emails...")
    
    new_count = 0
    cursor = db_conn.cursor()
    
    for i, email_id in enumerate(email_ids, 1):
        if i % 10 == 0:
            print(f"   Processing {i}/{len(email_ids)}...")
        
        # Fetch email
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Parse email
                msg = email.message_from_bytes(response_part[1])
                
                # Extract fields
                message_id = msg.get('Message-ID', f'<no-id-{email_id}>')
                
                # Skip if already in database
                if message_id in existing_ids:
                    continue
                
                thread_id = msg.get('In-Reply-To', '')
                subject = decode_mime_words(msg.get('Subject', ''))
                sender_email = msg.get('From', '')
                sender_name = decode_mime_words(email.utils.parseaddr(sender_email)[0])
                sender_email = email.utils.parseaddr(sender_email)[1]
                
                recipients = msg.get('To', '')
                cc = msg.get('Cc', '')
                date_sent = msg.get('Date', '')
                
                # Extract body
                body_text = ""
                body_html = ""
                
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            try:
                                body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except:
                                pass
                        elif content_type == "text/html":
                            try:
                                body_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except:
                                pass
                else:
                    try:
                        body_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        body_text = str(msg.get_payload())
                
                # Check for attachments
                has_attachments = 0
                attachment_count = 0
                
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_disposition() == 'attachment':
                            has_attachments = 1
                            attachment_count += 1
                
                # Insert into database
                try:
                    cursor.execute("""
                        INSERT INTO emails (
                            message_id, thread_id, sender_email, sender_name,
                            recipients, cc, subject, body_text, body_html,
                            date_sent, date_received, has_attachments, attachment_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?)
                    """, (
                        message_id, thread_id, sender_email, sender_name,
                        recipients, cc, subject, body_text[:5000], body_html[:5000],
                        date_sent, has_attachments, attachment_count
                    ))
                    
                    new_count += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Error storing email: {e}")
    
    db_conn.commit()
    
    return new_count

def main():
    print("="*70)
    print("TMAIL EMAIL SYNC")
    print("="*70)
    
    # Load config
    config = load_config()
    
    # Connect to IMAP
    try:
        mail = connect_to_imap(config)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Connect to database
    db_conn = sqlite3.connect(EMAILS_DB)
    
    # Fetch emails
    try:
        new_count = fetch_and_store_emails(mail, db_conn)
        
        print("\n" + "="*70)
        print("SYNC COMPLETE")
        print("="*70)
        print(f"✅ Added {new_count} new emails")
        
        if new_count > 0:
            print("\n💡 Next steps:")
            print("   1. Sync to master: python3 ACTIVE/sync_master.py")
            print("   2. Process emails: python3 ACTIVE/email_processor.py")
        
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        mail.logout()
        db_conn.close()

if __name__ == '__main__':
    main()