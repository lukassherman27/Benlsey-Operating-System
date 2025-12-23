#!/usr/bin/env python3
"""
Audit Invoice Links - Find orphaned and mislinked invoices
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv('DATABASE_PATH', './database/bensley_master.db')

def audit_invoices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("="*80)
    print("INVOICE DATA INTEGRITY AUDIT")
    print("="*80)

    # Get all invoices
    cursor.execute("""
        SELECT invoice_id, project_id, invoice_number, invoice_amount,
               payment_amount, status, description
        FROM invoices
    """)

    all_invoices = cursor.fetchall()
    print(f"\n📊 Total invoices: {len(all_invoices)}")

    # Check for orphaned invoices (project_id doesn't exist)
    print(f"\n{'='*80}")
    print("ORPHANED INVOICES (linked to non-existent projects)")
    print(f"{'='*80}")

    orphaned = []
    for inv in all_invoices:
        invoice_id, project_id, invoice_number, amount, paid, status, desc = inv

        if project_id:
            cursor.execute("SELECT proposal_id FROM proposals WHERE proposal_id = ?", (project_id,))
            if not cursor.fetchone():
                orphaned.append(inv)

    print(f"\n🚨 Found {len(orphaned)} orphaned invoices:")

    total_orphaned_value = 0
    for inv in orphaned:
        invoice_id, project_id, invoice_number, amount, paid, status, desc = inv
        total_orphaned_value += (paid or 0)
        print(f"\n  Invoice: {invoice_number}")
        print(f"    → Linked to: project_id {project_id} (DOESN'T EXIST)")
        print(f"    → Amount: ${amount:,.2f} | Paid: ${paid or 0:,.2f}")
        print(f"    → Status: {status}")
        print(f"    → Description: {desc or 'N/A'}")

    if orphaned:
        print(f"\n  💰 Total orphaned revenue: ${total_orphaned_value:,.2f}")

    # Check for NULL project_id
    print(f"\n{'='*80}")
    print("UNLINKED INVOICES (project_id is NULL)")
    print(f"{'='*80}")

    cursor.execute("""
        SELECT invoice_id, invoice_number, invoice_amount, payment_amount,
               status, description
        FROM invoices
        WHERE project_id IS NULL
    """)

    unlinked = cursor.fetchall()
    print(f"\n⚠️  Found {len(unlinked)} unlinked invoices:")

    total_unlinked_value = 0
    for inv in unlinked:
        invoice_id, invoice_number, amount, paid, status, desc = inv
        total_unlinked_value += (paid or 0)
        print(f"\n  Invoice: {invoice_number}")
        print(f"    → Amount: ${amount:,.2f} | Paid: ${paid or 0:,.2f}")
        print(f"    → Status: {status}")
        print(f"    → Description: {desc or 'N/A'}")

    if unlinked:
        print(f"\n  💰 Total unlinked revenue: ${total_unlinked_value:,.2f}")

    # Try to match orphaned invoices by invoice number pattern
    print(f"\n{'='*80}")
    print("SUGGESTED FIXES (matching by invoice number)")
    print(f"{'='*80}")

    fixes = []
    for inv in orphaned:
        invoice_id, project_id, invoice_number, amount, paid, status, desc = inv

        # Try to extract project code from invoice number (e.g., I24-017 → BK-017)
        import re
        match = re.search(r'I\d{2}-(\d{3})', invoice_number)
        if match:
            code_num = match.group(1)
            # Try both BK-XXX and 25BK-XXX formats
            cursor.execute("""
                SELECT proposal_id, project_code, project_name
                FROM proposals
                WHERE project_code IN (?, ?)
            """, (f'BK-{code_num}', f'25BK-{code_num}'))

            result = cursor.fetchone()
            if result:
                correct_proposal_id, project_code, project_name = result
                fixes.append({
                    'invoice_id': invoice_id,
                    'invoice_number': invoice_number,
                    'wrong_project_id': project_id,
                    'correct_project_id': correct_proposal_id,
                    'project_code': project_code,
                    'project_name': project_name,
                    'amount': amount,
                    'paid': paid
                })

    if fixes:
        print(f"\n✅ Found {len(fixes)} fixable invoices:")
        for fix in fixes:
            print(f"\n  Invoice: {fix['invoice_number']} (${fix['paid'] or 0:,.2f} paid)")
            print(f"    ❌ Currently: project_id {fix['wrong_project_id']} (doesn't exist)")
            print(f"    ✅ Should be: project_id {fix['correct_project_id']} ({fix['project_code']})")
            print(f"    📋 Project: {fix['project_name']}")

    # Summary
    print(f"\n{'='*80}")
    print("AUDIT SUMMARY")
    print(f"{'='*80}")
    print(f"Total invoices: {len(all_invoices)}")
    print(f"Orphaned (bad link): {len(orphaned)} (${total_orphaned_value:,.2f})")
    print(f"Unlinked (no link): {len(unlinked)} (${total_unlinked_value:,.2f})")
    print(f"Auto-fixable: {len(fixes)}")
    print(f"\n💸 Total broken revenue tracking: ${total_orphaned_value + total_unlinked_value:,.2f}")

    conn.close()

    return {
        'orphaned': orphaned,
        'unlinked': unlinked,
        'fixes': fixes
    }

if __name__ == '__main__':
    audit_invoices()
