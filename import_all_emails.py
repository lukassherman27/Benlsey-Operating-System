#!/usr/bin/env python3
"""
Import ALL emails from INBOX and Sent - Non-interactive
"""
import sys
from backend.services.email_importer import EmailImporter

def main():
    print("=" * 80, flush=True)
    print("IMPORTING ALL EMAILS (INBOX + Sent)", flush=True)
    print("=" * 80, flush=True)

    importer = EmailImporter()

    if not importer.connect():
        print("\n❌ Connection failed")
        return

    # Import ALL from INBOX
    print("\n📥 INBOX: Importing ALL emails (no limit)...")
    inbox_count = importer.import_emails('INBOX', limit=None)

    # Import ALL from Sent
    print("\n📤 Sent: Importing ALL emails (no limit)...")
    sent_count = importer.import_emails('Sent', limit=None)

    print("\n" + "=" * 80)
    print("✅ COMPLETE")
    print(f"   INBOX: {inbox_count} new emails")
    print(f"   Sent: {sent_count} new emails")
    print("=" * 80)

    importer.imap.logout()

if __name__ == "__main__":
    main()
