#!/usr/bin/env python3
"""
Parse the correct invoice→project mappings from Bill's Project Status sheet
"""

import pandas as pd
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv('DATABASE_PATH', './database/bensley_master.db')

# File paths
PROJECT_STATUS_EXCEL = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Project Status as of 17 Nov 25.xls"

def main():
    print("="*100)
    print("PARSING INVOICE→PROJECT MAPPINGS FROM BILL'S SHEET")
    print("="*100)

    # List all sheets first
    print("\n[1/5] Available sheets in the Excel file:")
    try:
        xls = pd.ExcelFile(PROJECT_STATUS_EXCEL)
        print(f"  Found {len(xls.sheet_names)} sheets:")
        for i, sheet in enumerate(xls.sheet_names, 1):
            print(f"    {i}. {sheet}")

        # Find the Bill's Project Status sheet
        bills_sheet = None
        for sheet in xls.sheet_names:
            if "Bill" in sheet and "Project Status" in sheet:
                bills_sheet = sheet
                break

        if not bills_sheet:
            print("\n  ⚠️  Could not find 'Bill's Project Status' sheet")
            print("  Please specify the exact sheet name.")
            return

        print(f"\n  ✅ Found sheet: '{bills_sheet}'")

    except Exception as e:
        print(f"  ❌ Error reading Excel: {e}")
        return

    # Read Bill's sheet
    print(f"\n[2/5] Reading sheet: '{bills_sheet}'...")
    try:
        df = pd.read_excel(PROJECT_STATUS_EXCEL, sheet_name=bills_sheet)
        print(f"  ✅ Loaded: {len(df)} rows, {len(df.columns)} columns")

        print("\n  Column names:")
        for i, col in enumerate(df.columns, 1):
            print(f"    {i}. '{col}'")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return

    # Show first 30 rows to understand structure
    print(f"\n[3/5] First 30 rows of data:")
    print(df.head(30).to_string())

    # Try to identify the columns
    print(f"\n[4/5] Analyzing structure...")

    # Look for rows that contain invoice numbers (pattern: I##-###)
    invoice_rows = []
    for idx, row in df.iterrows():
        row_str = ' '.join([str(val) for val in row if pd.notna(val)])
        if 'I2' in row_str or 'I19' in row_str or 'I20' in row_str or 'I21' in row_str or 'I22' in row_str or 'I23' in row_str or 'I24' in row_str or 'I25' in row_str:
            invoice_rows.append(idx)

    print(f"\n  Found {len(invoice_rows)} rows that likely contain invoice numbers")
    print(f"  Sample row indices: {invoice_rows[:10]}")

    # Show a few sample invoice rows
    if invoice_rows:
        print(f"\n[5/5] Sample invoice rows:")
        for idx in invoice_rows[:5]:
            print(f"\n  Row {idx}:")
            for col, val in df.iloc[idx].items():
                if pd.notna(val):
                    print(f"    {col}: {val}")

    print("\n" + "="*100)
    print("NEXT STEPS:")
    print("  1. Review the structure above")
    print("  2. Identify which columns contain:")
    print("     - Project Code (e.g., BK-017, 25 BK-088)")
    print("     - Invoice Number (e.g., I24-017)")
    print("     - Phase (e.g., Concept Design, Design Development)")
    print("     - Payment Amount")
    print("="*100)

if __name__ == '__main__':
    main()
