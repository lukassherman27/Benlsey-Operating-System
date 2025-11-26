#!/usr/bin/env python3
"""Debug PDF text extraction"""

import PyPDF2
from pathlib import Path

PDF_PATH = Path.home() / "Library/CloudStorage/OneDrive-Personal/Proposal 2025 (Nung)/25-002 Tonkin Palace Hanoi, Vietnam revised on 26 Jan 25 (both signed).pdf"

with open(PDF_PATH, 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    print(f"Total pages: {len(reader.pages)}\n")

    # Extract first 3 pages
    for i in range(min(3, len(reader.pages))):
        print(f"\n{'='*80}")
        print(f" PAGE {i+1} ".center(80, '='))
        print('='*80)
        text = reader.pages[i].extract_text()
        print(text[:2000])  # First 2000 characters
