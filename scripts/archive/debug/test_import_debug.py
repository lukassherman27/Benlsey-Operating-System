#!/usr/bin/env python3
"""Debug email import"""
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("Step 1: Importing EmailImporter class...")
from backend.services.email_importer import EmailImporter

print("Step 2: Creating importer instance...")
importer = EmailImporter()

print(f"Step 3: Server config: {importer.server}:{importer.port}")
print(f"         Username: {importer.username}")

print("Step 4: Calling connect()...")
result = importer.connect()

print(f"Step 5: Connection result: {result}")

if result:
    print("Step 6: Getting folder list...")
    folders = importer.get_folders()
    print(f"Step 7: Found {len(folders)} folders")

    print("Step 8: Selecting INBOX...")
    status, messages = importer.imap.search(None, 'ALL')
    email_ids = messages[0].split()
    print(f"Step 9: Found {len(email_ids)} emails in INBOX")

    print("Step 10: Starting import of 10 emails...")
    count = importer.import_emails('INBOX', limit=10)
    print(f"Step 11: Imported {count} emails")

    importer.close()
else:
    print("Connection failed!")
