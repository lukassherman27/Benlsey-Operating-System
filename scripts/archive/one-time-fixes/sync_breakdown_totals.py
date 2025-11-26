#!/usr/bin/env python3
"""
Sync Breakdown Totals Script
=============================
Synchronizes invoice totals from invoices table to project_fee_breakdown table.

This script:
1. Calculates total_invoiced and total_paid for each breakdown_id
2. Updates project_fee_breakdown table with calculated totals
3. Calculates percentage_invoiced and percentage_paid
4. Creates database triggers for auto-updates on future invoice changes

Usage:
    python3 sync_breakdown_totals.py [--dry-run]
"""

import sqlite3
import os
import sys
from datetime import datetime

DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

def get_connection():
    """Get database connection"""
    if not os.path.exists(DATABASE_PATH):
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")
    return sqlite3.connect(DATABASE_PATH)

def get_invoice_totals(cursor):
    """
    Calculate invoice totals grouped by breakdown_id
    Returns dict: {breakdown_id: (total_invoiced, total_paid)}
    """
    cursor.execute("""
        SELECT
            breakdown_id,
            SUM(COALESCE(invoice_amount, 0)) as total_invoiced,
            SUM(COALESCE(payment_amount, 0)) as total_paid,
            COUNT(*) as invoice_count
        FROM invoices
        WHERE breakdown_id IS NOT NULL
        GROUP BY breakdown_id
        ORDER BY breakdown_id
    """)

    results = {}
    for row in cursor.fetchall():
        breakdown_id, total_invoiced, total_paid, invoice_count = row
        results[breakdown_id] = {
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'invoice_count': invoice_count
        }

    return results

def get_breakdown_records(cursor):
    """
    Get all breakdown records with current totals
    Returns dict: {breakdown_id: {phase_fee_usd, total_invoiced, total_paid}}
    """
    cursor.execute("""
        SELECT
            breakdown_id,
            phase_fee_usd,
            total_invoiced,
            total_paid,
            percentage_invoiced,
            percentage_paid
        FROM project_fee_breakdown
        ORDER BY breakdown_id
    """)

    results = {}
    for row in cursor.fetchall():
        breakdown_id, phase_fee, total_inv, total_paid, pct_inv, pct_paid = row
        results[breakdown_id] = {
            'phase_fee_usd': phase_fee or 0,
            'total_invoiced': total_inv or 0,
            'total_paid': total_paid or 0,
            'percentage_invoiced': pct_inv or 0,
            'percentage_paid': pct_paid or 0
        }

    return results

def calculate_percentages(total, phase_fee):
    """Calculate percentage, handling division by zero"""
    if phase_fee and phase_fee > 0:
        return round((total / phase_fee) * 100, 1)
    return 0.0

def sync_breakdown_totals(dry_run=False):
    """
    Main sync function
    """
    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n{'='*80}")
    print(f"Breakdown Totals Sync - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DATABASE_PATH}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print(f"{'='*80}\n")

    # Get invoice totals grouped by breakdown_id
    print("Step 1: Calculating invoice totals...")
    invoice_totals = get_invoice_totals(cursor)
    print(f"  ✓ Found {len(invoice_totals)} breakdown_ids with invoices")

    # Get current breakdown records
    print("\nStep 2: Loading breakdown records...")
    breakdown_records = get_breakdown_records(cursor)
    print(f"  ✓ Found {len(breakdown_records)} breakdown records")

    # Calculate updates needed
    print("\nStep 3: Calculating updates...")
    updates_needed = []

    for breakdown_id, invoice_data in invoice_totals.items():
        if breakdown_id not in breakdown_records:
            print(f"  ⚠️  WARNING: Orphaned breakdown_id in invoices: {breakdown_id}")
            continue

        breakdown = breakdown_records[breakdown_id]
        phase_fee = breakdown['phase_fee_usd']

        new_total_invoiced = invoice_data['total_invoiced']
        new_total_paid = invoice_data['total_paid']
        new_pct_invoiced = calculate_percentages(new_total_invoiced, phase_fee)
        new_pct_paid = calculate_percentages(new_total_paid, phase_fee)

        # Check if update needed
        if (breakdown['total_invoiced'] != new_total_invoiced or
            breakdown['total_paid'] != new_total_paid or
            breakdown['percentage_invoiced'] != new_pct_invoiced or
            breakdown['percentage_paid'] != new_pct_paid):

            updates_needed.append({
                'breakdown_id': breakdown_id,
                'invoice_count': invoice_data['invoice_count'],
                'old': {
                    'total_invoiced': breakdown['total_invoiced'],
                    'total_paid': breakdown['total_paid'],
                    'pct_invoiced': breakdown['percentage_invoiced'],
                    'pct_paid': breakdown['percentage_paid']
                },
                'new': {
                    'total_invoiced': new_total_invoiced,
                    'total_paid': new_total_paid,
                    'pct_invoiced': new_pct_invoiced,
                    'pct_paid': new_pct_paid
                },
                'phase_fee': phase_fee
            })

    print(f"  ✓ Found {len(updates_needed)} breakdowns requiring updates")

    # Display sample updates
    if updates_needed:
        print(f"\n  Sample Updates (showing first 5):")
        for update in updates_needed[:5]:
            print(f"\n    {update['breakdown_id']}")
            print(f"      Phase Fee: ${update['phase_fee']:,.2f}")
            print(f"      Invoices: {update['invoice_count']}")
            print(f"      Total Invoiced: ${update['old']['total_invoiced']:,.2f} → ${update['new']['total_invoiced']:,.2f}")
            print(f"      Total Paid: ${update['old']['total_paid']:,.2f} → ${update['new']['total_paid']:,.2f}")
            print(f"      % Invoiced: {update['old']['pct_invoiced']:.1f}% → {update['new']['pct_invoiced']:.1f}%")
            print(f"      % Paid: {update['old']['pct_paid']:.1f}% → {update['new']['pct_paid']:.1f}%")

    # Perform updates
    if updates_needed and not dry_run:
        print(f"\nStep 4: Applying updates...")

        for update in updates_needed:
            cursor.execute("""
                UPDATE project_fee_breakdown
                SET
                    total_invoiced = ?,
                    total_paid = ?,
                    percentage_invoiced = ?,
                    percentage_paid = ?
                WHERE breakdown_id = ?
            """, (
                update['new']['total_invoiced'],
                update['new']['total_paid'],
                update['new']['pct_invoiced'],
                update['new']['pct_paid'],
                update['breakdown_id']
            ))

        conn.commit()
        print(f"  ✓ Updated {len(updates_needed)} breakdown records")

    elif updates_needed and dry_run:
        print(f"\nStep 4: SKIPPED (dry run mode)")
        print(f"  Would update {len(updates_needed)} breakdown records")
    else:
        print(f"\nStep 4: No updates needed - all breakdowns already in sync!")

    # Check for breakdowns with no invoices
    print(f"\nStep 5: Checking for breakdowns with no invoices...")
    no_invoice_breakdowns = []
    for breakdown_id, breakdown in breakdown_records.items():
        if breakdown_id not in invoice_totals:
            if breakdown['total_invoiced'] > 0 or breakdown['total_paid'] > 0:
                no_invoice_breakdowns.append(breakdown_id)

    if no_invoice_breakdowns:
        print(f"  ⚠️  WARNING: {len(no_invoice_breakdowns)} breakdowns have totals but no invoices:")
        for bid in no_invoice_breakdowns[:5]:
            print(f"      - {bid}")
        if len(no_invoice_breakdowns) > 5:
            print(f"      ... and {len(no_invoice_breakdowns) - 5} more")
    else:
        print(f"  ✓ All breakdowns with totals have corresponding invoices")

    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"  Total Breakdowns: {len(breakdown_records)}")
    print(f"  Breakdowns with Invoices: {len(invoice_totals)}")
    print(f"  Updates Applied: {len(updates_needed) if not dry_run else 0}")
    print(f"  Warnings: {len(no_invoice_breakdowns)}")
    print(f"{'='*80}\n")

    conn.close()
    return len(updates_needed)

def create_triggers(dry_run=False):
    """
    Create database triggers for auto-updating breakdown totals
    """
    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n{'='*80}")
    print(f"Creating Database Triggers for Auto-Update")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print(f"{'='*80}\n")

    # Drop existing triggers if they exist
    triggers_to_drop = [
        'update_breakdown_totals_insert',
        'update_breakdown_totals_update',
        'update_breakdown_totals_delete'
    ]

    for trigger_name in triggers_to_drop:
        try:
            if not dry_run:
                cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
                print(f"  ✓ Dropped old trigger: {trigger_name}")
        except sqlite3.Error as e:
            print(f"  Note: {trigger_name} did not exist")

    # Create INSERT trigger
    insert_trigger = """
    CREATE TRIGGER IF NOT EXISTS update_breakdown_totals_insert
    AFTER INSERT ON invoices
    FOR EACH ROW
    WHEN NEW.breakdown_id IS NOT NULL
    BEGIN
        UPDATE project_fee_breakdown
        SET
            total_invoiced = (
                SELECT COALESCE(SUM(invoice_amount), 0)
                FROM invoices
                WHERE breakdown_id = NEW.breakdown_id
            ),
            total_paid = (
                SELECT COALESCE(SUM(payment_amount), 0)
                FROM invoices
                WHERE breakdown_id = NEW.breakdown_id
            )
        WHERE breakdown_id = NEW.breakdown_id;

        UPDATE project_fee_breakdown
        SET
            percentage_invoiced = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_invoiced / phase_fee_usd * 100), 1)
                ELSE 0
            END,
            percentage_paid = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_paid / phase_fee_usd * 100), 1)
                ELSE 0
            END
        WHERE breakdown_id = NEW.breakdown_id;
    END;
    """

    # Create UPDATE trigger
    update_trigger = """
    CREATE TRIGGER IF NOT EXISTS update_breakdown_totals_update
    AFTER UPDATE ON invoices
    FOR EACH ROW
    WHEN NEW.breakdown_id IS NOT NULL OR OLD.breakdown_id IS NOT NULL
    BEGIN
        -- Update old breakdown if it changed
        UPDATE project_fee_breakdown
        SET
            total_invoiced = (
                SELECT COALESCE(SUM(invoice_amount), 0)
                FROM invoices
                WHERE breakdown_id = OLD.breakdown_id
            ),
            total_paid = (
                SELECT COALESCE(SUM(payment_amount), 0)
                FROM invoices
                WHERE breakdown_id = OLD.breakdown_id
            )
        WHERE breakdown_id = OLD.breakdown_id AND OLD.breakdown_id IS NOT NULL;

        UPDATE project_fee_breakdown
        SET
            percentage_invoiced = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_invoiced / phase_fee_usd * 100), 1)
                ELSE 0
            END,
            percentage_paid = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_paid / phase_fee_usd * 100), 1)
                ELSE 0
            END
        WHERE breakdown_id = OLD.breakdown_id AND OLD.breakdown_id IS NOT NULL;

        -- Update new breakdown
        UPDATE project_fee_breakdown
        SET
            total_invoiced = (
                SELECT COALESCE(SUM(invoice_amount), 0)
                FROM invoices
                WHERE breakdown_id = NEW.breakdown_id
            ),
            total_paid = (
                SELECT COALESCE(SUM(payment_amount), 0)
                FROM invoices
                WHERE breakdown_id = NEW.breakdown_id
            )
        WHERE breakdown_id = NEW.breakdown_id AND NEW.breakdown_id IS NOT NULL;

        UPDATE project_fee_breakdown
        SET
            percentage_invoiced = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_invoiced / phase_fee_usd * 100), 1)
                ELSE 0
            END,
            percentage_paid = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_paid / phase_fee_usd * 100), 1)
                ELSE 0
            END
        WHERE breakdown_id = NEW.breakdown_id AND NEW.breakdown_id IS NOT NULL;
    END;
    """

    # Create DELETE trigger
    delete_trigger = """
    CREATE TRIGGER IF NOT EXISTS update_breakdown_totals_delete
    AFTER DELETE ON invoices
    FOR EACH ROW
    WHEN OLD.breakdown_id IS NOT NULL
    BEGIN
        UPDATE project_fee_breakdown
        SET
            total_invoiced = (
                SELECT COALESCE(SUM(invoice_amount), 0)
                FROM invoices
                WHERE breakdown_id = OLD.breakdown_id
            ),
            total_paid = (
                SELECT COALESCE(SUM(payment_amount), 0)
                FROM invoices
                WHERE breakdown_id = OLD.breakdown_id
            )
        WHERE breakdown_id = OLD.breakdown_id;

        UPDATE project_fee_breakdown
        SET
            percentage_invoiced = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_invoiced / phase_fee_usd * 100), 1)
                ELSE 0
            END,
            percentage_paid = CASE
                WHEN phase_fee_usd > 0 THEN ROUND((total_paid / phase_fee_usd * 100), 1)
                ELSE 0
            END
        WHERE breakdown_id = OLD.breakdown_id;
    END;
    """

    if not dry_run:
        try:
            cursor.execute(insert_trigger)
            print(f"  ✓ Created trigger: update_breakdown_totals_insert")

            cursor.execute(update_trigger)
            print(f"  ✓ Created trigger: update_breakdown_totals_update")

            cursor.execute(delete_trigger)
            print(f"  ✓ Created trigger: update_breakdown_totals_delete")

            conn.commit()
            print(f"\n  ✅ All triggers created successfully!")
            print(f"  Breakdown totals will now auto-update when invoices change.")

        except sqlite3.Error as e:
            print(f"  ❌ Error creating triggers: {e}")
            conn.rollback()
            return False
    else:
        print(f"  Would create 3 triggers:")
        print(f"    - update_breakdown_totals_insert")
        print(f"    - update_breakdown_totals_update")
        print(f"    - update_breakdown_totals_delete")

    conn.close()
    return True

def main():
    """Main execution"""
    dry_run = '--dry-run' in sys.argv

    try:
        # Step 1: Sync existing data
        updates_count = sync_breakdown_totals(dry_run=dry_run)

        # Step 2: Create triggers for auto-updates
        if not dry_run and updates_count >= 0:
            create_triggers(dry_run=dry_run)
        elif dry_run:
            create_triggers(dry_run=dry_run)

        if dry_run:
            print(f"\n💡 TIP: Run without --dry-run to apply changes:")
            print(f"   python3 sync_breakdown_totals.py")
        else:
            print(f"\n✅ Sync complete! Breakdown totals are now accurate.")
            print(f"   Future invoice changes will auto-update breakdown totals.")

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
