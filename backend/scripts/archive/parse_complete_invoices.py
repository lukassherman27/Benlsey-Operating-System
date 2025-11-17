#!/usr/bin/env python3
"""
COMPLETE Invoice Parser for All 26 Projects
Properly handles project codes, disciplines, phases, amounts, and dates for ALL invoices.
"""

import re
import csv
from datetime import datetime
from typing import List, Dict, Optional

def parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats to YYYY-MM-DD"""
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()

    # Handle "06 & 27 oct 2025" format - take first date
    if '&' in date_str and any(month in date_str.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
        parts = date_str.split('&')
        if len(parts) > 0 and parts[0].strip():
            first_part = parts[0].strip().split()
            if len(first_part) > 0:
                first_num = first_part[0]
                date_parts = date_str.split()
                if len(date_parts) >= 2:
                    month_year = ' '.join(date_parts[-2:])
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

    # Handle various date formats
    for fmt in ["%d-%b-%y", "%d-%m-%Y", "%d %b %y", "%d-%b-%Y"]:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y-%m-%d")
        except:
            pass

    return None

def parse_amount(amount_str: str) -> float:
    """Parse amount string to float"""
    if not amount_str or amount_str.strip() == '':
        return 0.0
    try:
        return float(amount_str.replace(',', '').strip())
    except:
        return 0.0

def determine_phase(description: str) -> str:
    """Determine phase from description"""
    desc_lower = description.lower()

    if 'mobilization fee' in desc_lower or 'mobilization' in desc_lower:
        return 'Mobilization Fee'
    elif 'conceptual design' in desc_lower:
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
    elif 'monthly fee' in desc_lower or ('month ' in desc_lower and 'fee' in desc_lower):
        return 'Monthly Fee'
    elif 'mural' in desc_lower:
        return 'Mural'
    elif 'redesign' in desc_lower:
        return 'Redesign'
    elif 'branding' in desc_lower:
        return 'Branding Consultancy'
    elif 'additional service' in desc_lower:
        return 'Additional Service'
    elif 'package' in desc_lower:
        return 'Package'

    return 'Other'

def is_summary_line(line: str) -> bool:
    """Check if line is a summary/total line"""
    # Lines with no invoice number but multiple amounts
    if not re.search(r'[IT]\d{2}-\d{3}', line):
        amount_count = len(re.findall(r'\d{1,3}(?:,\d{3})*\.\d{2}', line))
        if amount_count >= 3:
            return True
    return False

def extract_discipline_from_line(line: str) -> Optional[str]:
    """Extract discipline if line contains discipline marker"""
    # Check for discipline at start or after project metadata
    if re.search(r'\bLandscape Architect', line, re.IGNORECASE):
        return 'Landscape Architectural'
    elif re.search(r'\bInterior Design', line, re.IGNORECASE):
        return 'Interior Design'
    elif re.match(r'^\s*Architect(iral|ural)\s*$', line, re.IGNORECASE):
        return 'Architectural'
    elif re.search(r'\bArchitect(iral|ural)\b(?!.*Interior)(?!.*Landscape)', line, re.IGNORECASE):
        # Only if not preceded by Landscape or Interior
        if not re.search(r'Landscape\s+Architect', line, re.IGNORECASE):
            return 'Architectural'
    return None

def extract_project_info(line: str) -> Optional[Dict]:
    """Extract project code and name from project header line"""
    # Format: "1 20 BK-047 Sep-26 Audley Square House..."
    # Or: "19 BK-018 Nov-23 Villa Project..."
    match = re.match(r'^(\d+\s+)?(\d{2}\s+BK-\d+)\s+([A-Za-z]+-\d+)\s+(.+)', line)
    if match:
        _, project_code, expiry, rest = match.groups()
        project_code = project_code.replace(' ', '')

        # Extract project name (clean up)
        project_name = rest

        # Check for discipline in same line
        discipline = extract_discipline_from_line(rest)

        # Clean project name - remove phases and disciplines
        for keyword in ['Mobilization Fee', 'Conceptual Design', 'Design Development',
                       'Construction Documents', 'Construction Observation', 'Schematic Design',
                       '1st installment', 'Monthly Fee', 'Package', 'Total Fee',
                       'Landscape Architectural', 'Architectural', 'Interior Design']:
            if keyword in project_name:
                project_name = project_name.split(keyword)[0].strip()

        # Also remove amount patterns
        project_name = re.sub(r'\d{1,3}(?:,\d{3})*\.\d{2}.*$', '', project_name).strip()

        return {
            'project_code': project_code,
            'project_name': project_name,
            'discipline': discipline
        }
    return None

def extract_invoice_data(line: str) -> Optional[Dict]:
    """Extract invoice data from line"""
    # Must contain invoice number
    inv_match = re.search(r'([IT]\d{2}-\d{3}[A-Z]?(?:&[A-Z])?)', line)
    if not inv_match:
        return None

    invoice_num = inv_match.group(1)
    inv_pos = line.index(invoice_num)

    # Before invoice: description + amount
    before = line[:inv_pos].strip()
    after = line[inv_pos + len(invoice_num):].strip()

    # Extract description (before amounts)
    amounts_before = re.findall(r'[\d,]+\.\d{2}', before)
    if amounts_before:
        last_amount_pos = before.rfind(amounts_before[-1])
        description = before[:last_amount_pos].strip()
    else:
        description = before.strip()

    # Extract percentage
    percent_match = re.search(r'(\d+)%', after)
    percent = percent_match.group(1) if percent_match else None
    if percent:
        after = after.replace(f'{percent}%', '', 1).strip()

    # Parse tokens from after section
    tokens = after.split()

    invoice_date = None
    payment_date = None
    amounts = []

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # Try to parse as date (look ahead for 2-token dates like "Nov 26.20")
        if i + 1 < len(tokens):
            two_token = f"{token} {tokens[i+1]}"
            parsed = parse_date(two_token)
            if parsed:
                if not invoice_date:
                    invoice_date = parsed
                else:
                    payment_date = parsed
                i += 2
                continue

        # Try single token date
        parsed = parse_date(token)
        if parsed and '-' in token:
            if not invoice_date:
                invoice_date = parsed
            else:
                payment_date = parsed
            i += 1
            continue

        # Check for amount
        if re.match(r'[\d,]+\.\d{2}$', token):
            amounts.append(parse_amount(token))

        i += 1

    # Assign amounts: outstanding, remaining, paid
    outstanding = amounts[0] if len(amounts) > 0 else 0.0
    remaining = amounts[1] if len(amounts) > 1 else 0.0
    paid = amounts[2] if len(amounts) > 2 else 0.0

    # Determine status and amounts
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
        return None

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

def main():
    input_file = '/Users/lukassherman/Desktop/FULL_INVOICE_DATA.txt'
    output_file = '/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/reports/ALL_INVOICES_PARSED.csv'

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    invoices = []
    current_project = None
    current_project_name = None
    current_discipline = None

    for i, line in enumerate(lines):
        line = line.strip()

        # Skip empty, headers, summaries
        if not line or 'Project Expiry' in line or 'Page' in line or 'Print on' in line or 'Remark' in line:
            continue

        if is_summary_line(line):
            continue

        # Check for project header
        project_info = extract_project_info(line)
        if project_info:
            current_project = project_info['project_code']
            current_project_name = project_info['project_name']
            # If discipline in same line, set it
            if project_info['discipline']:
                current_discipline = project_info['discipline']
            continue

        # Check for standalone discipline marker
        standalone_discipline = None
        if re.match(r'^\s*Architect(iral|ural)\s*$', line, re.IGNORECASE):
            standalone_discipline = 'Architectural'
        elif re.match(r'^\s*Interior Design\s*$', line, re.IGNORECASE):
            standalone_discipline = 'Interior Design'
        elif re.match(r'^\s*Landscape Architect', line, re.IGNORECASE) and len(line) < 50:
            standalone_discipline = 'Landscape Architectural'

        if standalone_discipline:
            current_discipline = standalone_discipline
            continue

        # Check for discipline in current line (for invoices)
        line_discipline = extract_discipline_from_line(line)
        if line_discipline and re.search(r'[IT]\d{2}-\d{3}', line):
            # This line has both discipline and invoice
            current_discipline = line_discipline

        # Extract invoice
        if current_project:
            invoice_data = extract_invoice_data(line)

            if invoice_data:
                phase = determine_phase(invoice_data['description'])

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

    # Write CSV
    fieldnames = [
        'project_code', 'project_name', 'invoice_number', 'invoice_date',
        'invoice_amount', 'payment_date', 'payment_amount', 'outstanding_amount',
        'phase', 'discipline', 'notes', 'status'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(invoices)

    # Generate comprehensive summary
    print(f"\n{'='*100}")
    print(f"COMPLETE INVOICE PARSING SUMMARY - ALL 26 PROJECTS (541 LINES)")
    print(f"{'='*100}\n")

    print(f"Total invoices parsed: {len(invoices)}")
    print(f"Output file: {output_file}\n")

    # By project
    project_data = {}
    for inv in invoices:
        code = inv['project_code']
        if code not in project_data:
            project_data[code] = {
                'name': inv['project_name'],
                'count': 0,
                'invoiced': 0.0,
                'paid': 0.0,
                'outstanding': 0.0
            }
        project_data[code]['count'] += 1
        project_data[code]['invoiced'] += inv['invoice_amount']
        project_data[code]['paid'] += inv['payment_amount']
        project_data[code]['outstanding'] += inv['outstanding_amount']

    print(f"{'Project':<10} {'Count':>7} {'Total Invoiced':>20} {'Paid':>20} {'Outstanding':>20}")
    print(f"{'-'*82}")

    for code in sorted(project_data.keys()):
        d = project_data[code]
        print(f"{code:<10} {d['count']:>7} ${d['invoiced']:>18,.2f} ${d['paid']:>18,.2f} ${d['outstanding']:>18,.2f}")

    print(f"{'-'*82}")
    total_inv = sum(d['invoiced'] for d in project_data.values())
    total_paid = sum(d['paid'] for d in project_data.values())
    total_out = sum(d['outstanding'] for d in project_data.values())
    print(f"{'TOTAL':<10} {len(invoices):>7} ${total_inv:>18,.2f} ${total_paid:>18,.2f} ${total_out:>18,.2f}\n")

    # Status
    status_counts = {'paid': 0, 'partial': 0, 'outstanding': 0}
    for inv in invoices:
        status_counts[inv['status']] += 1

    print(f"Status Breakdown:")
    for status in ['paid', 'partial', 'outstanding']:
        count = status_counts[status]
        pct = (count / len(invoices) * 100) if len(invoices) > 0 else 0
        print(f"  {status.capitalize():<15}: {count:>7} ({pct:>5.1f}%)")

    # Phase
    phase_counts = {}
    for inv in invoices:
        phase_counts[inv['phase']] = phase_counts.get(inv['phase'], 0) + 1

    print(f"\nPhase Breakdown:")
    for phase, count in sorted(phase_counts.items(), key=lambda x: -x[1])[:10]:
        pct = (count / len(invoices) * 100) if len(invoices) > 0 else 0
        print(f"  {phase:<30}: {count:>7} ({pct:>5.1f}%)")

    # Discipline
    discipline_counts = {}
    for inv in invoices:
        discipline_counts[inv['discipline']] = discipline_counts.get(inv['discipline'], 0) + 1

    print(f"\nDiscipline Breakdown:")
    for disc, count in sorted(discipline_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(invoices) * 100) if len(invoices) > 0 else 0
        print(f"  {disc:<30}: {count:>7} ({pct:>5.1f}%)")

    print(f"\n{'='*100}\n")

if __name__ == '__main__':
    main()
