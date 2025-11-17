#!/usr/bin/env python3
"""
Import Invoice Line Items for 25 BK-040
Extracted from "Project Status as of 10 Nov 25 (Updated).pdf"
"""

import sqlite3
from datetime import datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# Invoice line item for 25 BK-040
# From PDF page 11: The Ritz Carlton Reserve, Nusa Dua, Bali - Branding Consultancy Service
INVOICE_ITEMS = [
    {
        'project_code': '25 BK-040',
        'invoice_number': 'I25-094',
        'invoice_date': '2025-09-29',
        'description': 'Mobilization Fee',
        'amount': 31250.00,
        'percentage': None,
        'outstanding': 0.00,
        'remaining': 0.00,
        'paid': 31250.00,
        'date_paid': None,  # Not specified in PDF
    },
    # Note: The PDF shows "Step 1-3" with $31,250 remaining but no invoice number
    # This appears to be future work, not an invoice yet
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("IMPORTING INVOICE LINE ITEMS FOR 25 BK-040")
    print("Source: Project Status as of 10 Nov 25 (Updated).pdf")
    print("=" * 80)
    print()

    # Get proposal_id for 25 BK-040
    cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", ('25 BK-040',))
    result = cursor.fetchone()

    if not result:
        print("ERROR: Project 25 BK-040 not found in database!")
        conn.close()
        return

    proposal_id = result[0]
    print(f"Found proposal_id: {proposal_id} for project 25 BK-040")
    print()

    inserted = 0
    skipped = 0

    for item in INVOICE_ITEMS:
        # Check if invoice already exists
        cursor.execute("""
            SELECT invoice_id FROM invoices
            WHERE project_id = ? AND invoice_number = ?
        """, (proposal_id, item['invoice_number']))

        if cursor.fetchone():
            print(f"⊘ SKIPPED {item['invoice_number']}: Already exists")
            skipped += 1
            continue

        # Determine status based on payment
        status = 'Paid' if item['paid'] > 0 and item['outstanding'] == 0 else 'Partial' if item['paid'] > 0 else 'Outstanding'

        # Insert invoice
        cursor.execute("""
            INSERT INTO invoices (
                project_id,
                invoice_number,
                invoice_date,
                description,
                invoice_amount,
                payment_amount,
                payment_date,
                status,
                notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proposal_id,
            item['invoice_number'],
            item['invoice_date'],
            item['description'],
            item['amount'],
            item['paid'],
            item['date_paid'],
            status,
            f"Branding Consultancy Service - Imported from November 2025 project status report"
        ))

        print(f"✓ INSERTED {item['invoice_number']}: {item['description']}")
        print(f"  Amount: ${item['amount']:,.2f}")
        print(f"  Paid: ${item['paid']:,.2f}")
        print(f"  Status: {status}")
        print()

        inserted += 1

    conn.commit()
    conn.close()

    print("=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Inserted: {inserted} invoice line items")
    print(f"Skipped: {skipped} (already exist)")
    print()
    print("✅ Import complete!")

if __name__ == "__main__":
    main()
