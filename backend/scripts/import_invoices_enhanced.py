#!/usr/bin/env python3
"""
ENHANCED Invoice Import with Better Discipline Tracking
Properly tracks discipline context and payment status
"""

import pdfplumber
import sqlite3
import re
from datetime import datetime
from collections import defaultdict

PDF_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/2025-11/Project Status as of 10 Nov 25 (Updated).pdf"
DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

def parse_date(date_str):
    """Parse date from format like 'Aug 26.25' or '6-Oct-25' to '2025-08-26'"""
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()

    months = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }

    # Pattern 1: "Aug 26.25"
    match = re.match(r'([A-Z][a-z]{2})\s+(\d{1,2})\.(\d{2})', date_str)
    if match:
        month_abbr, day, year_short = match.groups()
        month = months.get(month_abbr)
        if month:
            year = f"20{year_short}"
            return f"{year}-{month}-{day.zfill(2)}"

    # Pattern 2: "6-Oct-25"
    match = re.match(r'(\d{1,2})-([A-Z][a-z]{2})-(\d{2})', date_str)
    if match:
        day, month_abbr, year_short = match.groups()
        month = months.get(month_abbr)
        if month:
            year = f"20{year_short}"
            return f"{year}-{month}-{day.zfill(2)}"

    return None

def parse_amount(amount_str):
    """Parse amount string to float"""
    if not amount_str:
        return 0.0
    try:
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

def extract_invoice_data_enhanced():
    """Enhanced extraction with better discipline and payment tracking"""
    invoice_lines = []

    print(f"\n{'='*120}")
    print(f"ENHANCED INVOICE EXTRACTION")
    print(f"{'='*120}\n")

    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Total pages: {len(pdf.pages)}\n")

        for page_num, page in enumerate(pdf.pages, 1):
            print(f"{'─'*120}")
            print(f"PAGE {page_num}")
            print(f"{'─'*120}")

            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')

            # Context tracking
            current_project_code = None
            current_project_title = None
            current_discipline = None
            project_count = 0

            i = 0
            while i < len(lines):
                line = lines[i]

                # Project header pattern: "1 20 BK-047 Sep-26 Audley Square House..."
                proj_match = re.match(r'^(\d+)\s+(\d{2}\s+BK-\d{3})\s+([A-Za-z]+-\d{2})\s+(.+)', line)
                if proj_match:
                    seq, proj_code, expiry, title = proj_match.groups()
                    current_project_code = proj_code
                    current_project_title = title
                    current_discipline = None  # Reset discipline
                    project_count += 1
                    print(f"\n[{project_count}] {proj_code}: {title[:60]}...")
                    i += 1
                    continue

                # Discipline markers - must be exact matches
                line_stripped = line.strip()

                if line_stripped == 'Landscape Architectural' or line_stripped.startswith('Landscape Architect'):
                    current_discipline = 'Landscape Architectural'
                    print(f"  ├─ {current_discipline}")
                    i += 1
                    continue

                elif line_stripped == 'Architectural':
                    current_discipline = 'Architectural'
                    print(f"  ├─ {current_discipline}")
                    i += 1
                    continue

                elif line_stripped == 'Interior Design':
                    current_discipline = 'Interior Design'
                    print(f"  ├─ {current_discipline}")
                    i += 1
                    continue

                elif 'Branding' in line_stripped:
                    current_discipline = 'Branding'
                    print(f"  ├─ {current_discipline}")
                    i += 1
                    continue

                # Invoice line detection
                if current_project_code:
                    inv_match = re.search(r'(I\d{2}-\d{3}[A-Z]?(?:&[A-Z])?|T\d{2}-\d{3}[A-Z]?)', line)
                    if inv_match:
                        invoice_number = inv_match.group(1)

                        # Determine phase from the line
                        phase = None
                        if 'Mobilization Fee' in line:
                            phase = 'Mobilization Fee'
                        elif 'Conceptual Design' in line:
                            phase = 'Conceptual Design'
                        elif 'Design Development' in line:
                            phase = 'Design Development'
                        elif 'Schematic Design' in line:
                            phase = 'Schematic Design'
                        elif 'Construction Documents' in line:
                            phase = 'Construction Documents'
                        elif 'Construction Observation' in line:
                            phase = 'Construction Observation'
                        elif 'installment' in line.lower():
                            inst = re.search(r'(\d+(?:st|nd|rd|th)\s+installment[^I]*)', line)
                            phase = inst.group(1).strip() if inst else 'Installment'

                        # Parse the line for amounts and dates
                        # The PDF format is: Description Amount Invoice# % InvoiceDate Outstanding Remaining Paid DatePaid

                        # Extract all amounts
                        amounts_raw = re.findall(r'([\d,]+\.\d{2})', line)
                        amounts = [parse_amount(a) for a in amounts_raw]

                        # Extract all dates
                        dates = re.findall(r'([A-Z][a-z]{2}\s+\d{1,2}\.\d{2}|\d{1,2}-[A-Z][a-z]{2}-\d{2})', line)

                        # Logic for extracting the correct values:
                        # Pattern: Description Amount Invoice# [%] InvoiceDate Outstanding Remaining Paid DatePaid
                        invoice_amount = amounts[0] if len(amounts) >= 1 else 0.0
                        invoice_date = parse_date(dates[0]) if len(dates) >= 1 else None

                        # Check for payment date (usually last date in line)
                        payment_date = None
                        paid_amount = 0.0

                        # If we have more amounts, check the "Paid" column (4th amount in typical format)
                        if len(amounts) >= 4:
                            paid_amount = amounts[3]

                        # If we have a second date, that's the payment date
                        if len(dates) >= 2:
                            payment_date = parse_date(dates[1])

                        # Determine status
                        if paid_amount > 0 or payment_date:
                            status = 'Paid'
                        else:
                            status = 'Outstanding'

                        # Only add if amount is reasonable
                        if invoice_amount > 1:  # Filter out tiny amounts that are likely parsing errors
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

                            status_icon = "✓" if status == "Paid" else "○"
                            disc_display = (current_discipline or 'General')[:15]
                            phase_display = (phase or 'N/A')[:25]
                            print(f"  │  {status_icon} {invoice_number:12s} {disc_display:15s} {phase_display:25s} ${invoice_amount:>12,.2f}")

                i += 1

    return invoice_lines

def import_to_database(invoice_lines):
    """Import to database with enhanced error handling"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"\n{'='*120}")
    print(f"DATABASE IMPORT")
    print(f"{'='*120}\n")

    # Clear
    print("Clearing existing invoices...")
    cursor.execute("DELETE FROM invoices")
    conn.commit()
    print("  ✓ Cleared\n")

    # Stats
    stats = defaultdict(int)
    discipline_stats = defaultdict(int)
    project_stats = defaultdict(lambda: {'count': 0, 'total': 0.0, 'disciplines': set()})
    inserted = 0
    skipped = 0
    missing_projects = set()

    for line in invoice_lines:
        project_code = line['project_code']
        proposal_id = get_proposal_id_by_project_code(conn, project_code)

        if not proposal_id:
            if project_code not in missing_projects:
                print(f"  ⚠ No proposal: {project_code}")
                missing_projects.add(project_code)
            skipped += 1
            continue

        try:
            cursor.execute("""
                INSERT INTO invoices (
                    project_id, invoice_number, discipline, phase,
                    description, invoice_amount, invoice_date,
                    payment_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal_id, line['invoice_number'], line['discipline'],
                line['phase'], line['description'], line['invoice_amount'],
                line['invoice_date'], line['payment_date'], line['status']
            ))

            inserted += 1
            stats[line['status']] += 1
            discipline_stats[line['discipline']] += 1
            project_stats[project_code]['count'] += 1
            project_stats[project_code]['total'] += line['invoice_amount']
            project_stats[project_code]['disciplines'].add(line['discipline'])

        except Exception as e:
            print(f"  ✗ Error: {line['invoice_number']}: {e}")
            skipped += 1

    conn.commit()

    # Reports
    print(f"\n{'='*120}")
    print(f"IMPORT SUMMARY")
    print(f"{'='*120}\n")
    print(f"Extracted:  {len(invoice_lines):4d}")
    print(f"Imported:   {inserted:4d}")
    print(f"Skipped:    {skipped:4d}")

    print(f"\nBy Status:")
    for status, count in sorted(stats.items()):
        pct = (count / inserted * 100) if inserted > 0 else 0
        print(f"  {status:15s}: {count:4d} ({pct:5.1f}%)")

    print(f"\nBy Discipline:")
    for disc, count in sorted(discipline_stats.items(), key=lambda x: -x[1]):
        pct = (count / inserted * 100) if inserted > 0 else 0
        print(f"  {disc:30s}: {count:4d} ({pct:5.1f}%)")

    print(f"\n{'='*120}")
    print(f"PROJECT BREAKDOWN ({len(project_stats)} projects)")
    print(f"{'='*120}\n")

    for proj_code in sorted(project_stats.keys()):
        data = project_stats[proj_code]
        discs = ', '.join(sorted(data['disciplines']))
        print(f"  {proj_code:12s} │ {data['count']:3d} lines │ {len(data['disciplines'])} disciplines │ ${data['total']:>15,.2f} │ {discs}")

    # Multi-discipline invoices
    print(f"\n{'='*120}")
    print(f"MULTI-DISCIPLINE INVOICES")
    print(f"{'='*120}\n")

    cursor.execute("""
        SELECT invoice_number, COUNT(*) as cnt,
               GROUP_CONCAT(DISTINCT discipline) as discs,
               SUM(invoice_amount) as total
        FROM invoices
        GROUP BY invoice_number
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 20
    """)

    for row in cursor.fetchall():
        print(f"  {row[0]:12s} │ {row[1]} items │ {row[2]:70s} │ ${row[3]:>12,.2f}")

    # Financial summary
    print(f"\n{'='*120}")
    print(f"FINANCIAL SUMMARY")
    print(f"{'='*120}\n")

    cursor.execute("SELECT SUM(invoice_amount) FROM invoices WHERE status = 'Paid'")
    paid = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(invoice_amount) FROM invoices WHERE status = 'Outstanding'")
    outstanding = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(invoice_amount) FROM invoices")
    total = cursor.fetchone()[0] or 0

    print(f"  Paid:        ${paid:>18,.2f}")
    print(f"  Outstanding: ${outstanding:>18,.2f}")
    print(f"  {'─'*40}")
    print(f"  TOTAL:       ${total:>18,.2f}")

    conn.close()

def main():
    print(f"\n{'#'*120}")
    print(f"#{'ENHANCED INVOICE IMPORT - ACCOUNTANT PDF REPORT':^118s}#")
    print(f"{'#'*120}\n")
    print(f"PDF:      {PDF_PATH}")
    print(f"Database: {DB_PATH}")

    invoice_lines = extract_invoice_data_enhanced()

    print(f"\n{'='*120}")
    print(f"EXTRACTION COMPLETE: {len(invoice_lines)} line items")
    print(f"{'='*120}")

    if invoice_lines:
        import_to_database(invoice_lines)
    else:
        print("\n⚠ No data extracted!")

    print(f"\n{'#'*120}")
    print(f"#{'IMPORT COMPLETE':^118s}#")
    print(f"{'#'*120}\n")

if __name__ == "__main__":
    main()
