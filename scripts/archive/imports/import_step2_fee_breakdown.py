#!/usr/bin/env python3
"""
STEP 2: Import Fee Breakdown and Invoices from MASTER_CONTRACT_FEE_BREAKDOWN.xlsx
Imports to: project_fee_breakdown and invoices tables
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

# Paths
WORKING_DIR = Path("/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System")
DB_PATH = WORKING_DIR / "database" / "bensley_master.db"
FEE_BREAKDOWN_EXCEL = Path("/Users/lukassherman/Desktop/MASTER_CONTRACT_FEE_BREAKDOWN.xlsx")


def get_project_id(cursor, project_code):
    """Get project_id from projects table, create if doesn't exist"""
    cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return None


def import_fee_breakdown_and_invoices():
    """Import fee breakdown and invoice data"""
    print("\n" + "="*80)
    print("STEP 2: IMPORT FEE BREAKDOWN & INVOICES")
    print("="*80)

    print(f"\n📖 Reading: {FEE_BREAKDOWN_EXCEL}")
    df = pd.read_excel(FEE_BREAKDOWN_EXCEL, sheet_name="Contract Breakdown")

    print(f"Loaded {len(df)} rows")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    fee_breakdown_count = 0
    invoices_imported = 0
    skipped = 0
    errors = 0

    for idx, row in df.iterrows():
        try:
            # Get project code
            project_code = row.get('Project\nCode')
            if pd.isna(project_code):
                skipped += 1
                continue

            project_code = str(project_code).strip()

            # Get project_id (needed for invoices)
            project_id = get_project_id(cursor, project_code)

            # 1. Import Phase Fee Breakdown
            discipline = row.get('Discipline')
            phase = row.get('Phase')
            phase_fee = row.get('Phase\nFee')

            if pd.notna(discipline) and pd.notna(phase) and pd.notna(phase_fee):
                try:
                    phase_fee = float(phase_fee)

                    # Check if exists
                    cursor.execute("""
                        SELECT breakdown_id FROM project_fee_breakdown
                        WHERE project_code = ? AND discipline = ? AND phase = ?
                    """, (project_code, discipline, phase))

                    existing = cursor.fetchone()

                    if existing:
                        # Update
                        cursor.execute("""
                            UPDATE project_fee_breakdown
                            SET phase_fee_usd = ?,
                                updated_at = datetime('now')
                            WHERE breakdown_id = ?
                        """, (phase_fee, existing[0]))
                    else:
                        # Insert
                        cursor.execute("""
                            INSERT INTO project_fee_breakdown (
                                project_code,
                                discipline,
                                phase,
                                phase_fee_usd,
                                created_at
                            ) VALUES (?, ?, ?, ?, datetime('now'))
                        """, (project_code, discipline, phase, phase_fee))
                        fee_breakdown_count += 1

                except Exception as e:
                    pass  # Skip invalid fees

            # 2. Import Invoices (up to 4 invoices per row)
            if project_id:
                for inv_num in range(1, 5):
                    invoice_number = row.get(f'Invoice {inv_num}\nNumber')
                    invoice_date = row.get(f'Invoice {inv_num}\nDate')
                    invoice_amount = row.get(f'Invoice {inv_num}\nAmount')
                    paid_date = row.get(f'Invoice {inv_num}\nPaid Date')
                    paid_amount = row.get(f'Invoice {inv_num}\nPaid Amount')
                    status = row.get(f'Status {inv_num}')

                    # Skip if no invoice number
                    if pd.isna(invoice_number):
                        continue

                    invoice_number = str(invoice_number).strip()

                    # Parse invoice date
                    if pd.notna(invoice_date):
                        try:
                            if isinstance(invoice_date, str):
                                invoice_date = pd.to_datetime(invoice_date).strftime('%Y-%m-%d')
                            else:
                                invoice_date = invoice_date.strftime('%Y-%m-%d')
                        except:
                            invoice_date = None
                    else:
                        invoice_date = None

                    # Parse paid date
                    if pd.notna(paid_date):
                        try:
                            if isinstance(paid_date, str):
                                paid_date = pd.to_datetime(paid_date).strftime('%Y-%m-%d')
                            else:
                                paid_date = paid_date.strftime('%Y-%m-%d')
                        except:
                            paid_date = None
                    else:
                        paid_date = None

                    # Parse amounts
                    try:
                        invoice_amount = float(invoice_amount) if pd.notna(invoice_amount) else 0
                    except:
                        invoice_amount = 0

                    try:
                        paid_amount = float(paid_amount) if pd.notna(paid_amount) else 0
                    except:
                        paid_amount = 0

                    # Determine status
                    if pd.notna(status):
                        status_str = str(status).lower()
                        if 'paid' in status_str:
                            invoice_status = 'paid'
                        elif 'outstanding' in status_str or 'unpaid' in status_str:
                            invoice_status = 'outstanding'
                        elif 'remaining' in status_str:
                            invoice_status = 'pending'
                        else:
                            invoice_status = 'outstanding'
                    else:
                        invoice_status = 'outstanding' if invoice_amount > 0 else 'pending'

                    # Check if invoice exists
                    cursor.execute("""
                        SELECT invoice_id FROM invoices
                        WHERE invoice_number = ?
                    """, (invoice_number,))

                    existing_inv = cursor.fetchone()

                    if existing_inv:
                        # Update
                        cursor.execute("""
                            UPDATE invoices
                            SET project_id = ?,
                                invoice_date = ?,
                                invoice_amount = ?,
                                payment_date = ?,
                                payment_amount = ?,
                                status = ?
                            WHERE invoice_id = ?
                        """, (
                            project_id,
                            invoice_date,
                            invoice_amount,
                            paid_date,
                            paid_amount,
                            invoice_status,
                            existing_inv[0]
                        ))
                    else:
                        # Insert
                        cursor.execute("""
                            INSERT INTO invoices (
                                project_id,
                                invoice_number,
                                invoice_date,
                                invoice_amount,
                                payment_date,
                                payment_amount,
                                status,
                                description
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            project_id,
                            invoice_number,
                            invoice_date,
                            invoice_amount,
                            paid_date,
                            paid_amount,
                            invoice_status,
                            f"{discipline} - {phase}" if pd.notna(discipline) and pd.notna(phase) else None
                        ))
                        invoices_imported += 1

            if (idx + 1) % 50 == 0:
                print(f"  Processed {idx + 1}/{len(df)} rows...")

        except Exception as e:
            errors += 1
            print(f"  ❌ Error at row {idx}: {e}")
            continue

    conn.commit()
    conn.close()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"  ✅ Fee breakdown records: {fee_breakdown_count}")
    print(f"  ✅ Invoices imported: {invoices_imported}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Errors: {errors}")


def main():
    print("\n" + "="*80)
    print("IMPORT FEE BREAKDOWN & INVOICES")
    print("="*80)
    print(f"\nSource: {FEE_BREAKDOWN_EXCEL}")
    print(f"Database: {DB_PATH}")
    print("\nThis imports:")
    print("  • Phase fee breakdown by discipline")
    print("  • Invoice records with payment status")

    response = input("\nProceed with import? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return

    import_fee_breakdown_and_invoices()

    print("\n✅ STEP 2 COMPLETE - Fee breakdown & invoices imported")
    print("Next: Run import_step3_contracts.py")


if __name__ == "__main__":
    main()
