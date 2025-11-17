#!/usr/bin/env python3
"""
Final Complete Invoice Parser for All 26 Projects
Correctly parses the tab/space-delimited invoice data with proper column alignment.
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
        # Get first number and month+year from end
        if len(parts) > 0 and parts[0].strip():
            first_part = parts[0].strip().split()
            if len(first_part) > 0:
                first_num = first_part[0]
                date_parts = date_str.split()
                if len(date_parts) >= 2:
                    month_year = ' '.join(date_parts[-2:])
                    date_str = f"{first_num} {month_year}"

    # Handle "Nov 26.20" format (most common in invoice dates)
    match = re.match(r'([A-Za-z]+)\s+(\d+)\.(\d+)', date_str)
    if match:
        month_str, day, year = match.groups()
        year = '20' + year
        try:
            date_obj = datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y")
            return date_obj.strftime("%Y-%m-%d")
        except:
            pass

    # Handle "6-Oct-25" or "7-Jan-21" format
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

    # Handle "3 Apr 24" format
    try:
        date_obj = datetime.strptime(date_str, "%d %b %y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        pass

    # Handle "23-Mar-21" format
    for fmt in ["%d-%b-%y", "%d-%b-%Y"]:
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
    # Remove commas and convert
    try:
        cleaned = amount_str.replace(',', '').strip()
        return float(cleaned)
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
    elif 'monthly fee' in desc_lower or 'month ' in desc_lower:
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
    # Lines with totals or no invoice number
    if not re.search(r'[IT]\d{2}-\d{3}', line):
        # Check if it's just amounts (summary line)
        amount_count = len(re.findall(r'\d{1,3}(?:,\d{3})*\.\d{2}', line))
        if amount_count >= 3 and amount_count <= 5:
            return True
    return False

def extract_invoice_from_line(line: str) -> Optional[Dict]:
    """Extract invoice data from a single line"""
    # Check for invoice number
    inv_match = re.search(r'([IT]\d{2}-\d{3}[A-Z]?(?:&[A-Z])?)', line)
    if not inv_match:
        return None

    invoice_num = inv_match.group(1)

    # Split the line into parts
    # Format: Description Amount Invoice# [%] Invoice_Date Outstanding Remaining Paid Date_Paid

    # Find invoice number position
    inv_pos = line.index(invoice_num)

    # Everything before invoice number is description + amount
    before_invoice = line[:inv_pos].strip()
    after_invoice = line[inv_pos + len(invoice_num):].strip()

    # Description is the text part before the last amount in before_invoice
    # Find all amounts in before_invoice
    amounts_before = re.findall(r'([\d,]+\.\d{2})', before_invoice)

    # Description is everything before the last amount
    if amounts_before:
        last_amount_pos = before_invoice.rfind(amounts_before[-1])
        description = before_invoice[:last_amount_pos].strip()
    else:
        description = before_invoice.strip()

    # Extract percentage if present
    percent_match = re.search(r'(\d+)%', after_invoice)
    percent = percent_match.group(1) if percent_match else None

    # Remove percentage from after_invoice for easier parsing
    if percent:
        after_invoice = after_invoice.replace(f'{percent}%', '', 1).strip()

    # Split after_invoice into tokens
    tokens = after_invoice.split()

    # Parse dates and amounts
    # Expected order: [invoice_date] outstanding remaining paid [payment_date]
    invoice_date = None
    outstanding = 0.0
    remaining = 0.0
    paid = 0.0
    payment_date = None

    i = 0
    found_amounts = []

    while i < len(tokens):
        token = tokens[i]

        # Check if this could be a date
        # Look ahead for date patterns
        potential_date = None

        # "Nov 26.20" pattern (2-3 tokens)
        if i + 1 < len(tokens):
            potential_date = parse_date(f"{token} {tokens[i+1]}")
            if potential_date:
                if not invoice_date:
                    invoice_date = potential_date
                    i += 2
                    continue
                else:
                    payment_date = potential_date
                    i += 2
                    continue

        # "6-Oct-25" pattern (single token)
        potential_date = parse_date(token)
        if potential_date and '-' in token:
            if not invoice_date:
                invoice_date = potential_date
                i += 1
                continue
            else:
                payment_date = potential_date
                i += 1
                continue

        # Check if this is an amount
        if re.match(r'[\d,]+\.\d{2}$', token):
            found_amounts.append(parse_amount(token))

        i += 1

    # Assign amounts: outstanding, remaining, paid
    if len(found_amounts) >= 1:
        outstanding = found_amounts[0]
    if len(found_amounts) >= 2:
        remaining = found_amounts[1]
    if len(found_amounts) >= 3:
        paid = found_amounts[2]

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
    elif remaining > 0 and outstanding == 0 and paid == 0:
        # No invoice yet - skip
        return None
    else:
        # Skip if no valid amounts
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

        # Skip empty lines and headers
        if not line or 'Project Expiry' in line or 'Page' in line or 'Print on' in line:
            continue

        # Skip summary lines
        if is_summary_line(line):
            continue

        # Check for project header
        # Format: "1 20 BK-047 Sep-26 Audley Square House..."
        project_match = re.match(r'^(\d+)\s+(\d{2}\s+BK-\d+)\s+([A-Za-z]+-\d+)\s+(.+)', line)
        if project_match:
            project_num, project_code, expiry, rest = project_match.groups()
            current_project = project_code.replace(' ', '')

            # Extract project name
            project_name = rest
            # Clean up project name (remove phase keywords)
            for keyword in ['Mobilization Fee', 'Conceptual Design', 'Design Development',
                           'Construction Documents', 'Construction Observation',
                           '1st installment', '2nd installment', 'Monthly Fee', 'Package']:
                if keyword in project_name:
                    project_name = project_name.split(keyword)[0].strip()

            current_project_name = project_name
            current_discipline = None
            continue

        # Check for discipline markers (standalone lines)
        if re.match(r'^Landscape Architect', line, re.IGNORECASE) and len(line) < 40:
            current_discipline = 'Landscape Architectural'
            continue
        elif re.match(r'^Architect(iral|ural)\s*$', line, re.IGNORECASE):
            current_discipline = 'Architectural'
            continue
        elif re.match(r'^Interior Design\s*$', line, re.IGNORECASE):
            current_discipline = 'Interior Design'
            continue

        # Try to extract invoice
        if current_project:
            invoice_data = extract_invoice_from_line(line)

            if invoice_data:
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
    print(f"\n{'='*90}")
    print(f"COMPLETE INVOICE PARSING SUMMARY - ALL 26 PROJECTS")
    print(f"{'='*90}\n")

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

    print(f"{'Project Code':<15} {'Count':>7} {'Total Invoiced':>20} {'Paid':>20} {'Outstanding':>20}")
    print(f"{'-'*90}")

    for code in sorted(project_counts.keys()):
        print(f"{code:<15} {project_counts[code]:>7} "
              f"${project_totals[code]:>18,.2f} "
              f"${project_paid[code]:>18,.2f} "
              f"${project_outstanding[code]:>18,.2f}")

    print(f"{'-'*90}")
    total_invoiced = sum(project_totals.values())
    total_paid = sum(project_paid.values())
    total_outstanding = sum(project_outstanding.values())

    print(f"{'GRAND TOTAL':<15} {len(invoices):>7} "
          f"${total_invoiced:>18,.2f} "
          f"${total_paid:>18,.2f} "
          f"${total_outstanding:>18,.2f}\n")

    # Status breakdown
    status_counts = {'paid': 0, 'partial': 0, 'outstanding': 0}
    for inv in invoices:
        status_counts[inv['status']] = status_counts.get(inv['status'], 0) + 1

    print(f"Invoice Status Breakdown:")
    print(f"{'-'*50}")
    for status in ['paid', 'partial', 'outstanding']:
        count = status_counts[status]
        pct = (count / len(invoices) * 100) if len(invoices) > 0 else 0
        print(f"  {status.capitalize():<20}: {count:>7} ({pct:>5.1f}%)")

    # Phase breakdown
    phase_counts = {}
    for inv in invoices:
        phase_counts[inv['phase']] = phase_counts.get(inv['phase'], 0) + 1

    print(f"\nInvoice Phase Breakdown:")
    print(f"{'-'*50}")
    for phase, count in sorted(phase_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(invoices) * 100) if len(invoices) > 0 else 0
        print(f"  {phase:<30}: {count:>7} ({pct:>5.1f}%)")

    # Discipline breakdown
    discipline_counts = {}
    for inv in invoices:
        discipline_counts[inv['discipline']] = discipline_counts.get(inv['discipline'], 0) + 1

    print(f"\nInvoice Discipline Breakdown:")
    print(f"{'-'*50}")
    for disc, count in sorted(discipline_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(invoices) * 100) if len(invoices) > 0 else 0
        print(f"  {disc:<30}: {count:>7} ({pct:>5.1f}%)")

    print(f"\n{'='*90}\n")

    # Identify parsing issues
    issues = []
    for inv in invoices:
        if not inv['invoice_date']:
            issues.append(f"Missing invoice date: {inv['invoice_number']} - {inv['project_code']}")
        if inv['status'] == 'paid' and not inv['payment_date']:
            issues.append(f"Paid invoice missing payment date: {inv['invoice_number']} - {inv['project_code']}")

    if issues:
        print(f"POTENTIAL PARSING ISSUES ({len(issues)}):")
        print(f"{'-'*50}")
        for issue in issues[:15]:
            print(f"  - {issue}")
        if len(issues) > 15:
            print(f"  ... and {len(issues)-15} more")
        print()

    # Show sample of parsed invoices
    print(f"SAMPLE PARSED INVOICES (first 10):")
    print(f"{'-'*50}")
    for i, inv in enumerate(invoices[:10]):
        print(f"\n{i+1}. {inv['invoice_number']} - {inv['project_code']}")
        print(f"   Project: {inv['project_name']}")
        print(f"   Phase: {inv['phase']} | Discipline: {inv['discipline']}")
        print(f"   Invoice Amount: ${inv['invoice_amount']:,.2f} | Paid: ${inv['payment_amount']:,.2f} | Outstanding: ${inv['outstanding_amount']:,.2f}")
        print(f"   Invoice Date: {inv['invoice_date']} | Payment Date: {inv['payment_date']} | Status: {inv['status']}")

    print(f"\n{'='*90}\n")

if __name__ == '__main__':
    main()
