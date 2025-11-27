#!/usr/bin/env python3
"""
Complete Invoice Parser for All 26 Projects - Enhanced Version
Extracts every invoice from FULL_INVOICE_DATA.txt with proper project codes, phases, disciplines, amounts, and dates.
"""

import re
import csv
from datetime import datetime
from typing import List, Dict, Optional

def parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats to YYYY-MM-DD"""
    if not date_str or date_str.strip() == '0.00' or date_str.strip() == '':
        return None

    date_str = date_str.strip()

    # Handle "06 & 27 oct 2025" format - take first date
    if '&' in date_str and any(month in date_str.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
        parts = date_str.split('&')
        # Get first number and month+year from end
        first_num = parts[0].strip().split()[0]
        month_year = ' '.join(date_str.split()[-2:])
        date_str = f"{first_num} {month_year}"

    # Handle "Nov 26.20" format (most common)
    match = re.match(r'([A-Za-z]+)\s+(\d+)\.(\d+)', date_str)
    if match:
        month_str, day, year = match.groups()
        year = '20' + year
        try:
            date_obj = datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y")
            return date_obj.strftime("%Y-%m-%d")
        except:
            pass

    # Handle "8-Jan-21" or "7-Jan-21" format
    try:
        date_obj = datetime.strptime(date_str, "%d-%b-%y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        pass

    # Handle "01-11-2023" format
    try:
        date_obj = datetime.strptime(date_str, "%d-%m-%Y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        pass

    # Handle "3 Apr 24" or "3-Apr-24" format
    try:
        date_obj = datetime.strptime(date_str.replace('-', ' '), "%d %b %y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        pass

    # Handle "6-Oct-25" format
    try:
        date_obj = datetime.strptime(date_str, "%d-%b-%y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        pass

    return None

def parse_amount(amount_str: str) -> float:
    """Parse amount string to float"""
    if not amount_str or amount_str.strip() == '':
        return 0.0
    # Remove commas and convert
    try:
        return float(amount_str.replace(',', ''))
    except:
        return 0.0

def clean_line(line: str) -> str:
    """Remove line number prefix from cat -n format"""
    match = re.match(r'\s*\d+→(.+)', line)
    if match:
        return match.group(1)
    return line

def extract_invoice_data(line: str, next_line: str = '') -> Optional[Dict]:
    """Extract invoice data from a line"""
    # Look for invoice pattern
    invoice_match = re.search(r'([IT]\d{2}-\d{3}[A-Z]?(?:&[A-Z])?)', line)
    if not invoice_match:
        return None

    invoice_num = invoice_match.group(1)

    # Split at invoice number
    parts = line.split(invoice_num, 1)
    description = parts[0].strip()
    after_inv = parts[1].strip() if len(parts) > 1 else ''

    # Parse percentage if present
    percent_match = re.search(r'(\d+)%', line)
    percent = percent_match.group(1) if percent_match else None

    # Extract numeric values from after invoice section
    # Pattern: amount invoice_num [percent] invoice_date outstanding remaining paid payment_date

    # Find all amounts (formatted as ###,###.##)
    amounts = re.findall(r'([\d,]+\.\d{2})', after_inv)

    # Find all dates
    date_patterns = [
        r'([A-Za-z]{3}\s+\d+\.\d+)',  # Nov 26.20
        r'(\d+-[A-Za-z]+-\d+)',        # 7-Jan-21
        r'(\d+\s+[A-Za-z]+\s+\d+)',    # 3 Apr 24
        r'(\d+-[A-Za-z]{3}-\d+)',      # 6-Oct-25
    ]

    dates_found = []
    for pattern in date_patterns:
        dates_found.extend(re.findall(pattern, line))

    # Parse dates
    parsed_dates = [parse_date(d) for d in dates_found]
    parsed_dates = [d for d in parsed_dates if d]

    invoice_date = parsed_dates[0] if len(parsed_dates) > 0 else None
    payment_date = parsed_dates[1] if len(parsed_dates) > 1 else None

    # Parse amounts (typically: outstanding, remaining, paid in that order)
    outstanding = parse_amount(amounts[0]) if len(amounts) > 0 else 0.0
    remaining = parse_amount(amounts[1]) if len(amounts) > 1 else 0.0
    paid = parse_amount(amounts[2]) if len(amounts) > 2 else 0.0

    # Determine invoice amount and status
    if paid > 0 and outstanding == 0:
        invoice_amount = paid
        payment_amount = paid
        outstanding_amount = 0.0
        status = 'paid'
    elif paid > 0 and outstanding > 0:
        invoice_amount = outstanding + paid
        payment_amount = paid
        outstanding_amount = outstanding
        status = 'partial'
    elif outstanding > 0 and paid == 0:
        invoice_amount = outstanding
        payment_amount = 0.0
        outstanding_amount = outstanding
        status = 'outstanding'
    else:
        # Could be remaining only
        invoice_amount = remaining
        payment_amount = 0.0
        outstanding_amount = remaining
        status = 'outstanding'

    return {
        'invoice_number': invoice_num,
        'description': description,
        'invoice_date': invoice_date,
        'payment_date': payment_date,
        'invoice_amount': invoice_amount,
        'payment_amount': payment_amount,
        'outstanding_amount': outstanding_amount,
        'percent': percent,
        'status': status
    }

def determine_phase(description: str) -> str:
    """Determine phase from description"""
    desc_lower = description.lower()

    if 'mobilization' in desc_lower or 'mobilization fee' in desc_lower:
        return 'Mobilization Fee'
    elif 'conceptual design' in desc_lower or 'concept design' in desc_lower:
        return 'Conceptual Design'
    elif 'schematic design' in desc_lower:
        return 'Schematic Design'
    elif 'design development' in desc_lower:
        return 'Design Development'
    elif 'construction document' in desc_lower:
        return 'Construction Documents'
    elif 'construction observation' in desc_lower:
        return 'Construction Observation'
    elif 'installment' in desc_lower:
        return 'Monthly Installment'
    elif 'monthly fee' in desc_lower:
        return 'Monthly Fee'
    elif 'mural' in desc_lower:
        return 'Mural'
    elif 'redesign' in desc_lower:
        return 'Redesign'
    elif 'branding' in desc_lower:
        return 'Branding Consultancy'
    elif 'additional service' in desc_lower:
        return 'Additional Service'

    return 'Other'

def main():
    input_file = '/Users/lukassherman/Desktop/FULL_INVOICE_DATA.txt'
    output_file = '/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/reports/ALL_INVOICES_PARSED.csv'

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    invoices = []
    current_project = None
    current_project_name = None
    current_discipline = None

    # Process lines
    i = 0
    while i < len(lines):
        line = clean_line(lines[i])
        next_line = clean_line(lines[i+1]) if i+1 < len(lines) else ''

        # Skip header and summary lines
        if 'Project Expiry Project Title' in line or 'Page' in line or 'Print on' in line:
            i += 1
            continue

        # Check for project header
        # Format: "1 20 BK-047 Sep-26 Audley Square House..."
        project_match = re.match(r'^(\d+)\s+(\d{2}\s+BK-\d+)\s+([A-Za-z]+-\d+)\s+(.+)', line)
        if project_match:
            project_num, project_code, expiry, rest = project_match.groups()
            current_project = project_code.replace(' ', '')

            # Extract project name (before phase descriptions)
            project_name = rest.split('Mobilization')[0].strip()
            project_name = project_name.split('Conceptual')[0].strip()
            project_name = project_name.split('Design Development')[0].strip()
            project_name = project_name.split('1st installment')[0].strip()
            project_name = project_name.split('Monthly Fee')[0].strip()
            project_name = project_name.split('Package')[0].strip()

            current_project_name = project_name
            current_discipline = None  # Reset discipline
            i += 1
            continue

        # Check for discipline markers
        if re.match(r'^Landscape Architect', line, re.IGNORECASE):
            current_discipline = 'Landscape Architectural'
            i += 1
            continue
        elif re.match(r'^Architect(iral|ural)\s*$', line, re.IGNORECASE):
            current_discipline = 'Architectural'
            i += 1
            continue
        elif re.match(r'^Interior Design', line, re.IGNORECASE):
            current_discipline = 'Interior Design'
            i += 1
            continue

        # Try to extract invoice from line
        if current_project and re.search(r'[IT]\d{2}-\d{3}', line):
            invoice_data = extract_invoice_data(line, next_line)

            if invoice_data and invoice_data['invoice_amount'] > 0:
                phase = determine_phase(invoice_data['description'])

                # Build notes
                notes = []
                if invoice_data['percent']:
                    notes.append(f"{invoice_data['percent']}% payment")

                invoice = {
                    'project_code': current_project,
                    'project_name': current_project_name or '',
                    'invoice_number': invoice_data['invoice_number'],
                    'invoice_date': invoice_data['invoice_date'] or '',
                    'invoice_amount': invoice_data['invoice_amount'],
                    'payment_date': invoice_data['payment_date'] or '',
                    'payment_amount': invoice_data['payment_amount'],
                    'outstanding_amount': invoice_data['outstanding_amount'],
                    'phase': phase,
                    'discipline': current_discipline or 'General',
                    'notes': '; '.join(notes),
                    'status': invoice_data['status']
                }

                invoices.append(invoice)

        i += 1

    # Write to CSV
    fieldnames = [
        'project_code', 'project_name', 'invoice_number', 'invoice_date',
        'invoice_amount', 'payment_date', 'payment_amount', 'outstanding_amount',
        'phase', 'discipline', 'notes', 'status'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(invoices)

    # Generate summary
    print(f"\n{'='*80}")
    print(f"COMPLETE INVOICE PARSING SUMMARY")
    print(f"{'='*80}\n")

    print(f"Total invoices parsed: {len(invoices)}")
    print(f"Output file: {output_file}\n")

    # Count by project
    project_counts = {}
    project_totals = {}
    project_paid = {}
    project_outstanding = {}

    for inv in invoices:
        code = inv['project_code']
        project_counts[code] = project_counts.get(code, 0) + 1
        project_totals[code] = project_totals.get(code, 0) + inv['invoice_amount']
        project_paid[code] = project_paid.get(code, 0) + inv['payment_amount']
        project_outstanding[code] = project_outstanding.get(code, 0) + inv['outstanding_amount']

    print(f"{'Project Code':<15} {'Invoices':>9} {'Total Invoiced':>18} {'Paid':>18} {'Outstanding':>18}")
    print(f"{'-'*82}")

    for code in sorted(project_counts.keys()):
        print(f"{code:<15} {project_counts[code]:>9} "
              f"${project_totals[code]:>16,.2f} "
              f"${project_paid[code]:>16,.2f} "
              f"${project_outstanding[code]:>16,.2f}")

    print(f"{'-'*82}")
    total_invoiced = sum(project_totals.values())
    total_paid = sum(project_paid.values())
    total_outstanding = sum(project_outstanding.values())

    print(f"{'GRAND TOTAL':<15} {len(invoices):>9} "
          f"${total_invoiced:>16,.2f} "
          f"${total_paid:>16,.2f} "
          f"${total_outstanding:>16,.2f}\n")

    # Status breakdown
    status_counts = {}
    for inv in invoices:
        status_counts[inv['status']] = status_counts.get(inv['status'], 0) + 1

    print(f"Invoice Status Breakdown:")
    print(f"{'-'*40}")
    for status in ['paid', 'partial', 'outstanding']:
        count = status_counts.get(status, 0)
        pct = (count / len(invoices) * 100) if len(invoices) > 0 else 0
        print(f"  {status.capitalize():<15}: {count:>6} ({pct:>5.1f}%)")

    # Phase breakdown
    phase_counts = {}
    for inv in invoices:
        phase_counts[inv['phase']] = phase_counts.get(inv['phase'], 0) + 1

    print(f"\nInvoice Phase Breakdown:")
    print(f"{'-'*40}")
    for phase, count in sorted(phase_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(invoices) * 100) if len(invoices) > 0 else 0
        print(f"  {phase:<25}: {count:>6} ({pct:>5.1f}%)")

    # Discipline breakdown
    discipline_counts = {}
    for inv in invoices:
        discipline_counts[inv['discipline']] = discipline_counts.get(inv['discipline'], 0) + 1

    print(f"\nInvoice Discipline Breakdown:")
    print(f"{'-'*40}")
    for disc, count in sorted(discipline_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(invoices) * 100) if len(invoices) > 0 else 0
        print(f"  {disc:<25}: {count:>6} ({pct:>5.1f}%)")

    print(f"\n{'='*80}\n")

    # Identify any potential parsing issues
    issues = []
    for inv in invoices:
        if not inv['invoice_date']:
            issues.append(f"Missing invoice date: {inv['invoice_number']}")
        if inv['status'] == 'paid' and not inv['payment_date']:
            issues.append(f"Paid invoice missing payment date: {inv['invoice_number']}")

    if issues:
        print(f"POTENTIAL PARSING ISSUES ({len(issues)}):")
        print(f"{'-'*40}")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues)-10} more")
        print()

if __name__ == '__main__':
    main()
