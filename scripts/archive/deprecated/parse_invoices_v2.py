#!/usr/bin/env python3
"""
Comprehensive invoice parser - handles all the complex cases in the invoice data
"""
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

def parse_date(date_str: str) -> Optional[str]:
    """Convert date formats like 'Nov 26.20', 'Aug 26.25' to YYYY-MM-DD"""
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()
    if date_str == '0.00' or date_str == '':
        return None

    # Handle "06 & 27 oct 2025" format
    if '&' in date_str:
        date_str = date_str.split('&')[0].strip()

    month_map = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }

    # Pattern: "Nov 26.20" or "Sep26" or "Nov-25"
    for month_name, month_num in month_map.items():
        if month_name.lower() in date_str.lower():
            parts = re.findall(r'\d+', date_str)
            if len(parts) >= 2:
                day = parts[0].zfill(2)
                year_short = parts[1]
                # If year is 2 digits, add 20 prefix
                if len(year_short) == 2:
                    year = f"20{year_short}"
                else:
                    year = year_short
                return f"{year}-{month_num}-{day}"

    # Try full date formats like "01-11-2023"
    if '-' in date_str:
        parts = date_str.split('-')
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year = f"20{year}"
            if len(year) == 4:
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    return None

# Read the pasted data
data_text = """Project Expiry Project Title Description Amount Invoice # % Invoice Outstanding Remaining Paid Date paid
No. Date US.$ Date US.$ US.$ US.$
[DATA CONTINUES AS USER PASTED]
"""

# Actually, let's read from the file we saved
with open('/Users/lukassherman/Desktop/complete_invoice_data.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

invoices_list = []

# Manual parsing - go through each known invoice from the data
# This is more reliable than trying to parse the complex format programmatically

# Project 1: 20 BK-047 - Audley Square House
invoices_list.extend([
    {'project_code': '20 BK-047', 'project_name': 'Audley Square House-Communal Spa', 'invoice_number': 'I25-087', 'invoice_date': '2025-08-26', 'invoice_amount': 8000, 'payment_date': '2025-10-06', 'payment_amount': 8000, 'phase': 'Monthly Installment', 'discipline': '', 'notes': '25th installment', 'status': 'paid'},
    {'project_code': '20 BK-047', 'project_name': 'Audley Square House-Communal Spa', 'invoice_number': 'I25-102', 'invoice_date': '2025-10-10', 'invoice_amount': 8000, 'payment_date': '2025-11-03', 'payment_amount': 8000, 'phase': 'Monthly Installment', 'discipline': '', 'notes': '26th installment', 'status': 'paid'},
    {'project_code': '20 BK-047', 'project_name': 'Audley Square House-Communal Spa', 'invoice_number': 'I25-103', 'invoice_date': '2025-10-10', 'invoice_amount': 8000, 'payment_date': '2025-11-03', 'payment_amount': 8000, 'phase': 'Monthly Installment', 'discipline': '', 'notes': '27th installment', 'status': 'paid'},
    {'project_code': '20 BK-047', 'project_name': 'Audley Square House-Communal Spa', 'invoice_number': 'I25-116', 'invoice_date': '2025-11-10', 'invoice_amount': 8000, 'payment_date': None, 'payment_amount': 0, 'phase': 'Monthly Installment', 'discipline': '', 'notes': '28th installment', 'status': 'outstanding'},
])

# Project 2: 19 BK-018 - Villa Project in Ahmedabad - Landscape
invoices_list.extend([
    {'project_code': '19 BK-018', 'project_name': 'Villa Project in Ahmedabad, India', 'invoice_number': 'I20-096', 'invoice_date': '2020-11-26', 'invoice_amount': 71250, 'payment_date': '2021-01-07', 'payment_amount': 71250, 'phase': 'Mobilization', 'discipline': 'Landscape Architectural', 'notes': '', 'status': 'paid'},
    {'project_code': '19 BK-018', 'project_name': 'Villa Project in Ahmedabad, India', 'invoice_number': 'I21-020', 'invoice_date': '2021-03-08', 'invoice_amount': 118750, 'payment_date': '2021-03-23', 'payment_amount': 118750, 'phase': 'Conceptual Design', 'discipline': 'Landscape Architectural', 'notes': '', 'status': 'paid'},
    {'project_code': '19 BK-018', 'project_name': 'Villa Project in Ahmedabad, India', 'invoice_number': 'I21-067', 'invoice_date': '2021-09-06', 'invoice_amount': 71250, 'payment_date': '2021-10-12', 'payment_amount': 71250, 'phase': 'Design Development', 'discipline': 'Landscape Architectural', 'notes': '50%', 'status': 'paid'},
    {'project_code': '19 BK-018', 'project_name': 'Villa Project in Ahmedabad, India', 'invoice_number': 'I22-006', 'invoice_date': '2022-02-12', 'invoice_amount': 71250, 'payment_date': '2022-03-11', 'payment_amount': 71250, 'phase': 'Design Development', 'discipline': 'Landscape Architectural', 'notes': '50%', 'status': 'paid'},
    {'project_code': '19 BK-018', 'project_name': 'Villa Project in Ahmedabad, India', 'invoice_number': 'I22-042', 'invoice_date': '2022-05-23', 'invoice_amount': 71250, 'payment_date': '2022-06-09', 'payment_amount': 71250, 'phase': 'Construction Documents', 'discipline': 'Landscape Architectural', 'notes': '100%', 'status': 'paid'},
    {'project_code': '19 BK-018', 'project_name': 'Villa Project in Ahmedabad, India', 'invoice_number': 'I23-001', 'invoice_date': '2023-01-10', 'invoice_amount': 17812.50, 'payment_date': '2023-03-27', 'payment_amount': 17812.50, 'phase': 'Construction Observation', 'discipline': 'Landscape Architectural', 'notes': '25%', 'status': 'paid'},
    {'project_code': '19 BK-018', 'project_name': 'Villa Project in Ahmedabad, India', 'invoice_number': 'I24-064', 'invoice_date': '2024-08-26', 'invoice_amount': 17812.50, 'payment_date': '2024-09-19', 'payment_amount': 17812.50, 'phase': 'Construction Observation', 'discipline': 'Landscape Architectural', 'notes': '25%', 'status': 'paid'},
    {'project_code': '19 BK-018', 'project_name': 'Villa Project in Ahmedabad, India', 'invoice_number': 'I24-073', 'invoice_date': '2024-10-01', 'invoice_amount': 35625, 'payment_date': None, 'payment_amount': 0, 'phase': 'Construction Observation', 'discipline': 'Landscape Architectural', 'notes': '50% - Outstanding', 'status': 'outstanding'},
])

# Continue for remaining projects...
# This would be very long, so let me use a hybrid approach

print("This manual approach will take too long...")
print("Let me use the Excel file the user originally had instead")
