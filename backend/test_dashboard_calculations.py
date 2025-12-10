#!/usr/bin/env python3
"""
Test script to verify dashboard calculation fixes
"""
import sqlite3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "bensley_master.db")

def test_calculations():
    """Verify all dashboard calculations"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print("DASHBOARD CALCULATION VERIFICATION")
    print("=" * 80)

    # 1. Total contract value (active projects)
    cursor.execute("""
        SELECT COALESCE(SUM(total_fee_usd), 0) as total_contract_value
        FROM projects
        WHERE is_active_project = 1
    """)
    total_contract = cursor.fetchone()['total_contract_value']
    print(f"\n1. Total Contract Value (Active Projects): ${total_contract:,.2f}")

    # 2. Paid (active projects only)
    cursor.execute("""
        SELECT COALESCE(SUM(i.payment_amount), 0) as total_paid
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE p.is_active_project = 1
    """)
    paid_active = cursor.fetchone()['total_paid']
    print(f"2. Paid (Active Projects): ${paid_active:,.2f}")

    # Compare to ALL invoices paid (should be different)
    cursor.execute("""
        SELECT COALESCE(SUM(payment_amount), 0) as total_paid
        FROM invoices
    """)
    paid_all = cursor.fetchone()['total_paid']
    print(f"   - For comparison, ALL invoices paid: ${paid_all:,.2f}")
    print(f"   - Difference: ${abs(paid_all - paid_active):,.2f}")

    # 3. Outstanding (active projects)
    cursor.execute("""
        SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as outstanding
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE p.is_active_project = 1
        AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
    """)
    outstanding_active = cursor.fetchone()['outstanding']
    print(f"\n3. Outstanding (Active Projects): ${outstanding_active:,.2f}")

    # Compare to ALL outstanding
    cursor.execute("""
        SELECT COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0) as outstanding
        FROM invoices
        WHERE (invoice_amount - COALESCE(payment_amount, 0)) > 0
    """)
    outstanding_all = cursor.fetchone()['outstanding']
    print(f"   - For comparison, ALL outstanding: ${outstanding_all:,.2f}")
    print(f"   - Difference: ${abs(outstanding_all - outstanding_active):,.2f}")

    # 4. Remaining contract value calculation
    remaining = total_contract - paid_active - outstanding_active
    print(f"\n4. REMAINING CONTRACT VALUE CALCULATION:")
    print(f"   Total Contract:     ${total_contract:,.2f}")
    print(f"   - Paid:            (${paid_active:,.2f})")
    print(f"   - Outstanding:     (${outstanding_active:,.2f})")
    print(f"   = Remaining:        ${remaining:,.2f}")

    # 5. Overdue invoices (active projects)
    cursor.execute("""
        SELECT COUNT(*) as count,
               COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as amount
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE p.is_active_project = 1
        AND i.due_date < date('now')
        AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
    """)
    row = cursor.fetchone()
    overdue_count = row['count']
    overdue_amount = row['amount']
    print(f"\n5. Overdue Invoices (Active Projects):")
    print(f"   Count: {overdue_count}")
    print(f"   Amount: ${overdue_amount:,.2f}")

    # 6. Age buckets (active projects)
    print(f"\n6. Outstanding Invoice Age Buckets (Active Projects):")

    # 0-30 days
    cursor.execute("""
        SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as value
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE p.is_active_project = 1
        AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
        AND i.due_date >= date('now', '-30 days')
        AND i.due_date < date('now')
    """)
    bucket_0_30 = cursor.fetchone()['value']
    print(f"   0-30 days overdue:  ${bucket_0_30:,.2f}")

    # 30-60 days
    cursor.execute("""
        SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as value
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE p.is_active_project = 1
        AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
        AND i.due_date >= date('now', '-60 days')
        AND i.due_date < date('now', '-30 days')
    """)
    bucket_30_60 = cursor.fetchone()['value']
    print(f"   30-60 days overdue: ${bucket_30_60:,.2f}")

    # 60-90 days
    cursor.execute("""
        SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as value
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE p.is_active_project = 1
        AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
        AND i.due_date >= date('now', '-90 days')
        AND i.due_date < date('now', '-60 days')
    """)
    bucket_60_90 = cursor.fetchone()['value']
    print(f"   60-90 days overdue: ${bucket_60_90:,.2f}")

    # 90+ days
    cursor.execute("""
        SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as value
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE p.is_active_project = 1
        AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
        AND i.due_date < date('now', '-90 days')
    """)
    bucket_90_plus = cursor.fetchone()['value']
    print(f"   90+ days overdue:   ${bucket_90_plus:,.2f}")

    # Verify buckets add up to total overdue
    bucket_total = bucket_0_30 + bucket_30_60 + bucket_60_90 + bucket_90_plus
    print(f"\n   Total from buckets: ${bucket_total:,.2f}")
    print(f"   Total overdue:      ${overdue_amount:,.2f}")
    if abs(bucket_total - overdue_amount) < 0.01:
        print("   ✓ Buckets match total!")
    else:
        print(f"   ✗ MISMATCH: ${abs(bucket_total - overdue_amount):,.2f} difference")

    # 7. Active projects count
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM projects
        WHERE is_active_project = 1
    """)
    active_count = cursor.fetchone()['count']
    print(f"\n7. Active Projects Count: {active_count}")

    # 8. Sample invoice details
    print(f"\n8. Sample Invoice Details (first 5 active project invoices):")
    cursor.execute("""
        SELECT i.invoice_number, p.project_code, i.invoice_amount,
               COALESCE(i.payment_amount, 0) as payment_amount,
               (i.invoice_amount - COALESCE(i.payment_amount, 0)) as outstanding,
               i.due_date
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE p.is_active_project = 1
        AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
        ORDER BY i.invoice_date DESC
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(f"   {row['invoice_number']} ({row['project_code']}): ${row['outstanding']:,.2f} outstanding (due: {row['due_date']})")

    conn.close()

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_calculations()
