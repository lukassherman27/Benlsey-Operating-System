#!/usr/bin/env python3
"""Import ALL emails with proper output buffering"""
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

from backend.services.email_importer import EmailImporter

print("=" * 80, flush=True)
print("IMPORTING ALL EMAILS (INBOX + Sent)", flush=True)
print("=" * 80, flush=True)

importer = EmailImporter()

if not importer.connect():
    print("\n❌ Connection failed", flush=True)
    sys.exit(1)

# Import ALL from INBOX
print("\n📥 INBOX: Importing ALL emails (no limit)...", flush=True)
inbox_count = importer.import_emails('INBOX', limit=None)

# Import ALL from Sent
print("\n📤 Sent: Importing ALL emails (no limit)...", flush=True)
sent_count = importer.import_emails('Sent', limit=None)

print("\n" + "=" * 80, flush=True)
print("✅ COMPLETE", flush=True)
print(f"   INBOX: {inbox_count} new emails", flush=True)
print(f"   Sent: {sent_count} new emails", flush=True)
print("=" * 80, flush=True)

importer.close()
