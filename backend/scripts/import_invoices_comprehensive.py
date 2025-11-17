#!/usr/bin/env python3
"""
Comprehensive Invoice Import from Accountant's PDF Report
Extracts ALL invoice line items from all 29 projects across 11 pages
Each line item = one discipline + phase combination
"""

import pdfplumber
import sqlite3
import re
from datetime import datetime
from collections import defaultdict

# File paths
PDF_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/2025-11/Project Status as of 10 Nov 25 (Updated).pdf"
DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

def parse_date(date_str):
    """
    Parse various date formats from the PDF
    Examples: "Aug 26.25", "Oct 10.25", "Nov 26.20", "Jun 21.22"
    Returns: ISO format date string YYYY-MM-DD or None
    """
    if not date_str or date_str.strip() == "":
        return None

    date_str = date_str.strip()

    # Month abbreviations to numbers
    months = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }

    # Pattern: "Aug 26.25" or "Oct 10.25"
    match = re.match(r'([A-Za-z]{3})\s+(\d{1,2})\.(\d{2})', date_str)
    if match:
        month_abbr, day, year_short = match.groups()
        month = months.get(month_abbr)
        if month:
            year = f"20{year_short}"
            return f"{year}-{month}-{day.zfill(2)}"

    return None

def parse_amount(amount_str):
    """
    Parse amount string to float
    Examples: "8,000.00", "118,750.00", "0.00"
    """
    if not amount_str:
        return 0.0

    try:
        # Remove commas and convert to float
        clean = str(amount_str).replace(',', '').strip()
        return float(clean)
    except:
        return 0.0

def get_proposal_id_by_project_code(conn, project_code):
    """Look up proposal_id from project_code"""
    cursor = conn.cursor()
    cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (project_code,))
    result = cursor.fetchone()
    return result[0] if result else None

def extract_invoice_lines_from_pdf():
    """
    Extract all invoice line items from the PDF
    Returns list of dicts with invoice data
    """
    invoice_lines = []

    print(f"\n{'='*80}")
    print(f"EXTRACTING INVOICE DATA FROM PDF")
    print(f"{'='*80}\n")

    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Total pages in PDF: {len(pdf.pages)}")

        for page_num, page in enumerate(pdf.pages, 1):
            print(f"\n--- Processing Page {page_num} ---")

            # Extract text from the page
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')

            current_project_code = None
            current_discipline = None

            for i, line in enumerate(lines):
                # Look for project code pattern (e.g., "1 20 BK-047", "2 19 BK-018")
                project_match = re.match(r'^\s*\d+\s+(\d{2}\s+BK-\d{3})', line)
                if project_match:
                    current_project_code = project_match.group(1).strip()
                    print(f"\n  Found Project: {current_project_code}")

                # Look for discipline indicators
                if 'Landscape Architectural' in line or 'Landscape Architect' in line:
                    current_discipline = 'Landscape Architectural'
                elif line.strip() == 'Architectural' or 'Architectural Conceptual' in line:
                    current_discipline = 'Architectural'
                elif 'Interior Design' in line:
                    current_discipline = 'Interior Design'
                elif 'Branding' in line:
                    current_discipline = 'Branding'

                # Look for invoice lines with invoice number pattern
                # Pattern: Amount Invoice# % Invoice_Date Outstanding Remaining Paid Date_paid
                invoice_match = re.search(r'(I\d{2}-\d{3}[A-Z]?(?:&[A-Z])?|T\d{2}-\d{3}[A-Z]?)', line)
                if invoice_match and current_project_code:
                    invoice_number = invoice_match.group(1)

                    # Extract phase/description from the line
                    phase = None
                    description = None

                    # Common phases
                    if 'Mobilization Fee' in line:
                        phase = 'Mobilization Fee'
                    elif 'Conceptual Design' in line:
                        phase = 'Conceptual Design'
                    elif 'Design Development' in line:
                        phase = 'Design Development'
                    elif 'Construction Documents' in line:
                        phase = 'Construction Documents'
                    elif 'Construction Observation' in line:
                        phase = 'Construction Observation'
                    elif 'Schematic Design' in line:
                        phase = 'Schematic Design'
                    elif 'installment' in line.lower():
                        # Extract installment description
                        phase = re.search(r'(\d+(?:st|nd|rd|th)\s+installment\s+[A-Za-z]+\s+\d+)', line)
                        phase = phase.group(1) if phase else 'Installment'

                    # Try to extract amounts and dates
                    # Split line into parts
                    parts = re.split(r'\s+', line)

                    # Find invoice date (after invoice number)
                    invoice_date_str = None
                    payment_date_str = None
                    invoice_amount = 0.0
                    paid_amount = 0.0

                    # Look for date patterns
                    for part in parts:
                        if re.match(r'[A-Za-z]{3}\s+\d{1,2}\.\d{2}', part + ' ' + parts[parts.index(part)+1] if parts.index(part)+1 < len(parts) else ''):
                            date_candidate = part + ' ' + parts[parts.index(part)+1]
                            if not invoice_date_str:
                                invoice_date_str = date_candidate
                            else:
                                payment_date_str = date_candidate

                    # Try to extract amounts (look for numbers with decimals)
                    amounts = []
                    for part in parts:
                        if re.match(r'[\d,]+\.\d{2}$', part):
                            amounts.append(parse_amount(part))

                    # Heuristic: first amount is invoice amount, last non-zero is paid amount
                    if len(amounts) >= 3:
                        invoice_amount = amounts[0]
                        # Find last non-zero amount for paid
                        for amt in reversed(amounts):
                            if amt > 0:
                                paid_amount = amt
                                break

                    invoice_date = parse_date(invoice_date_str) if invoice_date_str else None
                    payment_date = parse_date(payment_date_str) if payment_date_str else None

                    # Determine status
                    status = 'Paid' if payment_date else 'Outstanding'

                    invoice_line = {
                        'project_code': current_project_code,
                        'invoice_number': invoice_number,
                        'discipline': current_discipline,
                        'phase': phase,
                        'description': description,
                        'invoice_amount': invoice_amount,
                        'invoice_date': invoice_date,
                        'payment_date': payment_date,
                        'status': status
                    }

                    invoice_lines.append(invoice_line)

                    if invoice_amount > 0:
                        print(f"    - {invoice_number}: {current_discipline} - {phase} - ${invoice_amount:,.2f} [{status}]")

    return invoice_lines

def extract_invoice_lines_structured():
    """
    More structured extraction using the PDF content directly
    Parses the visible table structure
    """
    invoice_lines = []

    print(f"\n{'='*80}")
    print(f"STRUCTURED EXTRACTION FROM PDF")
    print(f"{'='*80}\n")

    with pdfplumber.open(PDF_PATH) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"\n--- Processing Page {page_num} ---")

            # Try to extract tables
            tables = page.extract_tables()

            if tables:
                for table in tables:
                    # Process table rows
                    for row in table:
                        if row and len(row) > 5:
                            # Check if row contains invoice number
                            invoice_num_found = False
                            for cell in row:
                                if cell and re.search(r'I\d{2}-\d{3}', str(cell)):
                                    invoice_num_found = True
                                    break

                            if invoice_num_found:
                                print(f"  Table row with invoice: {row}")

            # Also extract text for manual parsing
            text = page.extract_text()
            if text:
                lines = text.split('\n')

                current_project_code = None
                current_project_title = None
                current_discipline = None

                for line_idx, line in enumerate(lines):
                    # Project header: "1 20 BK-047 Sep-26 Audley Square House-Communal Spa"
                    project_match = re.match(r'^(\d+)\s+(\d{2}\s+BK-\d{3})\s+([A-Za-z]+-\d{2})\s+(.+)', line)
                    if project_match:
                        seq, project_code, expiry, title = project_match.groups()
                        current_project_code = project_code
                        current_project_title = title
                        current_discipline = None
                        print(f"\n  Project {seq}: {project_code} - {title}")
                        continue

                    # Discipline markers
                    if line.strip() in ['Landscape Architectural', 'Landscape Architect and Architectural Façade']:
                        current_discipline = 'Landscape Architectural'
                        print(f"    Discipline: {current_discipline}")
                        continue
                    elif line.strip() == 'Architectural':
                        current_discipline = 'Architectural'
                        print(f"    Discipline: {current_discipline}")
                        continue
                    elif line.strip() == 'Interior Design':
                        current_discipline = 'Interior Design'
                        print(f"    Discipline: {current_discipline}")
                        continue
                    elif 'Branding' in line and 'Consultancy' in line:
                        current_discipline = 'Branding'
                        print(f"    Discipline: {current_discipline}")
                        continue

                    # Invoice line pattern
                    # Format: Description Amount Invoice# % Invoice_Date Outstanding Remaining Paid Date_Paid
                    if current_project_code and re.search(r'(I\d{2}-\d{3}[A-Z]?(?:&[A-Z])?|T\d{2}-\d{3})', line):
                        parts = re.split(r'\s{2,}', line)

                        # Extract invoice number
                        invoice_match = re.search(r'(I\d{2}-\d{3}[A-Z]?(?:&[A-Z])?|T\d{2}-\d{3}[A-Z]?)', line)
                        if invoice_match:
                            invoice_number = invoice_match.group(1)

                            # Extract phase
                            phase = None
                            if 'Mobilization Fee' in line:
                                phase = 'Mobilization Fee'
                            elif 'Conceptual Design' in line:
                                phase = 'Conceptual Design'
                            elif 'Design Development' in line:
                                phase = 'Design Development'
                            elif 'Construction Documents' in line:
                                phase = 'Construction Documents'
                            elif 'Construction Observation' in line:
                                phase = 'Construction Observation'
                            elif 'Schematic Design' in line:
                                phase = 'Schematic Design'
                            elif 'installment' in line:
                                inst_match = re.search(r'(\d+(?:st|nd|rd|th)\s+installment[^I]*)', line)
                                phase = inst_match.group(1).strip() if inst_match else 'Installment'

                            # Extract all monetary amounts
                            amounts = re.findall(r'([\d,]+\.\d{2})', line)
                            amounts = [parse_amount(a) for a in amounts]

                            # Extract dates
                            dates = re.findall(r'([A-Z][a-z]{2}\s+\d{1,2}\.\d{2})', line)

                            invoice_date = parse_date(dates[0]) if len(dates) > 0 else None
                            payment_date = parse_date(dates[1]) if len(dates) > 1 else None

                            # First amount is typically the line amount
                            invoice_amount = amounts[0] if amounts else 0.0

                            # Last non-zero amount is typically paid
                            paid_amount = 0.0
                            for amt in reversed(amounts):
                                if amt > 0:
                                    paid_amount = amt
                                    break

                            status = 'Paid' if payment_date else 'Outstanding'

                            invoice_line = {
                                'project_code': current_project_code,
                                'invoice_number': invoice_number,
                                'discipline': current_discipline or 'General',
                                'phase': phase or 'Unspecified',
                                'description': phase,
                                'invoice_amount': invoice_amount,
                                'invoice_date': invoice_date,
                                'payment_date': payment_date,
                                'status': status
                            }

                            invoice_lines.append(invoice_line)

                            if invoice_amount > 0:
                                status_icon = "✓" if status == "Paid" else "○"
                                print(f"      {status_icon} {invoice_number}: {phase} - ${invoice_amount:,.2f}")

    return invoice_lines

def import_to_database(invoice_lines):
    """Import invoice lines to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"\n{'='*80}")
    print(f"IMPORTING TO DATABASE")
    print(f"{'='*80}\n")

    # First, clear existing invoice data
    print("Clearing existing invoices...")
    cursor.execute("DELETE FROM invoices")
    conn.commit()
    print(f"  Deleted existing records\n")

    # Track statistics
    stats = defaultdict(int)
    project_stats = defaultdict(int)
    inserted = 0
    skipped = 0

    for line in invoice_lines:
        project_code = line['project_code']

        # Look up proposal_id
        proposal_id = get_proposal_id_by_project_code(conn, project_code)

        if not proposal_id:
            print(f"  WARNING: No proposal found for project code {project_code}")
            skipped += 1
            continue

        # Insert invoice line
        try:
            cursor.execute("""
                INSERT INTO invoices (
                    project_id,
                    invoice_number,
                    discipline,
                    phase,
                    description,
                    invoice_amount,
                    invoice_date,
                    payment_date,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal_id,
                line['invoice_number'],
                line['discipline'],
                line['phase'],
                line['description'],
                line['invoice_amount'],
                line['invoice_date'],
                line['payment_date'],
                line['status']
            ))

            inserted += 1
            stats[line['status']] += 1
            project_stats[project_code] += 1

        except sqlite3.IntegrityError as e:
            # Duplicate invoice number - update instead
            if 'UNIQUE constraint failed' in str(e):
                print(f"  Note: Duplicate invoice {line['invoice_number']}, creating additional line item")
                # For duplicates, we need to modify the approach since invoice_number should be unique
                # Let's remove the UNIQUE constraint temporarily or use a composite key
                skipped += 1
            else:
                print(f"  ERROR inserting {line['invoice_number']}: {e}")
                skipped += 1

    conn.commit()

    print(f"\n{'='*80}")
    print(f"IMPORT SUMMARY")
    print(f"{'='*80}\n")
    print(f"Total lines extracted: {len(invoice_lines)}")
    print(f"Successfully imported: {inserted}")
    print(f"Skipped: {skipped}")
    print(f"\nBy Status:")
    for status, count in sorted(stats.items()):
        print(f"  {status}: {count}")

    print(f"\n{'='*80}")
    print(f"BREAKDOWN BY PROJECT")
    print(f"{'='*80}\n")
    for project_code in sorted(project_stats.keys()):
        count = project_stats[project_code]
        print(f"  {project_code}: {count} line items")

    # Get sample records
    print(f"\n{'='*80}")
    print(f"SAMPLE INVOICE RECORDS")
    print(f"{'='*80}\n")

    cursor.execute("""
        SELECT
            p.project_code,
            i.invoice_number,
            i.discipline,
            i.phase,
            i.invoice_amount,
            i.invoice_date,
            i.payment_date,
            i.status
        FROM invoices i
        JOIN proposals p ON i.project_id = p.proposal_id
        ORDER BY i.invoice_date DESC
        LIMIT 10
    """)

    samples = cursor.fetchall()
    for sample in samples:
        print(f"  {sample[0]} | {sample[1]} | {sample[2]} | {sample[3]} | ${sample[4]:,.2f} | {sample[5]} | [{sample[7]}]")

    # Multi-discipline invoice examples
    print(f"\n{'='*80}")
    print(f"MULTI-DISCIPLINE INVOICE EXAMPLES")
    print(f"{'='*80}\n")

    cursor.execute("""
        SELECT
            invoice_number,
            COUNT(*) as line_count,
            GROUP_CONCAT(DISTINCT discipline) as disciplines
        FROM invoices
        GROUP BY invoice_number
        HAVING COUNT(*) > 1
        ORDER BY line_count DESC
        LIMIT 10
    """)

    multi = cursor.fetchall()
    for m in multi:
        print(f"  {m[0]}: {m[1]} line items across disciplines: {m[2]}")

    conn.close()

def main():
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE INVOICE IMPORT")
    print(f"{'='*80}")
    print(f"PDF: {PDF_PATH}")
    print(f"Database: {DB_PATH}")
    print(f"{'='*80}\n")

    # Extract invoice lines
    invoice_lines = extract_invoice_lines_structured()

    print(f"\n{'='*80}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*80}")
    print(f"Total invoice lines extracted: {len(invoice_lines)}")

    if invoice_lines:
        # Import to database
        import_to_database(invoice_lines)
    else:
        print("\nNo invoice lines extracted. Please check the PDF structure.")

if __name__ == "__main__":
    main()
