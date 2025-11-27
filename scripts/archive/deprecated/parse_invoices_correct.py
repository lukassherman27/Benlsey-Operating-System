#!/usr/bin/env python3
"""
Correct Invoice Parser - Fixed amount parsing
"""

import re
import csv
from datetime import datetime
from collections import defaultdict

class InvoiceParser:
    def __init__(self):
        self.invoices = []
        self.current_project_code = None
        self.current_project_name = None
        self.current_discipline = None
        self.issues = []

    def parse_date(self, date_str):
        """Convert various date formats to YYYY-MM-DD"""
        if not date_str or not date_str.strip() or date_str.strip() == '0.00':
            return ''

        date_str = date_str.strip()

        # Handle multi-part dates - take first date
        if '&' in date_str:
            date_str = date_str.split('&')[0].strip()

        # Format: "Nov 26.20"
        m = re.match(r'([A-Za-z]+)\s+(\d+)\.(\d+)', date_str)
        if m:
            try:
                month = datetime.strptime(m.group(1), '%b').month
                day = int(m.group(2))
                year = 2000 + int(m.group(3))
                return f"{year}-{month:02d}-{day:02d}"
            except:
                pass

        # Format: "6-Oct-25"
        m = re.match(r'(\d+)-([A-Za-z]+)-(\d+)', date_str)
        if m:
            try:
                day = int(m.group(1))
                month = datetime.strptime(m.group(2), '%b').month
                year = 2000 + int(m.group(3))
                return f"{year}-{month:02d}-{day:02d}"
            except:
                pass

        # Format: "01-11-2023"
        m = re.match(r'(\d{2})-(\d{2})-(\d{4})', date_str)
        if m:
            return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

        return ''

    def parse_amount(self, s):
        """Parse amount string"""
        if not s:
            return 0.0
        try:
            return float(s.replace(',', ''))
        except:
            return 0.0

    def is_project_header(self, line):
        """Check if line is a project header"""
        return re.match(r'^\d+\s+\d+\s+[A-Z]+-\d+\s+\w+-\d+\s+', line)

    def is_discipline_line(self, line):
        """Check if line indicates a discipline"""
        # Lines that start with duration and discipline
        if re.match(r'^\d+\s+month\s+(Landscape Architectural|Architectural|Interior Design)', line):
            return True
        # Standalone discipline headers
        if line.strip().startswith('Landscape Architectural'):
            return True
        if line.strip().startswith('Interior Design'):
            return True
        if line.strip().startswith('Architectural') and 'Landscape' not in line:
            return True
        return False

    def is_total_line(self, line):
        """Check if line is a total/summary"""
        parts = line.strip().split()
        if len(parts) < 4:
            return False
        # Total lines start with a large amount and have no invoice number
        try:
            amt = self.parse_amount(parts[0])
            if amt > 50000:
                # Check if there's an invoice number
                has_invoice = any(re.match(r'[IT]\d+-\d+', p) for p in parts[:5])
                return not has_invoice
        except:
            pass
        return False

    def parse_invoice_line(self, line):
        """Parse invoice line - CORRECT FORMAT PARSING"""
        # Look for invoice number
        inv_match = re.search(r'\b([IT]\d+-\d+[A-Z&]*)\b', line)
        if not inv_match:
            return None

        inv_num = inv_match.group(1)

        # Everything before invoice number contains: Description [Month] Amount
        before = line[:inv_match.start()].strip()

        # Everything after invoice number contains: [%] InvoiceDate Outstanding Remaining Paid PaymentDate
        after = line[inv_match.end():].strip()

        # Parse the "before" section
        # Need to extract description and amount
        # The amount is the LAST number before the invoice number
        # There may be a month name right before the amount

        before_parts = before.split()
        if not before_parts:
            return None

        # Find the last numeric value (the amount)
        amount = 0.0
        amount_idx = -1
        for i in range(len(before_parts) - 1, -1, -1):
            clean = before_parts[i].replace(',', '')
            if re.match(r'^\d+\.?\d*$', clean):
                amount = self.parse_amount(before_parts[i])
                amount_idx = i
                break

        # Everything before the amount (excluding possible month) is the description
        if amount_idx > 0:
            # Check if the part before amount is a month name
            month_idx = amount_idx - 1
            if month_idx >= 0 and re.match(r'^[A-Za-z]{3,4}$', before_parts[month_idx]):
                # It's a month, skip it
                description = ' '.join(before_parts[:month_idx])
            else:
                description = ' '.join(before_parts[:amount_idx])
        else:
            description = ''

        # Determine phase from description
        desc_lower = description.lower()
        if 'mobilization' in desc_lower:
            phase = 'Mobilization Fee'
        elif 'conceptual design' in desc_lower:
            phase = 'Conceptual Design'
        elif 'design development' in desc_lower:
            phase = 'Design Development'
        elif 'construction documents' in desc_lower:
            phase = 'Construction Documents'
        elif 'construction observation' in desc_lower:
            phase = 'Construction Observation'
        elif re.search(r'\d+(?:st|nd|rd|th)\s+installment', desc_lower):
            phase = 'Monthly Installment'
        elif re.search(r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)-\d+', desc_lower):
            phase = 'Monthly Fee'
        else:
            phase = description if description else 'Unknown'

        # Parse the "after" section
        after_parts = after.split()

        pct = ''
        idx = 0

        # Check for percentage
        if idx < len(after_parts) and after_parts[idx].endswith('%'):
            pct = after_parts[idx]
            idx += 1

        # Parse invoice date (could be multi-part like "Aug 26.25")
        inv_date = ''
        if idx < len(after_parts):
            for n in [3, 2, 1]:
                if idx + n <= len(after_parts):
                    candidate = ' '.join(after_parts[idx:idx+n])
                    parsed = self.parse_date(candidate)
                    if parsed:
                        inv_date = parsed
                        idx += n
                        break

        # Now parse amounts: Outstanding Remaining Paid
        amounts = []
        amount_count = 0
        while idx < len(after_parts) and amount_count < 3:
            p = after_parts[idx]
            if re.match(r'^\d+[,\.\d]*$', p):
                amounts.append(self.parse_amount(p))
                idx += 1
                amount_count += 1
            else:
                # Hit non-amount (likely payment date)
                break

        outstanding = amounts[0] if len(amounts) > 0 else 0.0
        remaining = amounts[1] if len(amounts) > 1 else 0.0
        paid = amounts[2] if len(amounts) > 2 else 0.0

        # Parse payment date from remaining parts
        pay_date = ''
        if idx < len(after_parts):
            pay_date_str = ' '.join(after_parts[idx:])
            pay_date = self.parse_date(pay_date_str)

        # Determine status
        if paid > 0 and outstanding == 0:
            status = 'paid'
        elif outstanding > 0 and paid > 0:
            status = 'partial'
        elif outstanding > 0:
            status = 'outstanding'
        else:
            status = 'paid' if paid > 0 else 'outstanding'

        # Invoice amount: use paid if paid, otherwise outstanding
        inv_amount = paid if paid > 0 else outstanding

        return {
            'project_code': self.current_project_code or '',
            'project_name': self.current_project_name or '',
            'invoice_number': inv_num,
            'invoice_date': inv_date,
            'invoice_amount': inv_amount,
            'payment_date': pay_date,
            'payment_amount': paid,
            'phase': phase,
            'discipline': self.current_discipline or '',
            'notes': pct,
            'status': status
        }

    def parse_file(self, filepath):
        """Parse the entire file"""
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip empty, headers, footers
                if not line or 'Project Expiry' in line or line.startswith('No.') or \
                   'Page' in line or 'Print on' in line or 'Remark' in line:
                    continue

                # Check for project header
                if self.is_project_header(line):
                    m = re.match(r'^\d+\s+(\d+\s+[A-Z]+-\d+)\s+\w+-\d+\s+(.+)', line)
                    if m:
                        self.current_project_code = m.group(1)
                        name = m.group(2)
                        # Clean project name - remove phase/discipline keywords
                        name = re.split(r'\s+(?:Mobilization|Conceptual|Design|Construction|\d+(?:st|nd|rd|th)\s+installment)', name)[0]
                        name = re.split(r'\s+\d+\s+month', name)[0]
                        name = re.split(r'\s+Total Fee', name)[0]
                        self.current_project_name = name.strip()
                        self.current_discipline = None
                    continue

                # Check for discipline
                if self.is_discipline_line(line):
                    if 'Landscape Architectural' in line:
                        self.current_discipline = 'Landscape Architectural'
                    elif 'Interior Design' in line:
                        self.current_discipline = 'Interior Design'
                    elif 'Architectural' in line:
                        self.current_discipline = 'Architectural'
                    continue

                # Skip total lines
                if self.is_total_line(line):
                    continue

                # Parse invoice
                inv = self.parse_invoice_line(line)
                if inv:
                    self.invoices.append(inv)

    def write_csv(self, output_path):
        """Write to CSV"""
        fields = ['project_code', 'project_name', 'invoice_number', 'invoice_date',
                  'invoice_amount', 'payment_date', 'payment_amount', 'phase',
                  'discipline', 'notes', 'status']

        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.invoices)

    def summary(self):
        """Generate summary"""
        counts = defaultdict(int)
        for inv in self.invoices:
            counts[inv['project_code']] += 1

        print("=" * 70)
        print("INVOICE PARSING SUMMARY")
        print("=" * 70)
        print(f"\nTotal invoices parsed: {len(self.invoices)}")
        print(f"Unique projects: {len(counts)}")
        print("\nInvoices by project:")
        for proj, count in sorted(counts.items()):
            name = next((i['project_name'] for i in self.invoices if i['project_code'] == proj), '')
            print(f"  {proj} - {name}: {count} invoices")

        if self.issues:
            print(f"\nIssues: {len(self.issues)}")
            for issue in self.issues[:10]:
                print(f"  - {issue}")
        else:
            print("\nNo issues encountered!")
        print("=" * 70)


if __name__ == '__main__':
    parser = InvoiceParser()
    parser.parse_file('/Users/lukassherman/Desktop/complete_invoice_data.txt')
    parser.write_csv('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/reports/invoices_parsed_complete.csv')
    parser.summary()
