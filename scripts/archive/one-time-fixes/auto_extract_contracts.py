#!/usr/bin/env python3
"""
Automated Contract Extraction Tool
Extracts fee breakdowns and contract terms from PDF contracts
"""

import re
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import PyPDF2

PROPOSALS_DIR = Path.home() / "Library/CloudStorage/OneDrive-Personal/Proposal 2025 (Nung)"
DB_PATH = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_filename(filename):
    """Extract project number from filename"""
    project_match = re.match(r'(\d{2}-\d{3})', filename)
    return project_match.group(1) if project_match else None


def parse_date(date_str):
    """Convert date string like '11 Feb 25' to datetime"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d %b %y")
    except:
        return None


def find_latest_contracts():
    """Find latest version of each contract PDF"""
    projects = defaultdict(list)

    for file_path in PROPOSALS_DIR.glob("*.pdf"):
        project_num = parse_filename(file_path.name)
        if project_num:
            # Extract date if present
            date_match = re.search(r'(\d{1,2} \w+ \d{2})', file_path.name)
            date_str = date_match.group(1) if date_match else None
            parsed_date = parse_date(date_str)
            projects[project_num].append((file_path, parsed_date, date_str))

    # Get latest version for each project
    latest_contracts = {}
    for project_num, versions in sorted(projects.items()):
        versions_sorted = sorted(versions, key=lambda x: x[1] or datetime.min, reverse=True)
        latest_path, latest_date, date_str = versions_sorted[0]
        latest_contracts[project_num] = {
            'path': latest_path,
            'date': latest_date,
            'date_str': date_str or 'original',
            'versions': len(versions)
        }

    return latest_contracts


def get_active_projects():
    """Get all active projects from database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_code, project_name, total_fee_usd
        FROM projects
        WHERE is_active_project = 1 OR status IN ('active', 'active_project', 'Active')
        ORDER BY project_code DESC
    """)
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return projects


def extract_text_from_pdf(pdf_path):
    """Extract all text from PDF"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
            return full_text
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return None


def extract_client_name(text):
    """Extract client company name"""
    # Look for "BETWEEN ... AND BENSLEY"
    pattern = r'BETWEEN\s+(.*?)\s+AND.*?BENSLEY'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        client = match.group(1).strip()
        # Clean up common patterns
        client = re.sub(r'\s*\(.*?\)', '', client)  # Remove parentheticals
        client = re.sub(r'\s+', ' ', client).strip()  # Normalize whitespace
        return client
    return None


def extract_contract_duration(text):
    """Extract contract duration in months"""
    patterns = [
        r'(\d+)\s*(?:\(\d+\))?\s*month\s+period',
        r'period\s+of\s+(\d+)\s+months',
        r'duration[:\s]+(\d+)\s+months'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def extract_payment_terms(text):
    """Extract payment terms (days)"""
    patterns = [
        r'within\s+(\d+)\s+days?\s+(?:of|after).*?invoice',
        r'payment.*?(\d+)\s+days',
        r'(\d+)\s+days?\s+(?:of|after|from).*?invoice'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def extract_late_interest_rate(text):
    """Extract late payment interest rate (% per month)"""
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s+(?:\(\d+(?:\.\d+)?%\))?\s*per\s+month',
        r'interest.*?(\d+(?:\.\d+)?)\s*%.*?month'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def extract_stop_work_days(text):
    """Extract stop work threshold (days)"""
    patterns = [
        r'(\d+)\s+(?:\(\d+\))?\s*days?\s+delinquent',
        r'delinquent.*?(\d+)\s+days',
        r'after\s+(\d+)\s+days.*?suspend'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def extract_restart_fee(text):
    """Extract restart fee percentage"""
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s+(?:\(\d+(?:\.\d+)?%\))?\s*of.*?outstanding',
        r'start.*?up.*?fee.*?(\d+(?:\.\d+)?)\s*%'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def extract_total_fee(text):
    """Extract total contract fee"""
    patterns = [
        r'TOTAL\s+(?:FEE|PROFESSIONAL\s+FEE)[:\s]+USD[:\s]+([0-9,]+)',
        r'Total\s+Fee[:\s]+USD[:\s]+([0-9,]+)',
        r'total.*?fee.*?USD[:\s]+([0-9,]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fee_str = match.group(1).replace(',', '')
            return float(fee_str)
    return None


def extract_fee_breakdown(text):
    """
    Extract fee breakdown by discipline and phase
    Returns: list of (discipline, phase, fee, percentage) tuples
    """
    breakdown = []

    # Find the fee breakdown section (usually Clause 6)
    fee_section_patterns = [
        r'(6\..*?SCOPE OF WORK AND FEE.*?)(?=7\.|CLAUSE 7|$)',
        r'(CLAUSE 6.*?)(?=CLAUSE 7|$)',
    ]

    fee_section = None
    for pattern in fee_section_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            fee_section = match.group(1)
            break

    if not fee_section:
        return None

    # Extract discipline sections
    discipline_patterns = {
        'Landscape': r'(?:LANDSCAPE|Landscape).*?SERVICES?.*?USD\s+([0-9,]+)',
        'Architecture': r'(?:ARCHITECTURAL|Architectural).*?SERVICES?.*?USD\s+([0-9,]+)',
        'Interior': r'(?:INTERIOR|Interior).*?(?:DESIGN\s+)?SERVICES?.*?USD\s+([0-9,]+)',
    }

    # Phase patterns (common across disciplines)
    phase_patterns = [
        (r'Mobilization.*?USD\s+([0-9,]+).*?\((\d+(?:\.\d+)?)\s*%\)', 'Mobilization'),
        (r'(?:Conceptual|Concept).*?Design.*?USD\s+([0-9,]+).*?\((\d+(?:\.\d+)?)\s*%\)', 'Conceptual Design'),
        (r'Design\s+Development.*?USD\s+([0-9,]+).*?\((\d+(?:\.\d+)?)\s*%\)', 'Design Development'),
        (r'Construction\s+Documents?.*?USD\s+([0-9,]+).*?\((\d+(?:\.\d+)?)\s*%\)', 'Construction Documents'),
        (r'Construction\s+(?:Observation|Admin).*?USD\s+([0-9,]+).*?\((\d+(?:\.\d+)?)\s*%\)', 'Construction Observation'),
    ]

    # Try to extract discipline totals and phases
    for discipline, discipline_pattern in discipline_patterns.items():
        # Find discipline section
        discipline_match = re.search(discipline_pattern, fee_section, re.IGNORECASE)
        if not discipline_match:
            continue

        # Get discipline total
        discipline_total = float(discipline_match.group(1).replace(',', ''))

        # Find the discipline-specific section
        discipline_section_pattern = rf'(?:{discipline}.*?SERVICES?.*?)(?=(?:LANDSCAPE|ARCHITECTURAL|INTERIOR|CLAUSE|$))'
        discipline_section_match = re.search(discipline_section_pattern, fee_section, re.DOTALL | re.IGNORECASE)

        if discipline_section_match:
            discipline_section = discipline_section_match.group(0)

            # Extract phases within this discipline
            for phase_pattern, phase_name in phase_patterns:
                phase_match = re.search(phase_pattern, discipline_section, re.IGNORECASE)
                if phase_match:
                    fee = float(phase_match.group(1).replace(',', ''))
                    percentage = float(phase_match.group(2))
                    breakdown.append((discipline, phase_name, fee, percentage))

    return breakdown if breakdown else None


def extract_contract_metadata(pdf_path):
    """Extract all contract metadata from PDF"""
    print(f"\n📄 Extracting from: {pdf_path.name}")

    text = extract_text_from_pdf(pdf_path)
    if not text:
        return None

    metadata = {
        'client_name': extract_client_name(text),
        'total_fee': extract_total_fee(text),
        'contract_duration': extract_contract_duration(text),
        'payment_terms': extract_payment_terms(text),
        'late_interest': extract_late_interest_rate(text),
        'stop_work_days': extract_stop_work_days(text),
        'restart_fee': extract_restart_fee(text),
        'fee_breakdown': extract_fee_breakdown(text)
    }

    return metadata


def display_extraction_results(contract_num, metadata):
    """Display extraction results for review"""
    print("\n" + "="*80)
    print(f" EXTRACTION RESULTS: {contract_num} ".center(80, "="))
    print("="*80)

    print(f"\n📋 Client: {metadata['client_name'] or 'NOT FOUND'}")
    print(f"💰 Total Fee: ${metadata['total_fee']:,.0f}" if metadata['total_fee'] else "💰 Total Fee: NOT FOUND")
    print(f"📅 Duration: {metadata['contract_duration']} months" if metadata['contract_duration'] else "📅 Duration: NOT FOUND")
    print(f"💳 Payment Terms: {metadata['payment_terms']} days" if metadata['payment_terms'] else "💳 Payment Terms: NOT FOUND")
    print(f"💸 Late Interest: {metadata['late_interest']}% per month" if metadata['late_interest'] else "💸 Late Interest: NOT FOUND")
    print(f"⏸️  Stop Work: {metadata['stop_work_days']} days" if metadata['stop_work_days'] else "⏸️  Stop Work: NOT FOUND")
    print(f"🔄 Restart Fee: {metadata['restart_fee']}%" if metadata['restart_fee'] else "🔄 Restart Fee: NOT FOUND")

    if metadata['fee_breakdown']:
        print(f"\n💼 Fee Breakdown: {len(metadata['fee_breakdown'])} phases found")
        print("-"*80)

        # Group by discipline
        by_discipline = defaultdict(list)
        for discipline, phase, fee, pct in metadata['fee_breakdown']:
            by_discipline[discipline].append((phase, fee, pct))

        for discipline, phases in by_discipline.items():
            discipline_total = sum(fee for _, fee, _ in phases)
            print(f"\n{discipline.upper()}: ${discipline_total:,.0f}")
            for phase, fee, pct in phases:
                print(f"  • {phase:30s} ${fee:>10,.0f} ({pct:>4.1f}%)")
    else:
        print("\n❌ Fee Breakdown: NOT FOUND")

    print("="*80)


def import_contract_to_database(contract_num, db_code, metadata, contract_date):
    """Import contract data to database"""
    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n💾 Importing {db_code} to database...")

    # 1. Update project metadata
    cursor.execute("""
        UPDATE projects
        SET
            client_company = COALESCE(?, client_company),
            total_fee_usd = COALESCE(?, total_fee_usd),
            contract_duration_months = COALESCE(?, contract_duration_months),
            payment_terms_days = COALESCE(?, payment_terms_days),
            late_payment_interest_rate = COALESCE(?, late_payment_interest_rate),
            stop_work_days_threshold = COALESCE(?, stop_work_days_threshold),
            restart_fee_percentage = COALESCE(?, restart_fee_percentage),
            contract_date = COALESCE(?, contract_date),
            updated_at = ?
        WHERE project_code = ?
    """, (
        metadata['client_name'],
        metadata['total_fee'],
        metadata['contract_duration'],
        metadata['payment_terms'],
        metadata['late_interest'],
        metadata['stop_work_days'],
        metadata['restart_fee'],
        contract_date,
        datetime.now().isoformat(),
        db_code
    ))

    print(f"   ✓ Updated project metadata")

    # 2. Import fee breakdown if available
    if metadata['fee_breakdown']:
        # Clear existing breakdowns
        cursor.execute("DELETE FROM project_fee_breakdown WHERE project_code = ?", (db_code,))

        # Insert new breakdowns
        for discipline, phase, fee, percentage in metadata['fee_breakdown']:
            breakdown_id = f"{db_code}-{discipline[:3].upper()}-{phase[:3].upper()}-{uuid.uuid4().hex[:8]}"
            cursor.execute("""
                INSERT INTO project_fee_breakdown (
                    breakdown_id, project_code, discipline, phase,
                    phase_fee_usd, percentage_of_total,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                breakdown_id, db_code, discipline, phase,
                fee, percentage,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        print(f"   ✓ Imported {len(metadata['fee_breakdown'])} fee breakdown entries")

    conn.commit()
    conn.close()
    print(f"   ✅ Import complete!")


def main():
    print("\n" + "="*80)
    print(" AUTOMATED CONTRACT EXTRACTION ".center(80, "="))
    print("="*80)

    # Get data
    print("\n📊 Loading data...")
    active_projects = get_active_projects()
    latest_contracts = find_latest_contracts()

    print(f"✓ Found {len(active_projects)} active projects")
    print(f"✓ Found {len(latest_contracts)} contracts")

    # Match contracts to projects
    matched = []
    for contract_num, contract_info in sorted(latest_contracts.items()):
        year, num = contract_num.split('-')
        expected_code = f"{year} BK-{num}"

        # Find matching project
        db_project = next((p for p in active_projects if p['project_code'] == expected_code), None)
        if db_project:
            matched.append({
                'contract_num': contract_num,
                'db_code': expected_code,
                'db_name': db_project['project_name'],
                'contract_info': contract_info
            })

    print(f"✓ Matched {len(matched)} contracts to active projects\n")

    # Display matched contracts
    print("=" * 80)
    print(" MATCHED CONTRACTS ".center(80))
    print("=" * 80)
    for i, m in enumerate(matched, 1):
        print(f"{i:2d}. {m['contract_num']} → {m['db_code']} | {m['db_name'][:50]}")

    # Processing menu
    while True:
        print("\n" + "="*80)
        print("Options:")
        print("  1. Extract and import a specific contract")
        print("  2. Extract and import ALL contracts (batch mode)")
        print("  3. Exit")
        print("="*80)

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            try:
                idx = int(input(f"Enter contract number (1-{len(matched)}): ")) - 1
                if 0 <= idx < len(matched):
                    m = matched[idx]
                    metadata = extract_contract_metadata(m['contract_info']['path'])

                    if metadata:
                        display_extraction_results(m['contract_num'], metadata)

                        import_choice = input("\n❓ Import this to database? (y/n): ").strip().lower()
                        if import_choice == 'y':
                            # Get contract date
                            contract_date = m['contract_info']['date'].strftime('%Y-%m-%d') if m['contract_info']['date'] else datetime.now().strftime('%Y-%m-%d')
                            import_contract_to_database(
                                m['contract_num'],
                                m['db_code'],
                                metadata,
                                contract_date
                            )
                else:
                    print("❌ Invalid selection")
            except (ValueError, IndexError):
                print("❌ Invalid input")

        elif choice == '2':
            print("\n🚀 BATCH MODE - Processing all matched contracts...")
            confirm = input(f"This will process {len(matched)} contracts. Continue? (y/n): ").strip().lower()

            if confirm == 'y':
                for i, m in enumerate(matched, 1):
                    print(f"\n[{i}/{len(matched)}] Processing {m['contract_num']} → {m['db_code']}")
                    metadata = extract_contract_metadata(m['contract_info']['path'])

                    if metadata:
                        display_extraction_results(m['contract_num'], metadata)

                        # Auto-import if fee breakdown found
                        if metadata['fee_breakdown']:
                            contract_date = m['contract_info']['date'].strftime('%Y-%m-%d') if m['contract_info']['date'] else datetime.now().strftime('%Y-%m-%d')
                            import_contract_to_database(
                                m['contract_num'],
                                m['db_code'],
                                metadata,
                                contract_date
                            )
                        else:
                            print("⚠️  Skipping import - no fee breakdown found")

                print("\n✅ Batch processing complete!")

        elif choice == '3':
            print("\n👋 Goodbye!\n")
            break

        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()
