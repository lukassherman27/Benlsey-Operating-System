#!/usr/bin/env python3
"""
FINAL Comprehensive Invoice Import from PDF
Extracts ALL invoice line items with proper parsing
"""

import pdfplumber
import sqlite3
import re
from datetime import datetime
from collections import defaultdict

PDF_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/05_FILES/BY_DATE/2025-11/Project Status as of 10 Nov 25 (Updated).pdf"
DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

def parse_date(date_str):
    """Parse date from format like 'Aug 26.25' to '2025-08-26'"""
    if not date_str or not date_str.strip():
        return None

    months = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }

    match = re.match(r'([A-Z][a-z]{2})\s+(\d{1,2})\.(\d{2})', date_str.strip())
    if match:
        month_abbr, day, year_short = match.groups()
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

def extract_invoice_data():
    """Extract all invoice line items from PDF"""
    invoice_lines = []

    print(f"\n{'='*100}")
    print(f"EXTRACTING INVOICE DATA FROM PDF")
    print(f"{'='*100}\n")

    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"Total pages: {len(pdf.pages)}\n")

        for page_num, page in enumerate(pdf.pages, 1):
            print(f"{'─'*100}")
            print(f"PAGE {page_num}")
            print(f"{'─'*100}")

            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')

            # State tracking
            current_project = None
            current_discipline = None
            project_counter = 0

            for line_idx, line in enumerate(lines):
                # Match project header: "1 20 BK-047 Sep-26 Audley Square..."
                project_match = re.match(r'^(\d+)\s+(\d{2}\s+BK-\d{3})\s+([A-Za-z]+-\d{2})\s+(.+?)(?:\s+Mobilization Fee|\s+Conceptual|$)', line)
                if project_match:
                    seq, project_code, expiry, title_part = project_match.groups()
                    current_project = project_code
                    project_counter += 1
                    current_discipline = None
                    print(f"\n[{project_counter}] {project_code}: {title_part[:50]}...")
                    continue

                # Discipline section headers
                if re.match(r'^\s*Landscape Architectural?\s*$', line) or 'Landscape Architect and Architectural' in line:
                    current_discipline = 'Landscape Architectural'
                    print(f"  └─ {current_discipline}")
                    continue
                elif re.match(r'^\s*Architectural\s*$', line):
                    current_discipline = 'Architectural'
                    print(f"  └─ {current_discipline}")
                    continue
                elif re.match(r'^\s*Interior Design\s*$', line):
                    current_discipline = 'Interior Design'
                    print(f"  └─ {current_discipline}")
                    continue
                elif 'Branding Consultancy' in line:
                    current_discipline = 'Branding'
                    print(f"  └─ {current_discipline}")
                    continue

                # Invoice line detection
                if current_project and re.search(r'(I\d{2}-\d{3}[A-Z]?(?:&[A-Z])?|T\d{2}-\d{3}[A-Z]?)', line):
                    invoice_match = re.search(r'(I\d{2}-\d{3}[A-Z]?(?:&[A-Z])?|T\d{2}-\d{3}[A-Z]?)', line)
                    if not invoice_match:
                        continue

                    invoice_number = invoice_match.group(1)

                    # Determine phase
                    phase = None
                    desc = None

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
                        inst = re.search(r'(\d+(?:st|nd|rd|th)\s+installment\s+[A-Z][a-z]+\s+\d+)', line)
                        phase = inst.group(1) if inst else 'Installment'
                        desc = phase

                    # Extract amounts: pattern is Amount Invoice# % InvoiceDate Outstanding Remaining Paid DatePaid
                    amounts = re.findall(r'([\d,]+\.\d{2})', line)
                    amounts = [parse_amount(a) for a in amounts]

                    # Extract dates
                    dates = re.findall(r'([A-Z][a-z]{2}\s+\d{1,2}\.\d{2})', line)

                    # Parse based on position
                    invoice_amount = amounts[0] if len(amounts) >= 1 else 0.0
                    invoice_date = parse_date(dates[0]) if len(dates) >= 1 else None

                    # Paid amount is typically the last non-zero amount in the line
                    paid_amount = 0.0
                    payment_date = None

                    if len(amounts) >= 4:
                        # Pattern: Amount Invoice# % Date Outstanding Remaining Paid DatePaid
                        # Index: 0=Amount, 1=Outstanding, 2=Remaining, 3=Paid
                        paid_amount = amounts[3] if len(amounts) > 3 else 0.0

                    if paid_amount > 0 and len(dates) >= 2:
                        payment_date = parse_date(dates[1])

                    status = 'Paid' if paid_amount > 0 and payment_date else 'Outstanding'

                    # Only add if we have a valid amount
                    if invoice_amount > 0:
                        invoice_line = {
                            'project_code': current_project,
                            'invoice_number': invoice_number,
                            'discipline': current_discipline or 'General',
                            'phase': phase or 'Unspecified',
                            'description': desc,
                            'invoice_amount': invoice_amount,
                            'invoice_date': invoice_date,
                            'payment_date': payment_date,
                            'status': status
                        }

                        invoice_lines.append(invoice_line)

                        status_icon = "✓" if status == "Paid" else "○"
                        print(f"     {status_icon} {invoice_number}: {phase or 'N/A':30s} ${invoice_amount:>12,.2f} [{status}]")

    return invoice_lines

def import_to_database(invoice_lines):
    """Import to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"\n{'='*100}")
    print(f"IMPORTING TO DATABASE")
    print(f"{'='*100}\n")

    # Clear existing
    print("Clearing existing invoices...")
    cursor.execute("DELETE FROM invoices")
    conn.commit()
    print("  ✓ Cleared\n")

    # Statistics
    stats = defaultdict(int)
    project_stats = defaultdict(list)
    inserted = 0
    skipped = 0
    missing_projects = set()

    for line in invoice_lines:
        project_code = line['project_code']
        proposal_id = get_proposal_id_by_project_code(conn, project_code)

        if not proposal_id:
            if project_code not in missing_projects:
                print(f"  ⚠ No proposal found for: {project_code}")
                missing_projects.add(project_code)
            skipped += 1
            continue

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
            project_stats[project_code].append(line)

        except Exception as e:
            print(f"  ✗ Error inserting {line['invoice_number']}: {e}")
            skipped += 1

    conn.commit()

    # Summary
    print(f"\n{'='*100}")
    print(f"IMPORT SUMMARY")
    print(f"{'='*100}\n")
    print(f"Total extracted:      {len(invoice_lines)}")
    print(f"Successfully imported: {inserted}")
    print(f"Skipped:              {skipped}")
    print(f"\nBy Status:")
    for status, count in sorted(stats.items()):
        print(f"  {status:15s}: {count}")

    # Project breakdown
    print(f"\n{'='*100}")
    print(f"BREAKDOWN BY PROJECT ({len(project_stats)} projects)")
    print(f"{'='*100}\n")

    for project_code in sorted(project_stats.keys()):
        lines = project_stats[project_code]
        disciplines = set([l['discipline'] for l in lines])
        total_amount = sum([l['invoice_amount'] for l in lines])
        print(f"  {project_code}: {len(lines):3d} line items | {len(disciplines)} disciplines | ${total_amount:>15,.2f}")

    # Samples
    print(f"\n{'='*100}")
    print(f"SAMPLE INVOICE RECORDS (10 most recent)")
    print(f"{'='*100}\n")

    cursor.execute("""
        SELECT
            p.project_code,
            i.invoice_number,
            i.discipline,
            i.phase,
            i.invoice_amount,
            i.invoice_date,
            i.status
        FROM invoices i
        JOIN proposals p ON i.project_id = p.proposal_id
        ORDER BY i.invoice_date DESC
        LIMIT 10
    """)

    for row in cursor.fetchall():
        print(f"  {row[0]:12s} | {row[1]:10s} | {row[2]:25s} | {row[3]:30s} | ${row[4]:>12,.2f} | {row[5]} | [{row[6]}]")

    # Multi-discipline invoices
    print(f"\n{'='*100}")
    print(f"MULTI-DISCIPLINE INVOICE EXAMPLES")
    print(f"{'='*100}\n")

    cursor.execute("""
        SELECT
            invoice_number,
            COUNT(*) as line_count,
            GROUP_CONCAT(DISTINCT discipline) as disciplines,
            SUM(invoice_amount) as total_amount
        FROM invoices
        GROUP BY invoice_number
        HAVING COUNT(*) > 1
        ORDER BY line_count DESC
        LIMIT 15
    """)

    multi = cursor.fetchall()
    for m in multi:
        print(f"  {m[0]:10s}: {m[1]} line items | Disciplines: {m[2]:60s} | Total: ${m[3]:>12,.2f}")

    # Final totals
    print(f"\n{'='*100}")
    print(f"FINANCIAL SUMMARY")
    print(f"{'='*100}\n")

    cursor.execute("SELECT SUM(invoice_amount) FROM invoices WHERE status = 'Paid'")
    paid_total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(invoice_amount) FROM invoices WHERE status = 'Outstanding'")
    outstanding_total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(invoice_amount) FROM invoices")
    grand_total = cursor.fetchone()[0] or 0

    print(f"  Paid:        ${paid_total:>15,.2f}")
    print(f"  Outstanding: ${outstanding_total:>15,.2f}")
    print(f"  GRAND TOTAL: ${grand_total:>15,.2f}")

    conn.close()

def main():
    print(f"\n{'#'*100}")
    print(f"#{'COMPREHENSIVE INVOICE IMPORT FROM ACCOUNTANT PDF REPORT':^98s}#")
    print(f"{'#'*100}\n")
    print(f"PDF:      {PDF_PATH}")
    print(f"Database: {DB_PATH}")

    # Extract
    invoice_lines = extract_invoice_data()

    print(f"\n{'='*100}")
    print(f"EXTRACTION COMPLETE: {len(invoice_lines)} line items extracted")
    print(f"{'='*100}")

    if invoice_lines:
        import_to_database(invoice_lines)
    else:
        print("\n⚠ No invoice lines extracted!")

    print(f"\n{'#'*100}")
    print(f"#{'IMPORT COMPLETE':^98s}#")
    print(f"{'#'*100}\n")

if __name__ == "__main__":
    main()
