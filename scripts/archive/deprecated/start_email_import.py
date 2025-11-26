#!/usr/bin/env python3
"""
Start Email Import - Test connection and import emails
"""
import sys
import os
from dotenv import load_dotenv
from backend.services.email_importer import EmailImporter

load_dotenv()

def main():
    print("=" * 80)
    print("BENSLEY EMAIL IMPORT - Server Connection Test")
    print("=" * 80)

    # Check environment variables
    print("\n1️⃣  Checking configuration...")
    server = os.getenv('EMAIL_SERVER')
    port = os.getenv('EMAIL_PORT', 993)
    user = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')
    db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

    if not all([server, user, password]):
        print("❌ Missing email configuration!")
        print("\nRequired in .env file:")
        print("  EMAIL_SERVER=your.server.com")
        print("  EMAIL_PORT=993")
        print("  EMAIL_USER=your@email.com")
        print("  EMAIL_PASSWORD=yourpassword")
        print("  DATABASE_PATH=database/bensley_master.db")
        return

    print(f"   Server: {server}:{port}")
    print(f"   User: {user}")
    print(f"   Database: {db_path}")
    print("   ✅ Configuration loaded")

    # Initialize importer
    print("\n2️⃣  Connecting to email server...")
    importer = EmailImporter()

    if not importer.connect():
        print("\n❌ Connection failed. Check your credentials and server status.")
        return

    # List folders
    print("\n3️⃣  Listing email folders...")
    folders = importer.get_folders()

    # Ask user what to import
    print("\n4️⃣  What would you like to do?")
    print("   1. Import last 50 emails from INBOX")
    print("   2. Import last 100 emails from INBOX")
    print("   3. Import last 500 emails from INBOX")
    print("   4. Import ALL emails from INBOX (may take a while)")
    print("   5. Just test connection (done)")

    choice = input("\nChoice (1-5): ").strip()

    limits = {
        '1': 50,
        '2': 100,
        '3': 500,
        '4': None  # No limit
    }

    if choice in limits:
        limit = limits[choice]
        print(f"\n5️⃣  Importing emails (limit: {limit or 'all'})...")
        importer.import_emails('INBOX', limit=limit)
        print("\n✅ Import complete!")
    else:
        print("\n✅ Connection test successful. Closing.")

    importer.imap.logout()
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
