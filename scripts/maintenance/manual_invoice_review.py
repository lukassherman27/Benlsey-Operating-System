#!/usr/bin/env python3
"""
Manual Invoice Review Tool

Review and selectively import invoices from Desktop → OneDrive
"""
import sqlite3
import csv
from datetime import datetime

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "database/bensley_master.db"

def export_invoices_for_review():
    """Export all Desktop invoices to CSV for manual review"""

    print("="*100)
    print("EXPORTING INVOICES FOR MANUAL REVIEW")
    print("="*100)

    desktop_conn = sqlite3.connect(DESKTOP_DB)
    onedrive_conn = sqlite3.connect(ONEDRIVE_DB)

    desktop_conn.row_factory = sqlite3.Row
    onedrive_conn.row_factory = sqlite3.Row

    desktop_cursor = desktop_conn.cursor()
    onedrive_cursor = onedrive_conn.cursor()

    # Get Desktop invoice IDs
    desktop_cursor.execute("SELECT invoice_id FROM invoices")
    desktop_invoice_ids = {row[0] for row in desktop_cursor.fetchall()}

    # Get OneDrive invoice IDs
    onedrive_cursor.execute("SELECT invoice_id FROM invoices")
    onedrive_invoice_ids = {row[0] for row in onedrive_cursor.fetchall()}

    # Find invoices only in Desktop
    desktop_only_invoices = desktop_invoice_ids - onedrive_invoice_ids

    print(f"\nFound {len(desktop_only_invoices)} invoices in Desktop not in OneDrive")

    # Get all OneDrive project codes for reference
    onedrive_cursor.execute("SELECT project_code, project_title FROM projects ORDER BY project_code")
    onedrive_projects = {row['project_code']: row['project_title'] for row in onedrive_cursor.fetchall()}

    print(f"OneDrive has {len(onedrive_projects)} projects available")

    # Get full details of Desktop-only invoices
    placeholders = ','.join(['?' for _ in desktop_only_invoices])
    desktop_cursor.execute(f"""
        SELECT
            invoice_id,
            project_code,
            invoice_number,
            description,
            invoice_date,
            invoice_amount,
            payment_amount,
            payment_date,
            status,
            discipline,
            phase
        FROM invoices
        WHERE invoice_id IN ({placeholders})
        ORDER BY invoice_date DESC
    """, list(desktop_only_invoices))

    invoices = desktop_cursor.fetchall()

    # Export to CSV
    csv_file = 'invoices_to_review.csv'
    print(f"\nExporting to {csv_file}...")

    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'IMPORT?',
            'invoice_id',
            'invoice_number',
            'invoice_date',
            'invoice_amount',
            'payment_amount',
            'payment_date',
            'status',
            'project_code_desktop',
            'project_in_onedrive?',
            'new_project_code',
            'discipline',
            'phase',
            'description'
        ])

        # Data
        for inv in invoices:
            project_code = inv['project_code']
            in_onedrive = 'YES' if project_code in onedrive_projects else 'NO'

            writer.writerow([
                '',  # IMPORT? - user fills this in
                inv['invoice_id'],
                inv['invoice_number'],
                inv['invoice_date'],
                inv['invoice_amount'],
                inv['payment_amount'],
                inv['payment_date'],
                inv['status'],
                project_code,
                in_onedrive,
                '',  # new_project_code - user fills if different
                inv['discipline'],
                inv['phase'],
                inv['description']
            ])

    print(f"\n✅ Exported {len(invoices)} invoices to {csv_file}")

    # Also export OneDrive projects list for reference
    projects_file = 'onedrive_projects_reference.csv'
    print(f"\nExporting OneDrive projects to {projects_file}...")

    with open(projects_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['project_code', 'project_title'])

        for code, title in sorted(onedrive_projects.items()):
            writer.writerow([code, title])

    print(f"✅ Exported {len(onedrive_projects)} OneDrive projects")

    print(f"""
{'='*100}
INSTRUCTIONS
{'='*100}

1. Open {csv_file} in Excel/Google Sheets

2. For each invoice:
   - Column A (IMPORT?): Type "YES" to import, leave blank to skip
   - Column I (project_in_onedrive?): Shows if Desktop project exists in OneDrive
   - Column J (new_project_code): If project doesn't exist, enter OneDrive project code to link to
                                  (see {projects_file} for available codes)

3. EXAMPLE:
   Invoice I13-150 for "13 BK-057" project:
   - If "13 BK-057" exists in OneDrive → Just mark IMPORT? = YES
   - If "13 BK-057" NOT in OneDrive but you want to link to "24 BK-057" →
     Mark IMPORT? = YES and new_project_code = 24 BK-057

4. Save the CSV when done

5. Run: python3 import_reviewed_invoices.py

The system will import only invoices marked YES and link them to the correct projects.
    """)

    desktop_conn.close()
    onedrive_conn.close()

if __name__ == '__main__':
    export_invoices_for_review()
