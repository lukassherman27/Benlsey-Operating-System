#!/usr/bin/env python3
"""
Match contracts from Proposal 2025 (Nung) folder to active projects in database
"""

import re
import sqlite3
from pathlib import Path
from difflib import SequenceMatcher
import PyPDF2

PROPOSALS_DIR = Path.home() / "Library/CloudStorage/OneDrive-Personal/Proposal 2025 (Nung)"
DB_PATH = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_active_projects():
    """Get all active projects from database"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT project_code, project_name, total_fee_usd, status
        FROM projects
        WHERE is_active_project = 1 OR status IN ('active', 'active_project', 'Active')
        ORDER BY project_code DESC
    """)

    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return projects


def parse_filename(filename):
    """Extract project number from filename"""
    project_match = re.match(r'(\d{2}-\d{3})', filename)
    if project_match:
        return project_match.group(1)
    return None


def extract_project_name_from_pdf(pdf_path):
    """Extract project name from PDF"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            first_page = reader.pages[0].extract_text()
            lines = first_page.split('\n')[:15]

            for line in lines:
                line = line.strip()
                if re.match(r'\d{2}-\d{3}', line):
                    continue
                if len(line) > 20 and not line.isupper():
                    return line

        return pdf_path.stem
    except:
        return pdf_path.stem


def extract_total_fee_from_pdf(pdf_path):
    """Try to extract total fee from PDF"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in reader.pages[:5]:  # Check first 5 pages
                full_text += page.extract_text()

            # Look for total fee patterns
            patterns = [
                r'TOTAL FEE[:\s]+USD[:\s]+([\d,]+)',
                r'Total Fee[:\s]+USD[:\s]+([\d,]+)',
                r'total professional fee[:\s]+USD[:\s]+([\d,]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    fee_str = match.group(1).replace(',', '')
                    return float(fee_str)

        return None
    except:
        return None


def find_latest_contracts():
    """Find latest version of each contract"""
    from collections import defaultdict
    from datetime import datetime

    projects = defaultdict(list)

    for file_path in PROPOSALS_DIR.glob("*.pdf"):
        project_num = parse_filename(file_path.name)
        if project_num:
            # Try to extract date
            date_match = re.search(r'(\d{1,2} \w+ \d{2})', file_path.name)
            date_str = date_match.group(1) if date_match else None

            try:
                parsed_date = datetime.strptime(date_str, "%d %b %y") if date_str else None
            except:
                parsed_date = None

            projects[project_num].append((file_path, parsed_date, date_str))

    # Get latest for each
    latest = {}
    for proj_num, versions in projects.items():
        versions_sorted = sorted(versions, key=lambda x: x[1] or datetime.min, reverse=True)
        latest[proj_num] = versions_sorted[0][0]

    return latest


def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def main():
    print("\n" + "="*100)
    print(" CONTRACT TO PROJECT MATCHING REPORT ".center(100, "="))
    print("="*100)

    # Get data
    print("\n📊 Loading data...")
    active_projects = get_active_projects()
    latest_contracts = find_latest_contracts()

    print(f"✓ Found {len(active_projects)} active projects in database")
    print(f"✓ Found {len(latest_contracts)} unique contracts in Proposal folder")

    # Match contracts to projects
    print("\n" + "="*100)
    print(" MATCHING RESULTS ".center(100))
    print("="*100)

    matched = []
    unmatched_contracts = []
    unmatched_projects = []

    for contract_num, pdf_path in sorted(latest_contracts.items()):
        # Convert 25-001 to 25 BK-001 format
        year, num = contract_num.split('-')
        expected_code = f"{year} BK-{num}"

        # Try to find matching project
        db_project = None
        for proj in active_projects:
            if proj['project_code'] == expected_code:
                db_project = proj
                break

        # Extract info from PDF
        pdf_name = extract_project_name_from_pdf(pdf_path)
        pdf_fee = extract_total_fee_from_pdf(pdf_path)

        if db_project:
            # MATCHED!
            db_fee = db_project['total_fee_usd'] or 0
            fee_match = "✓" if pdf_fee and abs(db_fee - pdf_fee) < 1000 else "✗" if pdf_fee else "?"

            matched.append({
                'contract_num': contract_num,
                'db_code': db_project['project_code'],
                'contract_name': pdf_name[:50],
                'db_name': db_project['project_name'][:50],
                'pdf_fee': pdf_fee,
                'db_fee': db_fee,
                'fee_match': fee_match,
                'pdf_file': pdf_path.name[:60]
            })
        else:
            # NOT MATCHED - might be a proposal that's not yet active
            unmatched_contracts.append({
                'contract_num': contract_num,
                'expected_code': expected_code,
                'contract_name': pdf_name[:50],
                'pdf_fee': pdf_fee,
                'pdf_file': pdf_path.name[:60]
            })

    # Find projects without contracts
    matched_codes = {m['db_code'] for m in matched}
    for proj in active_projects:
        if proj['project_code'] not in matched_codes:
            unmatched_projects.append(proj)

    # Print matched contracts
    print(f"\n✅ MATCHED CONTRACTS ({len(matched)}):")
    print("-"*100)
    print(f"{'Contract':<12} {'DB Code':<12} {'Name Match':<35} {'PDF Fee':<15} {'DB Fee':<15} {'Fee ✓':<5}")
    print("-"*100)

    for m in matched:
        name_sim = similarity(m['contract_name'], m['db_name'])
        name_indicator = "✓" if name_sim > 0.6 else "~"

        pdf_fee_str = f"${m['pdf_fee']:,.0f}" if m['pdf_fee'] else "Unknown"
        db_fee_str = f"${m['db_fee']:,.0f}"

        print(f"{m['contract_num']:<12} {m['db_code']:<12} {name_indicator:<2} {m['contract_name'][:32]:<33} "
              f"{pdf_fee_str:<15} {db_fee_str:<15} {m['fee_match']:<5}")

    # Print unmatched contracts (proposals not yet active)
    if unmatched_contracts:
        print(f"\n⚠️  CONTRACTS WITHOUT MATCHING ACTIVE PROJECT ({len(unmatched_contracts)}):")
        print("-"*100)
        print("These might be NEW proposals that haven't been won yet, or the project code might be different")
        print("-"*100)
        print(f"{'Contract':<12} {'Expected Code':<15} {'Project Name':<50} {'Fee':<15}")
        print("-"*100)
        for u in unmatched_contracts[:15]:  # Show first 15
            fee_str = f"${u['pdf_fee']:,.0f}" if u['pdf_fee'] else "Unknown"
            print(f"{u['contract_num']:<12} {u['expected_code']:<15} {u['contract_name'][:48]:<50} {fee_str:<15}")
        if len(unmatched_contracts) > 15:
            print(f"... and {len(unmatched_contracts) - 15} more")

    # Print unmatched active projects
    if unmatched_projects:
        print(f"\n⚠️  ACTIVE PROJECTS WITHOUT CONTRACT IN FOLDER ({len(unmatched_projects)}):")
        print("-"*100)
        print(f"{'DB Code':<15} {'Project Name':<60} {'Fee':<15}")
        print("-"*100)
        for p in unmatched_projects[:15]:  # Show first 15
            fee_str = f"${p['total_fee_usd']:,.0f}" if p['total_fee_usd'] else "Unknown"
            print(f"{p['project_code']:<15} {p['project_name'][:58]:<60} {fee_str:<15}")
        if len(unmatched_projects) > 15:
            print(f"... and {len(unmatched_projects) - 15} more")

    # Summary
    print("\n" + "="*100)
    print(" SUMMARY ".center(100, "="))
    print("="*100)
    print(f"✅ Matched Contracts: {len(matched)}")
    print(f"⚠️  Unmatched Contracts: {len(unmatched_contracts)} (might be proposals, not active yet)")
    print(f"⚠️  Active Projects without contracts: {len(unmatched_projects)}")
    print("="*100)
    print("\nℹ️  Next Steps:")
    print("   1. For MATCHED contracts: Use import_contract_fees.py to extract fee breakdowns")
    print("   2. For UNMATCHED contracts: These are likely proposals that haven't won yet")
    print("   3. For Active projects without contracts: Contract might be in a different folder")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()
