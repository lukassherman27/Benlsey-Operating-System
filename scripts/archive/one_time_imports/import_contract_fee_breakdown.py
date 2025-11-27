#!/usr/bin/env python3
"""
Import CONTRACT_FEE_BREAKDOWN.xlsx into database
DELETES all existing invoice data first!
"""
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "database/bensley_master.db"
EXCEL_FILE = "/Users/lukassherman/Desktop/MASTER_CONTRACT_FEE_BREAKDOWN.xlsx"

def connect_db():
    return sqlite3.connect(DB_PATH)

def clear_invoices(conn):
    """Delete ALL existing invoice data"""
    cursor = conn.cursor()

    print("\n🗑️  DELETING ALL EXISTING INVOICE DATA...")
    cursor.execute("SELECT COUNT(*) FROM invoices")
    old_count = cursor.fetchone()[0]

    cursor.execute("DELETE FROM invoices")
    conn.commit()

    print(f"   Deleted {old_count} old invoices")
    return old_count

def get_project_id(conn, project_code):
    """Get project_id from project_code"""
    cursor = conn.cursor()
    cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
    result = cursor.fetchone()
    return result[0] if result else None

def parse_date(date_val):
    """Parse date to YYYY-MM-DD format"""
    if pd.isna(date_val):
        return None
    if isinstance(date_val, str):
        try:
            dt = datetime.strptime(date_val, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except:
            return None
    elif isinstance(date_val, datetime):
        return date_val.strftime("%Y-%m-%d")
    return None

def parse_amount(amount_val):
    """Safely parse amount to float, handling datetime and other types"""
    if pd.isna(amount_val):
        return 0.0
    if isinstance(amount_val, (int, float)):
        return float(amount_val)
    if isinstance(amount_val, datetime):
        # DateTime in amount field is wrong data - return 0
        return 0.0
    if isinstance(amount_val, str):
        try:
            return float(amount_val.replace(',', ''))
        except:
            return 0.0
    return 0.0

def import_invoices(conn, df):
    """Import invoices from DataFrame"""
    cursor = conn.cursor()

    imported_count = 0
    skipped_count = 0
    errors = []

    print("\n📥 IMPORTING INVOICES FROM EXCEL...")

    for idx, row in df.iterrows():
        project_code = row['Project\nCode']

        # Get project_id
        project_id = get_project_id(conn, project_code)
        if not project_id:
            skipped_count += 1
            errors.append(f"Row {idx}: Project {project_code} not found in database")
            continue

        discipline = row['Discipline'] if pd.notna(row['Discipline']) else ''
        phase = row['Phase'] if pd.notna(row['Phase']) else ''
        phase_fee = parse_amount(row['Phase\nFee'])

        # Process up to 4 invoices per row
        for i in range(1, 5):
            inv_num = row.get(f'Invoice {i}\nNumber')

            if pd.isna(inv_num):
                continue

            inv_date = parse_date(row.get(f'Invoice {i}\nDate'))
            inv_amount = parse_amount(row.get(f'Invoice {i}\nAmount'))
            paid_date = parse_date(row.get(f'Invoice {i}\nPaid Date'))
            paid_amount = parse_amount(row.get(f'Invoice {i}\nPaid Amount'))
            status = row.get(f'Status {i}', '').lower() if pd.notna(row.get(f'Status {i}')) else 'unknown'

            # Determine status if not provided
            if not status or status == 'unknown':
                if paid_amount > 0 and paid_amount >= inv_amount:
                    status = 'paid'
                elif paid_amount > 0 and paid_amount < inv_amount:
                    status = 'partial'
                else:
                    status = 'outstanding'

            # Insert invoice with provenance tracking
            try:
                cursor.execute("""
                    INSERT INTO invoices (
                        project_id,
                        invoice_number,
                        description,
                        invoice_date,
                        invoice_amount,
                        payment_date,
                        payment_amount,
                        status,
                        notes,
                        source_type,
                        source_reference,
                        created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_id,
                    inv_num,
                    f"{phase} - {discipline}",
                    inv_date,
                    inv_amount,
                    paid_date,
                    paid_amount,
                    status,
                    f"Phase Fee: ${phase_fee:,.2f}",
                    'import',
                    f'MASTER_CONTRACT_FEE_BREAKDOWN.xlsx:row_{idx}',
                    'import_contract_fee_breakdown'
                ))
                imported_count += 1
            except Exception as e:
                errors.append(f"Row {idx}, Invoice {inv_num}: {str(e)}")
                skipped_count += 1

    conn.commit()

    print(f"   ✅ Imported: {imported_count} invoices")
    print(f"   ⚠️  Skipped: {skipped_count} invoices")

    if errors and len(errors) <= 10:
        print(f"\n⚠️  Errors/Warnings:")
        for error in errors[:10]:
            print(f"   - {error}")
    elif len(errors) > 10:
        print(f"\n⚠️  {len(errors)} errors/warnings (showing first 10):")
        for error in errors[:10]:
            print(f"   - {error}")

    return imported_count, skipped_count

def main():
    print("=" * 100)
    print("IMPORTING CONTRACT_FEE_BREAKDOWN.xlsx INTO DATABASE")
    print("=" * 100)

    # Connect to database
    conn = connect_db()

    # Clear existing invoices
    old_count = clear_invoices(conn)

    # Read Excel file
    print(f"\n📄 READING EXCEL FILE...")
    print(f"   File: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE)
    print(f"   Rows: {len(df)}")

    # Import invoices
    imported, skipped = import_invoices(conn, df)

    # Summary
    print("\n" + "=" * 100)
    print("IMPORT SUMMARY")
    print("=" * 100)
    print(f"\n🗑️  Deleted: {old_count} old invoices")
    print(f"✅ Imported: {imported} new invoices")
    print(f"⚠️  Skipped: {skipped} invoices")

    # Verify
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM invoices")
    final_count = cursor.fetchone()[0]
    print(f"\n📊 Final invoice count: {final_count}")

    # Check by status
    cursor.execute("""
        SELECT status, COUNT(*) as count, SUM(invoice_amount) as total
        FROM invoices
        GROUP BY status
    """)

    print(f"\n📈 Breakdown by status:")
    for status, count, total in cursor.fetchall():
        print(f"   {status:15}: {count:4} invoices (${total:,.2f})")

    conn.close()

    print("\n✅ IMPORT COMPLETE!")
    print("=" * 100)

if __name__ == '__main__':
    main()
