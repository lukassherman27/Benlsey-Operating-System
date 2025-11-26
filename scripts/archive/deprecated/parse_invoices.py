#!/usr/bin/env python3
"""
Invoice Parser - Parses invoice data from text format to CSV
"""

import re
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class InvoiceParser:
    def __init__(self):
        self.invoices = []
        self.current_project_code = None
        self.current_project_name = None
        self.current_discipline = None
        self.current_phase = None
        self.issues = []

    def parse_date(self, date_str: str) -> str:
        """Convert various date formats to YYYY-MM-DD"""
        if not date_str or date_str.strip() == '0.00':
            return ''

        date_str = date_str.strip()

        # Handle multi-part dates like "06 & 27 oct 2025" or "01-11-2023 & 3 Apr 24"
        if '&' in date_str:
            date_str = date_str.split('&')[0].strip()

        # Handle dates like "8 &28 Jul 22" - take first part
        date_str = re.sub(r'\s*&\s*\d+\s*', ' ', date_str)

        # Format: "Nov 26.20" -> "2020-11-26"
        match = re.match(r'([A-Za-z]+)\s+(\d+)\.(\d+)', date_str)
        if match:
            month_str, day, year = match.groups()
            year = f"20{year}"
            try:
                month = datetime.strptime(month_str, '%b').month
                return f"{year}-{month:02d}-{int(day):02d}"
            except:
                self.issues.append(f"Failed to parse date: {date_str}")
                return ''

        # Format: "6-Oct-25" or "3-Nov-25"
        match = re.match(r'(\d+)-([A-Za-z]+)-(\d+)', date_str)
        if match:
            day, month_str, year = match.groups()
            year = f"20{year}"
            try:
                month = datetime.strptime(month_str, '%b').month
                return f"{year}-{month:02d}-{int(day):02d}"
            except:
                self.issues.append(f"Failed to parse date: {date_str}")
                return ''

        # Format: "01-11-2023"
        match = re.match(r'(\d{2})-(\d{2})-(\d{4})', date_str)
        if match:
            day, month, year = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"

        # Format: "8 Jul 22" or "28 Jul 22"
        match = re.match(r'(\d+)\s+([A-Za-z]+)\s+(\d+)', date_str)
        if match:
            day, month_str, year = match.groups()
            year = f"20{year}"
            try:
                month = datetime.strptime(month_str, '%b').month
                return f"{year}-{month:02d}-{int(day):02d}"
            except:
                self.issues.append(f"Failed to parse date: {date_str}")
                return ''

        self.issues.append(f"Unrecognized date format: {date_str}")
        return ''

    def parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float"""
        if not amount_str:
            return 0.0
        # Remove commas and convert to float
        return float(amount_str.replace(',', ''))

    def is_summary_row(self, parts: List[str]) -> bool:
        """Check if this is a summary/total row"""
        # Lines with only amounts (no invoice number) are usually totals
        if len(parts) < 3:
            return False

        # Check if first column is a large amount (likely a total)
        try:
            amount = self.parse_amount(parts[0])
            if amount > 50000 and not any(parts[1:3]):  # Large amount with no description
                return True
        except:
            pass

        return False

    def extract_project_header(self, line: str) -> Optional[Tuple[str, str]]:
        """Extract project code and name from header line"""
        # Format: "1 20 BK-047 Sep-26 Audley Square House-Communal Spa ..."
        # Number, ProjectCode, ExpiryDate, ProjectName, FirstPhase
        match = re.match(r'^\d+\s+(\d+\s+[A-Z]+-\d+)\s+\w+-\d+\s+(.+?)(?:\s+(?:Mobilization|25th|26th|27th|28th|29th|\d+st|\d+nd|\d+rd|\d+th)\s+|$)', line)
        if match:
            project_name = match.group(2).strip()
            # Clean up project name - remove trailing content
            project_name = re.sub(r'\s+(?:36|40|48)\s+month.*$', '', project_name)
            project_name = re.sub(r'\s+Total Fee.*$', '', project_name)
            return match.group(1), project_name

        # Format: "2 19 BK-018 Nov-23 Villa Project in Ahmedabad, India Mobilization"
        match = re.match(r'^(\d+)\s+(\d+\s+[A-Z]+-\d+)\s+\w+-\d+\s+(.+?)(?:\s+(?:Mobilization|Landscape|Architectural|Interior)\s+|$)', line)
        if match:
            project_name = match.group(3).strip()
            project_name = re.sub(r'\s+(?:36|40|48)\s+month.*$', '', project_name)
            return match.group(2), project_name

        # Format: "22 BK-013 Tel Aviv High Rise Project in Israel" (continuation line)
        match = re.match(r'^(\d+\s+[A-Z]+-\d+)\s+(.+?)(?:\s+(?:Design|Mobilization|Monthly)\s+|$)', line)
        if match:
            return match.group(1), match.group(2).strip()

        return None

    def extract_discipline(self, line: str) -> Optional[str]:
        """Extract discipline from line"""
        if 'Landscape Architectural' in line:
            return 'Landscape Architectural'
        elif 'Architectural' in line and 'Landscape' not in line:
            return 'Architectural'
        elif 'Interior Design' in line:
            return 'Interior Design'
        return None

    def extract_phase(self, description: str) -> str:
        """Extract phase from description"""
        description_lower = description.lower()

        if 'mobilization' in description_lower:
            return 'Mobilization Fee'
        elif 'conceptual design' in description_lower:
            return 'Conceptual Design'
        elif 'design development' in description_lower:
            return 'Design Development'
        elif 'construction documents' in description_lower:
            return 'Construction Documents'
        elif 'construction observation' in description_lower:
            return 'Construction Observation'
        elif 'installment' in description_lower:
            return 'Monthly Installment'
        elif any(month in description_lower for month in ['jan-', 'feb-', 'mar-', 'apr-', 'may-', 'jun-',
                                                            'jul-', 'aug-', 'sep-', 'oct-', 'nov-', 'dec-']):
            return 'Monthly Fee'

        return description

    def parse_invoice_line(self, line: str):
        """Parse a single invoice line"""
        # Skip empty lines and headers
        if not line.strip() or 'Project' in line or 'No.' in line:
            return

        # Check for project header
        project_info = self.extract_project_header(line)
        if project_info:
            self.current_project_code, self.current_project_name = project_info
            self.current_discipline = None
            return

        # Check for discipline
        discipline = self.extract_discipline(line)
        if discipline:
            self.current_discipline = discipline
            return

        # Skip remark lines and page footers
        if 'Remark' in line or 'Page' in line or 'Print on' in line:
            return

        # Parse invoice data
        # Expected format: Description Amount Invoice# % InvoiceDate Outstanding Remaining Paid DatePaid
        parts = line.split()

        if len(parts) < 3:
            return

        # Check for summary rows
        if self.is_summary_row(parts):
            return

        # Try to find invoice number
        invoice_num = None
        invoice_idx = -1
        for i, part in enumerate(parts):
            # Invoice numbers start with I, T, or contain numbers
            if re.match(r'[IT]\d+-\d+[A-Z]*|[IT]\d+-\d+', part):
                invoice_num = part
                invoice_idx = i
                break

        # If no invoice number, skip (could be a remaining installment)
        if not invoice_num:
            return

        # Build description from parts before invoice number
        description = ' '.join(parts[:invoice_idx]).strip()
        if not description:
            return

        # Extract phase from description
        phase = self.extract_phase(description)

        # Parse remaining fields after invoice number
        remaining_parts = parts[invoice_idx + 1:]

        try:
            # Find percentage if present
            percentage = ''
            pct_idx = -1
            for i, part in enumerate(remaining_parts):
                if part.endswith('%'):
                    percentage = part
                    pct_idx = i
                    break

            # Parse dates and amounts
            # Expected order after invoice#: [%] InvoiceDate Outstanding Remaining Paid DatePaid
            if pct_idx >= 0:
                # Has percentage
                date_start_idx = pct_idx + 1
            else:
                date_start_idx = 0

            # Try to find invoice date (should be first date-like value)
            invoice_date = ''
            amount_start_idx = date_start_idx

            for i in range(date_start_idx, min(date_start_idx + 3, len(remaining_parts))):
                if i < len(remaining_parts):
                    potential_date = ' '.join(remaining_parts[i:i+3])
                    parsed = self.parse_date(potential_date)
                    if parsed:
                        invoice_date = parsed
                        # Determine how many parts the date used
                        if re.match(r'[A-Za-z]+\s+\d+\.\d+', potential_date):
                            amount_start_idx = i + 2
                        else:
                            amount_start_idx = i + 1
                        break

            # Parse amounts: Outstanding, Remaining, Paid, DatePaid
            amounts = []
            for part in remaining_parts[amount_start_idx:]:
                if re.match(r'^\d+[\d,\.]*$', part):
                    amounts.append(self.parse_amount(part))
                elif re.match(r'^\d+-[A-Za-z]+-\d+$', part):
                    # This is the payment date
                    break

            # Assign amounts
            outstanding = amounts[0] if len(amounts) > 0 else 0.0
            remaining = amounts[1] if len(amounts) > 1 else 0.0
            paid = amounts[2] if len(amounts) > 2 else 0.0

            # Parse payment date (last date in line)
            payment_date = ''
            # Look for date pattern at the end
            date_match = re.search(r'(\d+-[A-Za-z]+-\d+|[A-Za-z]+\s+\d+\.\d+|\d+\s+[A-Za-z]+\s+\d+|\d+-\d+-\d+)\s*$', line)
            if date_match:
                payment_date = self.parse_date(date_match.group(1))

            # Determine status
            if paid > 0 and outstanding == 0:
                status = 'paid'
            elif outstanding > 0 and paid > 0:
                status = 'partial'
            elif outstanding > 0:
                status = 'outstanding'
            else:
                status = 'paid'

            # Determine invoice amount (paid if paid, otherwise outstanding)
            invoice_amount = paid if paid > 0 else outstanding

            # Create invoice record
            invoice = {
                'project_code': self.current_project_code or '',
                'project_name': self.current_project_name or '',
                'invoice_number': invoice_num,
                'invoice_date': invoice_date,
                'invoice_amount': invoice_amount,
                'payment_date': payment_date,
                'payment_amount': paid,
                'phase': phase,
                'discipline': self.current_discipline or '',
                'notes': percentage,
                'status': status
            }

            self.invoices.append(invoice)

        except Exception as e:
            self.issues.append(f"Error parsing line: {line[:50]}... - {str(e)}")

    def parse_file(self, filepath: str):
        """Parse the entire file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                self.parse_invoice_line(line)

    def write_csv(self, output_path: str):
        """Write invoices to CSV"""
        fieldnames = [
            'project_code', 'project_name', 'invoice_number', 'invoice_date',
            'invoice_amount', 'payment_date', 'payment_amount', 'phase',
            'discipline', 'notes', 'status'
        ]

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.invoices)

    def get_summary(self) -> Dict:
        """Generate summary statistics"""
        from collections import defaultdict

        project_counts = defaultdict(int)
        for inv in self.invoices:
            project_counts[inv['project_code']] += 1

        return {
            'total_invoices': len(self.invoices),
            'project_counts': dict(project_counts),
            'issues': self.issues
        }


def main():
    input_file = '/Users/lukassherman/Desktop/complete_invoice_data.txt'
    output_file = '/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/reports/invoices_parsed_complete.csv'

    parser = InvoiceParser()
    parser.parse_file(input_file)
    parser.write_csv(output_file)

    summary = parser.get_summary()

    print("=" * 70)
    print("INVOICE PARSING SUMMARY")
    print("=" * 70)
    print(f"\nTotal invoices parsed: {summary['total_invoices']}")
    print("\nInvoices by project:")
    for project, count in sorted(summary['project_counts'].items()):
        print(f"  {project}: {count} invoices")

    if summary['issues']:
        print(f"\nIssues encountered ({len(summary['issues'])}):")
        for issue in summary['issues'][:20]:  # Show first 20 issues
            print(f"  - {issue}")
        if len(summary['issues']) > 20:
            print(f"  ... and {len(summary['issues']) - 20} more issues")
    else:
        print("\nNo issues encountered!")

    print(f"\nOutput saved to: {output_file}")
    print("=" * 70)


if __name__ == '__main__':
    main()
