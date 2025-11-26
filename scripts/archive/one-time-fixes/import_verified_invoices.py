#!/usr/bin/env python3
"""
Import verified invoices from CSV to database
Skips invoices without project codes
"""
import sqlite3
import csv
from datetime import datetime
from pathlib import Path

DB_PATH = "database/bensley_master.db"
CSV_PATH = "reports/invoices_for_review.csv"

def parse_date(date_str):
    """Parse date string to YYYY-MM-DD format"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        # Already in YYYY-MM-DD format
        return date_str.strip()
    except:
        return None

def import_invoices():
    """Import invoices from CSV to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Read CSV
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Statistics
    total_rows = len(rows)
    imported = 0
    skipped = 0
    skipped_list = []
    errors = []

    for row in rows:
        # Skip if no project code
        if not row['project_code'] or row['project_code'].strip() == '':
            skipped += 1
            skipped_list.append({
                'invoice_number': row['invoice_number'],
                'amount': row['invoice_amount'],
                'status': row['status'],
                'reason': 'Missing project_code'
            })
            continue

        # Check if project exists
        cursor.execute("""
            SELECT project_id FROM projects
            WHERE project_code = ?
        """, (row['project_code'],))
        project = cursor.fetchone()

        if not project:
            skipped += 1
            skipped_list.append({
                'invoice_number': row['invoice_number'],
                'amount': row['invoice_amount'],
                'status': row['status'],
                'reason': f"Project {row['project_code']} not found in database"
            })
            continue

        project_id = project[0]

        # Check if invoice already exists
        cursor.execute("""
            SELECT invoice_id FROM invoices
            WHERE invoice_number = ?
        """, (row['invoice_number'],))
        existing = cursor.fetchone()

        if existing:
            skipped += 1
            skipped_list.append({
                'invoice_number': row['invoice_number'],
                'amount': row['invoice_amount'],
                'status': row['status'],
                'reason': 'Invoice number already exists'
            })
            continue

        # Parse amounts
        try:
            invoice_amount = float(row['invoice_amount']) if row['invoice_amount'] else 0.0
            payment_amount = float(row['payment_amount']) if row['payment_amount'] else 0.0
        except ValueError:
            errors.append(f"Invalid amount for {row['invoice_number']}")
            continue

        # Parse dates
        invoice_date = parse_date(row['invoice_date'])
        payment_date = parse_date(row['payment_date'])

        # Determine status
        status = 'paid' if payment_amount > 0 else 'outstanding'

        # Insert invoice
        try:
            cursor.execute("""
                INSERT INTO invoices (
                    project_id,
                    invoice_number,
                    invoice_date,
                    invoice_amount,
                    payment_date,
                    payment_amount,
                    phase,
                    discipline,
                    notes,
                    status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                project_id,
                row['invoice_number'],
                invoice_date,
                invoice_amount,
                payment_date,
                payment_amount,
                row.get('phase', ''),
                row.get('discipline', ''),
                row.get('notes', ''),
                status
            ))
            imported += 1
        except sqlite3.Error as e:
            errors.append(f"Error importing {row['invoice_number']}: {str(e)}")

    conn.commit()
    conn.close()

    # Print summary
    print("=" * 80)
    print("INVOICE IMPORT SUMMARY")
    print("=" * 80)
    print(f"\n📊 Total rows processed: {total_rows}")
    print(f"✅ Successfully imported: {imported}")
    print(f"⚠️  Skipped: {skipped}")
    print(f"❌ Errors: {len(errors)}")

    if skipped_list:
        print(f"\n{'=' * 80}")
        print("SKIPPED INVOICES")
        print("=" * 80)
        for item in skipped_list:
            print(f"\n  Invoice: {item['invoice_number']}")
            print(f"  Amount:  ${item['amount']}")
            print(f"  Status:  {item['status']}")
            print(f"  Reason:  {item['reason']}")

    if errors:
        print(f"\n{'=' * 80}")
        print("ERRORS")
        print("=" * 80)
        for error in errors:
            print(f"  - {error}")

    print(f"\n{'=' * 80}")
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. Review the skipped invoices above")
    print("2. For invoices with 'Missing project_code', assign the correct project")
    print("3. Re-run this script to import the remaining invoices")
    print("\n" + "=" * 80 + "\n")

    return {
        'total': total_rows,
        'imported': imported,
        'skipped': skipped,
        'errors': len(errors)
    }

if __name__ == '__main__':
    import_invoices()
