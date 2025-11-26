#!/usr/bin/env python3
"""
Contract Fee Parser - Parse contracts from Proposal 2025 (Nung) folder

Automatically finds the latest version of each contract and extracts fee breakdowns.
"""

import re
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import PyPDF2

PROPOSALS_DIR = Path.home() / "Library/CloudStorage/OneDrive-Personal/Proposal 2025 (Nung)"
DB_PATH = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_filename(filename):
    """
    Parse contract filename to extract:
    - Project number (e.g., '25-001')
    - Date (if present)
    - File type (.pdf or .docx)

    Returns: (project_num, date_str, extension)
    """
    # Extract project number (e.g., 25-001, 25-002)
    project_match = re.match(r'(\d{2}-\d{3})', filename)
    if not project_match:
        return None, None, None

    project_num = project_match.group(1)

    # Extract date if present (various formats)
    date_patterns = [
        r'revised on (\d{1,2} \w+ \d{2})',  # e.g., "revised on 11 Feb 25"
        r'revised (\d{1,2} \w+ \d{2})',      # e.g., "revised 11 Feb 25"
        r'(\d{1,2} \w+ \d{2})',              # e.g., "11 Feb 25"
    ]

    date_str = None
    for pattern in date_patterns:
        date_match = re.search(pattern, filename)
        if date_match:
            date_str = date_match.group(1)
            break

    # Get extension
    extension = Path(filename).suffix.lower()

    return project_num, date_str, extension


def parse_date(date_str):
    """Convert date string like '11 Feb 25' to datetime"""
    if not date_str:
        return None

    try:
        # Try to parse "11 Feb 25" format
        dt = datetime.strptime(date_str, "%d %b %y")
        return dt
    except:
        return None


def find_latest_contracts():
    """
    Find the latest version of each contract PDF
    Returns: dict of {project_num: latest_pdf_path}
    """
    if not PROPOSALS_DIR.exists():
        print(f"❌ Proposals directory not found: {PROPOSALS_DIR}")
        return {}

    # Group files by project number
    projects = defaultdict(list)

    for file_path in PROPOSALS_DIR.glob("*.pdf"):
        project_num, date_str, ext = parse_filename(file_path.name)
        if project_num and ext == '.pdf':
            parsed_date = parse_date(date_str)
            projects[project_num].append((file_path, parsed_date, date_str))

    # Find latest version for each project
    latest_contracts = {}
    for project_num, versions in sorted(projects.items()):
        # Sort by date (None dates go first)
        versions_sorted = sorted(versions, key=lambda x: x[1] or datetime.min, reverse=True)
        latest_path, latest_date, date_str = versions_sorted[0]
        latest_contracts[project_num] = {
            'path': latest_path,
            'date': latest_date,
            'date_str': date_str or 'original',
            'all_versions': len(versions)
        }

    return latest_contracts


def extract_project_name_from_pdf(pdf_path):
    """Extract project name from PDF title/content"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            # Get first page text
            first_page = reader.pages[0].extract_text()

            # Try to find project name (usually in first few lines)
            lines = first_page.split('\n')[:10]
            for line in lines:
                # Skip contract numbers
                if re.match(r'\d{2}-\d{3}', line.strip()):
                    continue
                # Project name is usually a longer line with location
                if len(line.strip()) > 20:
                    return line.strip()

        # Fallback to filename
        return pdf_path.stem
    except:
        return pdf_path.stem


def search_for_fee_breakdown_in_pdf(pdf_path):
    """
    Search PDF for fee breakdown section (usually Clause 6 or similar)
    Returns: extracted text containing fee information
    """
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""

            for page in reader.pages:
                full_text += page.extract_text() + "\n"

            # Search for fee breakdown section
            # Common patterns: "Fee Breakdown", "Clause 6", "Scope of Work and Fee"
            fee_section_patterns = [
                r'(6\.\s*SCOPE OF WORK AND FEE.*?)(?=7\.|$)',
                r'(CLAUSE 6.*?)(?=CLAUSE 7|$)',
                r'(FEE BREAKDOWN.*?)(?=\n\n|\d+\.|$)',
                r'(SCOPE.*?FEE.*?)(?=\n\n|\d+\.|$)',
            ]

            for pattern in fee_section_patterns:
                match = re.search(pattern, full_text, re.DOTALL | re.IGNORECASE)
                if match:
                    return match.group(1)

            return None
    except Exception as e:
        print(f"❌ Error reading PDF {pdf_path.name}: {e}")
        return None


def main():
    """Main function"""
    print("\n" + "="*80)
    print(" CONTRACT FEE PARSER - Proposal 2025 (Nung) ".center(80, "="))
    print("="*80)

    print(f"\n📁 Scanning: {PROPOSALS_DIR}")

    latest_contracts = find_latest_contracts()

    if not latest_contracts:
        print("\n❌ No contract PDFs found!")
        return

    print(f"\n✓ Found {len(latest_contracts)} unique projects")
    print("\n" + "="*80)
    print(" LATEST CONTRACTS ".center(80))
    print("="*80)

    for i, (project_num, info) in enumerate(sorted(latest_contracts.items()), 1):
        project_name = extract_project_name_from_pdf(info['path'])
        print(f"\n{i:2d}. {project_num} | {info['date_str']:15s} | {info['all_versions']} version(s)")
        print(f"    {project_name[:70]}")
        print(f"    📄 {info['path'].name}")

    print("\n" + "="*80)

    # Interactive menu
    while True:
        print("\nOptions:")
        print("1. View a specific contract's fee breakdown")
        print("2. Export list of latest contracts to CSV")
        print("3. Auto-extract fees from a contract (manual verification needed)")
        print("4. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            try:
                idx = int(input("Enter contract number (1-{}): ".format(len(latest_contracts)))) - 1
                projects_list = sorted(latest_contracts.items())

                if 0 <= idx < len(projects_list):
                    project_num, info = projects_list[idx]
                    print(f"\n📄 Searching fee breakdown in: {info['path'].name}")

                    fee_text = search_for_fee_breakdown_in_pdf(info['path'])
                    if fee_text:
                        print("\n" + "-"*80)
                        print("FEE BREAKDOWN SECTION (first 2000 chars):")
                        print("-"*80)
                        print(fee_text[:2000])
                        print("-"*80)

                        # Ask if user wants to manually enter fees
                        enter_fees = input("\nEnter fees for this project? (y/n): ").strip().lower()
                        if enter_fees == 'y':
                            print("\nℹ️  Please use the import_contract_fees.py script to manually enter fees")
                            print(f"   Project: {project_num}")
                    else:
                        print("\n⚠️  Could not find fee breakdown section in PDF")
                else:
                    print("❌ Invalid selection")
            except (ValueError, IndexError):
                print("❌ Invalid input")

        elif choice == '2':
            output_file = Path("latest_contracts_list.csv")
            with open(output_file, 'w') as f:
                f.write("Project Number,Date,Versions,PDF Filename,Project Name\n")
                for project_num, info in sorted(latest_contracts.items()):
                    project_name = extract_project_name_from_pdf(info['path'])
                    f.write(f'"{project_num}","{info["date_str"]}",{info["all_versions"]},"{info["path"].name}","{project_name}"\n')
            print(f"\n✅ Exported to: {output_file.absolute()}")

        elif choice == '3':
            print("\n🚧 Auto-extraction feature coming soon!")
            print("   For now, please use import_contract_fees.py to manually enter fees")
            print("   while reviewing the PDF")

        elif choice == '4':
            print("\n👋 Goodbye!\n")
            break

        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()
