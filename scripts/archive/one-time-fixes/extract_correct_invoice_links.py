#!/usr/bin/env python3
"""
Extract the CORRECT invoice→project mappings from Bill's sheet and compare with database
"""

import pandas as pd
import sqlite3
import os
import re
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv('DATABASE_PATH', './database/bensley_master.db')

PROJECT_STATUS_EXCEL = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Project Status as of 17 Nov 25.xls"

def normalize_project_code(code):
    """Normalize project code variations"""
    if pd.isna(code) or not code:
        return None
    code = str(code).strip()
    # Remove spaces
    code = code.replace(' ', '')
    return code

def main():
    print("="*120)
    print("EXTRACT CORRECT INVOICE→PROJECT MAPPINGS")
    print("="*120)

    # Read Bill's Project Status-27 Oct 25 sheet
    print("\n[1/4] Reading 'Bill's Project Status-27 Oct 25' sheet...")
    try:
        df = pd.read_excel(PROJECT_STATUS_EXCEL, sheet_name="Bill's Project Status-27 Oct 25")
        print(f"  ✅ Loaded: {len(df)} rows")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return

    # Extract invoice→project mappings
    print("\n[2/4] Extracting invoice→project mappings...")

    mappings = []
    current_project_code = None
    current_project_title = None

    for idx, row in df.iterrows():
        # Check if this row contains a project code in column 1
        project_code_col = row.iloc[1] if len(row) > 1 else None
        if pd.notna(project_code_col):
            project_code_str = str(project_code_col).strip()
            # Check if it's a project code (contains "BK-")
            if 'BK-' in project_code_str:
                current_project_code = project_code_str
                # Get project title from column 3
                if len(row) > 3:
                    current_project_title = row.iloc[3] if pd.notna(row.iloc[3]) else None

        # Check if this row contains an invoice number in column 6
        if len(row) > 6:
            invoice_col = row.iloc[6]
            if pd.notna(invoice_col):
                invoice_str = str(invoice_col).strip()
                # Check if it looks like an invoice number (I##-###)
                if re.match(r'I\d{2}-\d{3}', invoice_str) or re.match(r'\d{2}-\d{3}', invoice_str):
                    # Get phase/description from column 4
                    phase = row.iloc[4] if len(row) > 4 and pd.notna(row.iloc[4]) else None
                    # Get amount from column 11 (paid)
                    amount = row.iloc[11] if len(row) > 11 and pd.notna(row.iloc[11]) else None

                    mappings.append({
                        'invoice_number': invoice_str,
                        'project_code': current_project_code,
                        'project_title': current_project_title,
                        'phase': phase,
                        'amount': amount
                    })

    print(f"  ✅ Found {len(mappings)} invoice→project mappings")

    # Show sample mappings
    print("\n  Sample mappings:")
    for m in mappings[:10]:
        print(f"    {m['invoice_number']} → {m['project_code']} ({m['project_title']})")

    # Connect to database and compare
    print("\n[3/4] Comparing with database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all invoices from database
    cursor.execute("""
        SELECT
            i.invoice_id,
            i.invoice_number,
            i.project_id,
            p.project_code,
            p.project_title
        FROM invoices i
        LEFT JOIN projects p ON i.project_id = p.project_id
        ORDER BY i.invoice_number
    """)
    db_invoices = {row[1]: row for row in cursor.fetchall()}  # invoice_number → row

    # Compare
    print(f"  Database has {len(db_invoices)} invoices")

    matches = []
    mismatches = []
    not_in_db = []

    for mapping in mappings:
        inv_num = mapping['invoice_number']
        expected_project = mapping['project_code']

        if inv_num not in db_invoices:
            not_in_db.append(mapping)
            continue

        db_row = db_invoices[inv_num]
        db_project_code = db_row[3]

        # Normalize both codes for comparison
        expected_normalized = normalize_project_code(expected_project)
        db_normalized = normalize_project_code(db_project_code)

        if expected_normalized == db_normalized:
            matches.append({
                'invoice': inv_num,
                'project_code': expected_project,
                'status': 'CORRECT ✅'
            })
        else:
            mismatches.append({
                'invoice': inv_num,
                'expected_project': expected_project,
                'expected_title': mapping['project_title'],
                'db_project': db_project_code,
                'db_title': db_row[4]
            })

    print(f"\n[4/4] Results:")
    print(f"  ✅ Correctly linked: {len(matches)}/{len(mappings)} ({len(matches)/len(mappings)*100:.1f}%)")
    print(f"  ❌ Incorrectly linked: {len(mismatches)}/{len(mappings)} ({len(mismatches)/len(mappings)*100:.1f}%)")
    print(f"  ⚠️  Not in database: {len(not_in_db)}/{len(mappings)}")

    # Show mismatches
    if mismatches:
        print(f"\n" + "="*120)
        print(f"INCORRECTLY LINKED INVOICES ({len(mismatches)} total)")
        print("="*120)

        for i, m in enumerate(mismatches[:20], 1):  # Show first 20
            print(f"\n[{i}] Invoice: {m['invoice']}")
            print(f"  ❌ Current DB: {m['db_project']} - {m['db_title']}")
            print(f"  ✅ Should be: {m['expected_project']} - {m['expected_title']}")

        if len(mismatches) > 20:
            print(f"\n  ... and {len(mismatches) - 20} more mismatches")

    # Save full results to file
    output_file = "database/INVOICE_LINK_COMPARISON.txt"
    with open(output_file, 'w') as f:
        f.write("="*120 + "\n")
        f.write("COMPLETE INVOICE LINK COMPARISON\n")
        f.write("="*120 + "\n\n")

        f.write(f"Total invoices in Excel: {len(mappings)}\n")
        f.write(f"Correctly linked: {len(matches)} ({len(matches)/len(mappings)*100:.1f}%)\n")
        f.write(f"Incorrectly linked: {len(mismatches)} ({len(mismatches)/len(mappings)*100:.1f}%)\n")
        f.write(f"Not in database: {len(not_in_db)}\n\n")

        f.write("="*120 + "\n")
        f.write("ALL MISMATCHES\n")
        f.write("="*120 + "\n\n")

        for m in mismatches:
            f.write(f"Invoice: {m['invoice']}\n")
            f.write(f"  Current DB: {m['db_project']} - {m['db_title']}\n")
            f.write(f"  Should be: {m['expected_project']} - {m['expected_title']}\n\n")

        f.write("\n" + "="*120 + "\n")
        f.write("INVOICES NOT IN DATABASE\n")
        f.write("="*120 + "\n\n")

        for m in not_in_db:
            f.write(f"Invoice: {m['invoice_number']}\n")
            f.write(f"  Project: {m['project_code']} - {m['project_title']}\n")
            f.write(f"  Phase: {m['phase']}\n")
            f.write(f"  Amount: {m['amount']}\n\n")

    print(f"\n✅ Full comparison saved to: {output_file}")

    conn.close()

if __name__ == '__main__':
    main()
