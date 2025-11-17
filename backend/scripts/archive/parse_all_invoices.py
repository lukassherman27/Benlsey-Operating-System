#!/usr/bin/env python3
"""
Complete Invoice Parser for All 26 Projects
Extracts every invoice from FULL_INVOICE_DATA.txt with proper project codes, phases, disciplines, amounts, and dates.
"""

import re
import csv
from datetime import datetime
from typing import List, Dict, Optional, Tuple

def parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats to YYYY-MM-DD"""
    if not date_str or date_str.strip() == '0.00' or date_str.strip() == '':
        return None

    date_str = date_str.strip()

    # Handle "06 & 27 oct 2025" format
    if '&' in date_str:
        parts = date_str.split('&')
        date_str = parts[0].strip() + ' ' + ' '.join(date_str.split()[-2:])

    # Handle "Nov 26.20" format
    match = re.match(r'([A-Za-z]+)\s+(\d+)\.(\d+)', date_str)
    if match:
        month_str, day, year = match.groups()
        year = '20' + year
        try:
            date_obj = datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y")
            return date_obj.strftime("%Y-%m-%d")
        except:
            pass

    # Handle "8 &28 Jul 22" format
    if '&' in date_str or 'and' in date_str.lower():
        parts = re.split(r'[&]|and', date_str)
        date_str = parts[0].strip() + ' ' + ' '.join(date_str.split()[-2:])

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

    # Handle "3 Apr 24" format
    try:
        date_obj = datetime.strptime(date_str, "%d %b %y")
        return date_obj.strftime("%Y-%m-%d")
    except:
        pass

    # Handle "3 & 8 Jan 25" format - take first date
    if re.match(r'\d+\s*&\s*\d+\s+[A-Za-z]+\s+\d+', date_str):
        parts = date_str.split('&')
        date_str = parts[0].strip() + ' ' + ' '.join(date_str.split()[-2:])
        try:
            date_obj = datetime.strptime(date_str.strip(), "%d %b %y")
            return date_obj.strftime("%Y-%m-%d")
        except:
            pass

    return None

def parse_amount(amount_str: str) -> float:
    """Parse amount string to float"""
    if not amount_str or amount_str.strip() == '':
        return 0.0
    # Remove commas and convert
    return float(amount_str.replace(',', ''))

def determine_phase(description: str) -> str:
    """Determine phase from description"""
    desc_lower = description.lower()

    # Check for specific phases
    if 'mobilization' in desc_lower:
        return 'Mobilization Fee'
    elif 'conceptual design' in desc_lower or 'concept' in desc_lower:
        return 'Conceptual Design'
    elif 'design development' in desc_lower:
        return 'Design Development'
    elif 'construction document' in desc_lower:
        return 'Construction Documents'
    elif 'construction observation' in desc_lower:
        return 'Construction Observation'
    elif 'schematic design' in desc_lower:
        return 'Schematic Design'
    elif 'installment' in desc_lower:
        return 'Monthly Installment'
    elif 'monthly fee' in desc_lower:
        return 'Monthly Fee'
    elif 'additional service' in desc_lower:
        return 'Additional Service'
    elif 'mural' in desc_lower:
        return 'Mural'
    elif 'redesign' in desc_lower:
        return 'Redesign'
    elif 'branding' in desc_lower:
        return 'Branding Consultancy'

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

    # Track context for multi-line entries
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Parse line with numbered prefix (from cat -n format)
        match = re.match(r'\s*(\d+)→(.+)', line)
        if match:
            line_num, content = match.groups()
            content = content.strip()
        else:
            content = line

        # Check for project header: "Project No." line
        # Format: 1 20 BK-047 Sep-26 Audley Square House...
        project_match = re.match(r'^(\d+)\s+(\d{2}\s+BK-\d+)\s+([A-Za-z]+-\d+)\s+(.+)', content)
        if project_match:
            project_num, project_code, expiry, project_title = project_match.groups()
            current_project = project_code.replace(' ', '')  # "20 BK-047" -> "20BK-047"
            current_project_name = project_title.split('Mobilization')[0].strip()
            current_project_name = current_project_name.split('Conceptual')[0].strip()
            current_project_name = current_project_name.split('Design')[0].strip()
            current_project_name = current_project_name.split('1st')[0].strip()
            current_project_name = current_project_name.split('Monthly')[0].strip()
            current_discipline = None  # Reset discipline
            i += 1
            continue

        # Check for discipline markers
        if 'Landscape Architect' in content:
            current_discipline = 'Landscape Architectural'
            i += 1
            continue
        elif content.strip() in ['Architectural', 'Architectiral']:
            current_discipline = 'Architectural'
            i += 1
            continue
        elif 'Interior Design' in content:
            current_discipline = 'Interior Design'
            i += 1
            continue

        # Parse invoice lines
        # Look for invoice number pattern: I\d+-\d+ or T\d+-\d+
        invoice_match = re.search(r'([IT]\d{2}-\d{3}[A-Z]?(?:&[A-Z])?)', content)
        if invoice_match and current_project:
            invoice_number = invoice_match.group(1)

            # Extract components using pattern matching
            # Typical format: Description Amount Invoice# % Invoice_Date Outstanding Remaining Paid Date_Paid
            parts = content.split(invoice_number)
            before_invoice = parts[0].strip()
            after_invoice = parts[1].strip() if len(parts) > 1 else ''

            # Description is everything before the invoice number (excluding amounts)
            description = before_invoice

            # Remove trailing amounts from description
            desc_parts = description.split()
            clean_desc_parts = []
            for part in desc_parts:
                # Skip if it looks like an amount
                if re.match(r'[\d,]+\.?\d*', part.replace(',', '')):
                    # Check if it's a reasonable amount (> 1000)
                    try:
                        val = float(part.replace(',', ''))
                        if val > 1000:
                            break
                    except:
                        pass
                clean_desc_parts.append(part)

            description = ' '.join(clean_desc_parts).strip()

            # Extract percentage if present
            percent_match = re.search(r'(\d+)%', content)
            percent = percent_match.group(1) if percent_match else None

            # Extract dates and amounts from after_invoice section
            # Split by whitespace and parse
            tokens = after_invoice.split()

            invoice_date = None
            outstanding = 0.0
            remaining = 0.0
            paid = 0.0
            payment_date = None

            # Parse tokens
            j = 0
            while j < len(tokens):
                token = tokens[j]

                # Look for date patterns
                if re.match(r'[A-Za-z]+\s+\d+\.\d+', ' '.join(tokens[j:j+2])) and not invoice_date:
                    # This is invoice date
                    invoice_date = parse_date(' '.join(tokens[j:j+2]))
                    j += 2
                    continue

                # Look for amounts (numbers with commas)
                if re.match(r'[\d,]+\.\d{2}', token):
                    amount = parse_amount(token)
                    # First amount after invoice date is outstanding
                    if invoice_date and outstanding == 0.0:
                        outstanding = amount
                    elif remaining == 0.0:
                        remaining = amount
                    elif paid == 0.0:
                        paid = amount

                # Look for payment date at end
                if j > len(tokens) - 3:
                    potential_date = ' '.join(tokens[j:])
                    parsed = parse_date(potential_date)
                    if parsed and paid > 0:
                        payment_date = parsed
                        break

                j += 1

            # If we couldn't parse from tokens, try a different approach
            if not invoice_date:
                # Look for date pattern in full line
                date_patterns = [
                    r'([A-Za-z]+\s+\d+\.\d+)',
                    r'(\d+-[A-Za-z]+-\d+)',
                    r'(\d+\s+[A-Za-z]+\s+\d+)'
                ]
                for pattern in date_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        invoice_date = parse_date(matches[0])
                        if invoice_date:
                            break

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
                # Skip if no clear amounts
                i += 1
                continue

            # Determine phase
            phase = determine_phase(description)

            # Build notes
            notes = []
            if percent:
                notes.append(f"{percent}% payment")
            if 'Revised' in content:
                notes.append('Revised invoice')

            notes_str = '; '.join(notes) if notes else ''

            # Create invoice record
            invoice = {
                'project_code': current_project,
                'project_name': current_project_name or '',
                'invoice_number': invoice_number,
                'invoice_date': invoice_date or '',
                'invoice_amount': invoice_amount,
                'payment_date': payment_date or '',
                'payment_amount': payment_amount,
                'outstanding_amount': outstanding_amount,
                'phase': phase,
                'discipline': current_discipline or 'General',
                'notes': notes_str,
                'status': status
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
    print(f"INVOICE PARSING COMPLETE")
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

    print(f"{'Project Code':<15} {'Count':>8} {'Total Invoiced':>18} {'Paid':>18} {'Outstanding':>18}")
    print(f"{'-'*80}")

    for code in sorted(project_counts.keys()):
        print(f"{code:<15} {project_counts[code]:>8} "
              f"${project_totals[code]:>16,.2f} "
              f"${project_paid[code]:>16,.2f} "
              f"${project_outstanding[code]:>16,.2f}")

    print(f"{'-'*80}")
    total_invoiced = sum(project_totals.values())
    total_paid = sum(project_paid.values())
    total_outstanding = sum(project_outstanding.values())

    print(f"{'TOTAL':<15} {len(invoices):>8} "
          f"${total_invoiced:>16,.2f} "
          f"${total_paid:>16,.2f} "
          f"${total_outstanding:>16,.2f}\n")

    # Status breakdown
    status_counts = {}
    for inv in invoices:
        status_counts[inv['status']] = status_counts.get(inv['status'], 0) + 1

    print(f"Status breakdown:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status.capitalize()}: {count}")

    # Phase breakdown
    phase_counts = {}
    for inv in invoices:
        phase_counts[inv['phase']] = phase_counts.get(inv['phase'], 0) + 1

    print(f"\nPhase breakdown:")
    for phase, count in sorted(phase_counts.items(), key=lambda x: -x[1]):
        print(f"  {phase}: {count}")

    # Discipline breakdown
    discipline_counts = {}
    for inv in invoices:
        discipline_counts[inv['discipline']] = discipline_counts.get(inv['discipline'], 0) + 1

    print(f"\nDiscipline breakdown:")
    for disc, count in sorted(discipline_counts.items(), key=lambda x: -x[1]):
        print(f"  {disc}: {count}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
