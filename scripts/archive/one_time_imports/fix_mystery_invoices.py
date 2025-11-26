#!/usr/bin/env python3
"""
Fix the 6 mystery invoices - they're all from 24 BK-074
"""
import pandas as pd

# Read current CSV
df = pd.read_csv('reports/invoices_for_review.csv')

# The 6 mystery invoices that need fixing
mystery_invoices = {
    'I24-081': {
        'project_code': '24 BK-074',
        'project_name': 'Dang Thai Mai Project, Hanoi, Vietnam',
        'invoice_date': '2024-11-04',
        'invoice_amount': 294000.00,
        'payment_date': '2024-12-11',
        'payment_amount': 294000.00,
        'phase': 'Mobilization',
        'discipline': 'Interior Design',
        'status': 'paid',
        'needs_review': ''
    },
    'I25-007': {
        'project_code': '24 BK-074',
        'project_name': 'Dang Thai Mai Project, Hanoi, Vietnam',
        'invoice_date': '2025-01-20',
        'invoice_amount': 245000.00,
        'payment_date': '2025-09-01',
        'payment_amount': 245000.00,
        'phase': 'Conceptual Design',
        'discipline': 'Interior Design',
        'notes': '50% payment',
        'status': 'paid',
        'needs_review': ''
    },
    'I25-046': {
        'project_code': '24 BK-074',
        'project_name': 'Dang Thai Mai Project, Hanoi, Vietnam',
        'invoice_date': '2025-04-29',
        'invoice_amount': 245000.00,
        'payment_date': '2025-10-06',
        'payment_amount': 245000.00,
        'phase': 'Conceptual Design',
        'discipline': 'Interior Design',
        'notes': '50% payment - paid Oct 6 & 27',
        'status': 'paid',
        'needs_review': ''
    },
    'I25-082': {
        'project_code': '24 BK-074',
        'project_name': 'Dang Thai Mai Project, Hanoi, Vietnam',
        'invoice_date': '2025-08-14',
        'invoice_amount': 294000.00,
        'payment_date': '2025-10-27',
        'payment_amount': 200000.00,
        'phase': 'Design Development',
        'discipline': 'Interior Design',
        'notes': '50% payment - $94K still outstanding',
        'status': 'partial',
        'needs_review': ''
    },
    'I25-121': {
        'project_code': '24 BK-074',
        'project_name': 'Dang Thai Mai Project, Hanoi, Vietnam',
        'invoice_date': '2025-11-11',
        'invoice_amount': 294000.00,
        'payment_date': '',
        'payment_amount': 0.00,
        'phase': 'Design Development',
        'discipline': 'Interior Design',
        'notes': '50% payment',
        'status': 'outstanding',
        'needs_review': ''
    },
    'I25-099': {
        'project_code': '24 BK-074',
        'project_name': 'Dang Thai Mai Project, Hanoi, Vietnam',
        'invoice_date': '2025-10-01',
        'invoice_amount': 264600.00,  # 90% of $294K = $264,600
        'payment_date': '',
        'payment_amount': 0.00,
        'phase': 'Construction Documents',
        'discipline': 'Interior Design',
        'notes': '90% payment',
        'status': 'outstanding',
        'needs_review': ''
    }
}

# Update the mystery invoices
for invoice_num, data in mystery_invoices.items():
    mask = df['invoice_number'] == invoice_num
    if mask.any():
        for col, val in data.items():
            df.loc[mask, col] = val
        print(f"✅ Updated {invoice_num}: {data['phase']} - ${data['invoice_amount']:,.0f}")

# Save back to CSV
df.to_csv('reports/invoices_for_review.csv', index=False)

print("\n" + "="*80)
print("MYSTERY INVOICES FIXED!")
print("="*80)
print("\nAll 6 invoices assigned to: 24 BK-074 (Dang Thai Mai Project)")
print("\nUpdated CSV: reports/invoices_for_review.csv")
print("\nSummary:")
print("  - I24-081: Mobilization - $294,000 PAID")
print("  - I25-007: Conceptual Design 50% - $245,000 PAID")
print("  - I25-046: Conceptual Design 50% - $245,000 PAID")
print("  - I25-082: Design Development 50% - $294,000 ($200K paid, $94K outstanding)")
print("  - I25-121: Design Development 50% - $294,000 OUTSTANDING")
print("  - I25-099: Construction Documents 90% - $264,600 OUTSTANDING (CORRECTED!)")
print("\n" + "="*80)
