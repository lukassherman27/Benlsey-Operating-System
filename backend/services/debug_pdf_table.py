#!/usr/bin/env python3
"""Debug PDF table extraction"""

import pdfplumber
import sys

if len(sys.argv) < 2:
    print("Usage: python3 debug_pdf_table.py <pdf_path>")
    sys.exit(1)

pdf_path = sys.argv[1]

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]

    # Get page dimensions
    print(f"Page size: {page.width} x {page.height}")
    print()

    # Extract tables
    tables = page.extract_tables()
    print(f"Found {len(tables)} tables")
    print()

    if tables:
        table = tables[0]
        print(f"Table has {len(table)} rows")
        print()

        # Print first 10 rows
        for i, row in enumerate(table[:15]):
            print(f"Row {i}: {row[:5] if len(row) > 5 else row}")  # First 5 columns

        print()
        print("Full first few rows:")
        for i, row in enumerate(table[:5]):
            print(f"Row {i}: {len(row)} columns")
            for j, cell in enumerate(row[:10]):
                if cell:
                    print(f"  [{j}]: {cell[:50]}")
