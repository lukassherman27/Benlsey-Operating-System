#!/usr/bin/env python3
"""
Complete Database Audit - Desktop vs OneDrive

Make sure we're not missing ANY critical data before archiving Desktop.
"""
import sqlite3
import os

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "database/bensley_master.db"

def audit_databases():
    """Complete audit of both databases"""

    print("="*100)
    print("COMPLETE DATABASE AUDIT - DESKTOP vs ONEDRIVE")
    print("="*100)

    desktop_conn = sqlite3.connect(DESKTOP_DB)
    onedrive_conn = sqlite3.connect(ONEDRIVE_DB)

    desktop_cursor = desktop_conn.cursor()
    onedrive_cursor = onedrive_conn.cursor()

    # Get all tables from both
    desktop_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    desktop_tables = {row[0] for row in desktop_cursor.fetchall()}

    onedrive_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    onedrive_tables = {row[0] for row in onedrive_cursor.fetchall()}

    # Tables only in Desktop
    desktop_only = desktop_tables - onedrive_tables
    # Tables only in OneDrive
    onedrive_only = onedrive_tables - desktop_tables
    # Tables in both
    common_tables = desktop_tables & onedrive_tables

    print(f"\n📊 TABLE SUMMARY:")
    print(f"   Desktop tables: {len(desktop_tables)}")
    print(f"   OneDrive tables: {len(onedrive_tables)}")
    print(f"   Common: {len(common_tables)}")
    print(f"   Desktop-only: {len(desktop_only)}")
    print(f"   OneDrive-only: {len(onedrive_only)}")

    # CRITICAL TABLES TO AUDIT
    critical_tables = [
        'proposals',
        'projects',
        'invoices',
        'emails',
        'contracts',
        'clients',
        'contacts',
        'project_fee_breakdown',
        'contract_payment_terms',
        'invoice_aging',
        'proposal_tracker',
        'weekly_proposal_reports'
    ]

    print(f"\n{'='*100}")
    print("CRITICAL DATA AUDIT")
    print(f"{'='*100}")

    issues = []
    to_migrate = []

    for table in critical_tables:
        if table not in desktop_tables and table not in onedrive_tables:
            continue

        desktop_count = 0
        onedrive_count = 0

        if table in desktop_tables:
            try:
                desktop_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                desktop_count = desktop_cursor.fetchone()[0]
            except:
                desktop_count = "ERROR"

        if table in onedrive_tables:
            try:
                onedrive_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                onedrive_count = onedrive_cursor.fetchone()[0]
            except:
                onedrive_count = "ERROR"

        # Analyze the difference
        status = "✅"
        notes = ""

        if table not in onedrive_tables:
            status = "⚠️ "
            notes = "MISSING in OneDrive"
            if desktop_count > 0:
                to_migrate.append((table, desktop_count, "Table missing"))
                issues.append(f"{table}: {desktop_count} rows in Desktop, TABLE MISSING in OneDrive")

        elif desktop_count > onedrive_count:
            diff = desktop_count - onedrive_count if isinstance(desktop_count, int) and isinstance(onedrive_count, int) else "?"
            status = "⚠️ "
            notes = f"Desktop has {diff} MORE rows"
            if isinstance(diff, int) and diff > 0:
                to_migrate.append((table, diff, f"Missing {diff} rows"))
                issues.append(f"{table}: Desktop has {diff} more rows")

        elif onedrive_count > desktop_count:
            diff = onedrive_count - desktop_count if isinstance(desktop_count, int) and isinstance(onedrive_count, int) else "?"
            status = "✅"
            notes = f"OneDrive has {diff} MORE (newer data)"

        else:
            notes = "Equal"

        print(f"{status} {table:<30} Desktop: {str(desktop_count):>6} | OneDrive: {str(onedrive_count):>6} | {notes}")

    # Check Desktop-only tables with data
    print(f"\n{'='*100}")
    print("DESKTOP-ONLY TABLES (Not in OneDrive)")
    print(f"{'='*100}")

    desktop_only_with_data = []
    for table in sorted(desktop_only):
        if table.startswith('sqlite_'):
            continue

        try:
            desktop_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = desktop_cursor.fetchone()[0]
            if count > 0:
                desktop_only_with_data.append((table, count))
        except:
            pass

    if desktop_only_with_data:
        print(f"\n⚠️  Found {len(desktop_only_with_data)} Desktop-only tables WITH DATA:")
        for table, count in desktop_only_with_data[:20]:
            print(f"   • {table:<40} {count:>6} rows")

            # Mark important ones for migration
            important_keywords = ['proposal', 'project', 'invoice', 'contract', 'payment', 'client', 'contact', 'financial']
            if any(keyword in table.lower() for keyword in important_keywords):
                to_migrate.append((table, count, "Desktop-only important table"))

        if len(desktop_only_with_data) > 20:
            print(f"   ... and {len(desktop_only_with_data) - 20} more")
    else:
        print("✅ No Desktop-only tables with data")

    # Check data quality in common tables
    print(f"\n{'='*100}")
    print("DATA QUALITY CHECKS")
    print(f"{'='*100}")

    # Check proposals with contacts
    if 'proposals' in common_tables:
        # Desktop
        desktop_cursor.execute("PRAGMA table_info(proposals)")
        desktop_cols = {col[1] for col in desktop_cursor.fetchall()}

        onedrive_cursor.execute("PRAGMA table_info(proposals)")
        onedrive_cols = {col[1] for col in onedrive_cursor.fetchall()}

        # Check for contact columns
        desktop_has_contacts = 'contact_person' in desktop_cols or 'contact_email' in desktop_cols
        onedrive_has_contacts = 'contact_person' in onedrive_cols or 'contact_email' in onedrive_cols

        if onedrive_has_contacts:
            onedrive_cursor.execute("SELECT COUNT(*) FROM proposals WHERE contact_person IS NOT NULL OR contact_email IS NOT NULL")
            onedrive_with_contacts = onedrive_cursor.fetchone()[0]
            print(f"✅ Proposals: OneDrive has {onedrive_with_contacts} with contact info")
        else:
            print(f"⚠️  Proposals: OneDrive schema missing contact columns")

    # Check invoices with outstanding amounts
    if 'invoices' in common_tables:
        desktop_cursor.execute("SELECT SUM(invoice_amount - COALESCE(payment_amount, 0)) FROM invoices WHERE status='outstanding'")
        desktop_outstanding = desktop_cursor.fetchone()[0] or 0

        onedrive_cursor.execute("SELECT SUM(invoice_amount - COALESCE(payment_amount, 0)) FROM invoices WHERE status='outstanding'")
        onedrive_outstanding = onedrive_cursor.fetchone()[0] or 0

        print(f"   Desktop outstanding invoices: ${desktop_outstanding:,.0f}")
        print(f"   OneDrive outstanding invoices: ${onedrive_outstanding:,.0f}")

        if abs(desktop_outstanding - onedrive_outstanding) > 100000:
            diff = abs(desktop_outstanding - onedrive_outstanding)
            issues.append(f"invoices: ${diff:,.0f} difference in outstanding amounts")
            print(f"   ⚠️  ${diff:,.0f} difference!")

    # FINAL SUMMARY
    print(f"\n{'='*100}")
    print("MIGRATION RECOMMENDATIONS")
    print(f"{'='*100}")

    if not issues:
        print("✅ No critical issues found!")
        print("✅ OneDrive has all the data Desktop has")
    else:
        print(f"⚠️  Found {len(issues)} issues:\n")
        for issue in issues:
            print(f"   • {issue}")

    if to_migrate:
        print(f"\n📋 RECOMMEND MIGRATING {len(to_migrate)} items:")
        for table, count, reason in to_migrate[:15]:
            print(f"   • {table}: {count} rows ({reason})")

        if len(to_migrate) > 15:
            print(f"   ... and {len(to_migrate) - 15} more")

        # Save detailed migration list
        with open('migration_recommendations.txt', 'w') as f:
            f.write("MIGRATION RECOMMENDATIONS\n")
            f.write("="*80 + "\n\n")
            for table, count, reason in to_migrate:
                f.write(f"{table}: {count} rows - {reason}\n")
        print(f"\n📄 Saved detailed list to: migration_recommendations.txt")

    else:
        print("\n✅ Nothing to migrate - OneDrive is complete!")

    desktop_conn.close()
    onedrive_conn.close()

if __name__ == '__main__':
    audit_databases()
