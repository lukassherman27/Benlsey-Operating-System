#!/usr/bin/env python3
"""
Cross-reference Excel invoice list with database to understand correct linking
"""

import pandas as pd
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv('DATABASE_PATH', './database/bensley_master.db')

# File paths
INVOICE_EXCEL = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/List of Oversea Invoice 2024-2025 .xlsx"
PROJECT_STATUS_EXCEL = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Project Status as of 17 Nov 25.xls"

def main():
    print("="*100)
    print("CROSS-REFERENCE: EXCEL FILES vs DATABASE")
    print("="*100)

    # Read Excel files
    print("\n[1/4] Reading Excel files...")

    try:
        # Read invoice Excel
        invoice_df = pd.read_excel(INVOICE_EXCEL)
        print(f"  ✅ Loaded invoice Excel: {len(invoice_df)} rows")
        print(f"  Columns: {list(invoice_df.columns)}")

        # Read project status Excel
        project_df = pd.read_excel(PROJECT_STATUS_EXCEL)
        print(f"  ✅ Loaded project status Excel: {len(project_df)} rows")
        print(f"  Columns: {list(project_df.columns)}")

    except Exception as e:
        print(f"  ❌ Error reading Excel files: {e}")
        return

    # Show sample data from invoice Excel
    print("\n[2/4] Sample data from Invoice Excel:")
    print(invoice_df.head(10).to_string())

    # Show sample data from project status Excel
    print("\n[3/4] Sample data from Project Status Excel:")
    print(project_df.head(10).to_string())

    # Connect to database
    print("\n[4/4] Comparing with database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all invoices from database
    cursor.execute("""
        SELECT
            i.invoice_id,
            i.invoice_number,
            i.project_id,
            p.project_code,
            p.project_title,
            i.invoice_amount,
            i.payment_amount
        FROM invoices i
        LEFT JOIN projects p ON i.project_id = p.project_id
        ORDER BY i.invoice_number
    """)

    db_invoices = cursor.fetchall()
    print(f"\n  Database has {len(db_invoices)} invoices")

    print("\n" + "="*100)
    print("ANALYSIS RESULTS")
    print("="*100)

    print("\n🔍 To understand the correct linking, I need to see:")
    print("  1. What columns in the Invoice Excel show which project each invoice belongs to?")
    print("  2. What's the relationship between invoice numbers and project codes?")
    print("  3. Are there any invoices in the Excel that match the database?")

    print("\n📋 Full column details:")
    print("\nInvoice Excel columns:")
    for i, col in enumerate(invoice_df.columns, 1):
        sample_values = invoice_df[col].dropna().head(3).tolist()
        print(f"  {i}. '{col}' - Sample values: {sample_values}")

    print("\nProject Status Excel columns:")
    for i, col in enumerate(project_df.columns, 1):
        sample_values = project_df[col].dropna().head(3).tolist()
        print(f"  {i}. '{col}' - Sample values: {sample_values}")

    conn.close()

    print("\n" + "="*100)
    print("NEXT: Please review the columns above and tell me:")
    print("  - Which column in Invoice Excel shows the project code/name?")
    print("  - How do invoice numbers relate to projects?")
    print("="*100)

if __name__ == '__main__':
    main()
