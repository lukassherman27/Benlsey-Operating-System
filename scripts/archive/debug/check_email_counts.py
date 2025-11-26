#!/usr/bin/env python3
"""
Check email counts in all folders
"""
from backend.services.email_importer import EmailImporter

importer = EmailImporter()
if importer.connect():
    folders = ['INBOX', 'Sent', 'Archive', 'Bensley finance ', 'New Business Development', 'RFPs ', 'Drafts']

    print("\n📊 EMAIL FOLDER COUNTS:")
    print("=" * 60)

    for folder in folders:
        try:
            importer.imap.select(folder, readonly=True)
            status, messages = importer.imap.search(None, 'ALL')
            count = len(messages[0].split()) if messages[0] else 0
            print(f"   {folder:30} {count:>6} emails")
        except Exception as e:
            print(f"   {folder:30}  Error: {e}")

    print("=" * 60)
    importer.imap.logout()
