#!/usr/bin/env python3
"""
Import Reviewed Invoices

Imports invoices marked YES in the review CSV
"""
import sqlite3
import csv
import os
from datetime import datetime

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "database/bensley_master.db"
REVIEW_CSV = 'invoices_to_review.csv'

def import_reviewed_invoices():
    """Import invoices that user marked YES"""

    print("="*100)
    print("IMPORTING REVIEWED INVOICES")
    print("="*100)

    if not os.path.exists(REVIEW_CSV):
        print(f"❌ ERROR: {REVIEW_CSV} not found!")
        print("Run manual_invoice_review.py first to generate it.")
        return

    # Read reviewed CSV
    print(f"\nReading {REVIEW_CSV}...")

    to_import = []
    with open(REVIEW_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['IMPORT?'].strip().upper() == 'YES':
                to_import.append(row)

    if not to_import:
        print("❌ No invoices marked YES for import!")
        print("Open invoices_to_review.csv and mark invoices to import.")
        return

    print(f"✅ Found {len(to_import)} invoices marked YES")

    # Backup
    print("\nCreating backup...")
    backup_path = f"database/backups/bensley_master_pre_invoice_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.makedirs("database/backups", exist_ok=True)
    os.system(f"cp {ONEDRIVE_DB} {backup_path}")
    print(f"✅ Backup: {backup_path}")

    # Connect
    print("\nConnecting to databases...")
    desktop_conn = sqlite3.connect(DESKTOP_DB)
    onedrive_conn = sqlite3.connect(ONEDRIVE_DB)

    desktop_conn.row_factory = sqlite3.Row
    desktop_cursor = desktop_conn.cursor()
    onedrive_cursor = onedrive_conn.cursor()
    print("✅ Connected")

    # Get OneDrive invoice schema
    onedrive_cursor.execute("PRAGMA table_info(invoices)")
    onedrive_cols = [col[1] for col in onedrive_cursor.fetchall()]

    # Get Desktop invoice schema
    desktop_cursor.execute("PRAGMA table_info(invoices)")
    desktop_cols = [col[1] for col in desktop_cursor.fetchall()]

    # Common columns
    common_cols = [col for col in desktop_cols if col in onedrive_cols]

    print(f"\nWill use {len(common_cols)} common columns")

    # Get OneDrive projects for validation
    onedrive_cursor.execute("SELECT project_id, project_code FROM projects")
    onedrive_projects = {row[1]: row[0] for row in onedrive_cursor.fetchall()}

    # Import each invoice
    print(f"\nImporting {len(to_import)} invoices...")
    print("="*100)

    imported = 0
    skipped = 0
    errors = []

    for row in to_import:
        invoice_id = row['invoice_id']

        # Determine project code to use
        if row['new_project_code'].strip():
            # User specified a different project code
            project_code = row['new_project_code'].strip()
        else:
            # Use original project code
            project_code = row['project_code_desktop'].strip()

        # Validate project exists in OneDrive
        if project_code not in onedrive_projects:
            skipped += 1
            errors.append(f"Invoice {row['invoice_number']}: Project {project_code} not found in OneDrive")
            continue

        # Get full invoice data from Desktop
        desktop_cursor.execute(f"SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
        desktop_invoice = desktop_cursor.fetchone()

        if not desktop_invoice:
            skipped += 1
            errors.append(f"Invoice {invoice_id}: Not found in Desktop database")
            continue

        # Build insert statement using common columns
        invoice_dict = dict(desktop_invoice)

        # Update project_id to OneDrive project_id
        if 'project_id' in common_cols:
            invoice_dict['project_id'] = onedrive_projects[project_code]

        # Update project_code if user changed it
        if 'project_code' in common_cols:
            invoice_dict['project_code'] = project_code

        # Insert into OneDrive
        try:
            cols = [col for col in common_cols if col in invoice_dict]
            values = [invoice_dict[col] for col in cols]

            placeholders = ','.join(['?' for _ in cols])
            cols_str = ','.join(cols)

            onedrive_cursor.execute(f"""
                INSERT OR REPLACE INTO invoices ({cols_str})
                VALUES ({placeholders})
            """, values)

            imported += 1
            print(f"✅ {row['invoice_number']}: ${row['invoice_amount']} → {project_code} | {row['status']}")

        except Exception as e:
            skipped += 1
            errors.append(f"Invoice {row['invoice_number']}: {str(e)}")

    # Summary
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"✅ Imported: {imported}")
    print(f"⚠️  Skipped: {skipped}")

    if errors:
        print(f"\n❌ ERRORS:")
        for error in errors[:10]:
            print(f"   • {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")

    # Verify
    print("\n" + "="*100)
    print("VERIFICATION")
    print("="*100)

    onedrive_cursor.execute("SELECT COUNT(*) FROM invoices")
    total_invoices = onedrive_cursor.fetchone()[0]

    onedrive_cursor.execute("SELECT COUNT(*) FROM invoices WHERE status='outstanding'")
    outstanding_count = onedrive_cursor.fetchone()[0]

    onedrive_cursor.execute("SELECT SUM(invoice_amount - COALESCE(payment_amount, 0)) FROM invoices WHERE status='outstanding'")
    outstanding_amount = onedrive_cursor.fetchone()[0] or 0

    print(f"OneDrive now has:")
    print(f"   Total invoices: {total_invoices}")
    print(f"   Outstanding: {outstanding_count} invoices, ${outstanding_amount:,.0f}")

    print(f"\n✅ Backup saved: {backup_path}")

    # Commit
    print("\nCommit changes? (yes/no): ", end="")
    import sys
    response = sys.stdin.readline().strip().lower()

    if response == 'yes':
        onedrive_conn.commit()
        print("\n✅ IMPORT COMPLETE!")
    else:
        onedrive_conn.rollback()
        print("\n❌ CANCELLED - No changes made")

    desktop_conn.close()
    onedrive_conn.close()

if __name__ == '__main__':
    import_reviewed_invoices()
