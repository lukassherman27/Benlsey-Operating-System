#!/usr/bin/env python3
"""
Complete System Inventory - Show EVERYTHING
"""
import sqlite3
import os
import glob

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "database/bensley_master.db"

def check_database(db_path, db_name):
    """Complete inventory of a database"""
    print(f"\n{'='*100}")
    print(f"{db_name} DATABASE: {db_path}")
    print(f"{'='*100}")

    if not os.path.exists(db_path):
        print(f"❌ DOES NOT EXIST")
        return

    size_mb = os.path.getsize(db_path) / (1024*1024)
    print(f"Size: {size_mb:.1f}MB")
    print(f"Modified: {os.path.getmtime(db_path)}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n📊 TABLES: {len(tables)} total")

    # Count data in key tables
    key_tables = {
        'proposals': 'Proposal/Project tracking',
        'projects': 'Active projects',
        'invoices': 'Invoice data',
        'emails': 'Email data',
        'email_proposal_links': 'Email-to-proposal links',
        'contracts': 'Contract data',
        'contract_payment_terms': 'Payment schedules',
        'project_fee_breakdown': 'Fee breakdowns by phase',
        'attachments': 'File attachments',
        'clients': 'Client contacts',
        'project_contacts': 'Project-specific contacts'
    }

    print(f"\n📋 KEY DATA:")
    for table, description in key_tables.items():
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {table}: {count} rows - {description}")

            # Special handling for key tables
            if table == 'proposals' and count > 0:
                cursor.execute("PRAGMA table_info(proposals)")
                cols = [col[1] for col in cursor.fetchall()]
                has_contacts = 'contact_person' in cols or 'contact_email' in cols
                cursor.execute("SELECT COUNT(*) FROM proposals WHERE contact_person IS NOT NULL OR contact_email IS NOT NULL")
                with_contacts = cursor.fetchone()[0]
                print(f"      → {with_contacts} have contact info")

            elif table == 'projects' and count > 0:
                cursor.execute("PRAGMA table_info(projects)")
                cols = [col[1] for col in cursor.fetchall()]
                print(f"      → Columns: {', '.join(cols[:10])}...")

            elif table == 'invoices' and count > 0:
                cursor.execute("SELECT COUNT(*) FROM invoices WHERE status='outstanding'")
                outstanding = cursor.fetchone()[0]
                cursor.execute("SELECT SUM(invoice_amount - COALESCE(payment_amount, 0)) FROM invoices WHERE status='outstanding'")
                unpaid = cursor.fetchone()[0] or 0
                print(f"      → {outstanding} outstanding (${unpaid:,.0f} unpaid)")

            elif table == 'emails' and count > 0:
                cursor.execute("SELECT COUNT(*) FROM emails WHERE processed=1")
                processed = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM emails WHERE has_attachments=1")
                with_attach = cursor.fetchone()[0]
                print(f"      → {processed} processed, {with_attach} with attachments")

        else:
            print(f"   ❌ {table}: NOT EXISTS - {description}")

    # Show OTHER tables not in key list
    other_tables = [t for t in tables if t not in key_tables]
    if other_tables:
        print(f"\n📦 OTHER TABLES ({len(other_tables)}):")
        for table in other_tables[:20]:  # Show first 20
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   • {table}: {count} rows")
        if len(other_tables) > 20:
            print(f"   ... and {len(other_tables) - 20} more")

    conn.close()

def check_file_system():
    """Check what files/scripts exist"""
    print(f"\n{'='*100}")
    print("FILE SYSTEM INVENTORY")
    print(f"{'='*100}")

    # Python scripts
    print(f"\n🐍 PYTHON SCRIPTS:")
    scripts = glob.glob("*.py")
    email_scripts = [s for s in scripts if 'email' in s.lower()]
    import_scripts = [s for s in scripts if 'import' in s.lower() or 'parse' in s.lower()]
    other_scripts = [s for s in scripts if s not in email_scripts and s not in import_scripts]

    print(f"\n   Email Processing Scripts ({len(email_scripts)}):")
    for script in sorted(email_scripts):
        size = os.path.getsize(script)
        print(f"   • {script} ({size} bytes)")

    print(f"\n   Import/Parse Scripts ({len(import_scripts)}):")
    for script in sorted(import_scripts)[:15]:  # Show first 15
        size = os.path.getsize(script)
        print(f"   • {script} ({size} bytes)")
    if len(import_scripts) > 15:
        print(f"   ... and {len(import_scripts) - 15} more")

    print(f"\n   Other Scripts ({len(other_scripts)}):")
    for script in sorted(other_scripts)[:10]:
        size = os.path.getsize(script)
        print(f"   • {script} ({size} bytes)")
    if len(other_scripts) > 10:
        print(f"   ... and {len(other_scripts) - 10} more")

    # Database files
    print(f"\n💾 DATABASE FILES:")
    db_files = glob.glob("**/*.db", recursive=True) + glob.glob("database/**/*.db", recursive=True)
    for db in set(db_files):
        if os.path.exists(db):
            size_mb = os.path.getsize(db) / (1024*1024)
            print(f"   • {db} ({size_mb:.1f}MB)")

    # Backup directories
    print(f"\n📦 BACKUP DIRECTORIES:")
    if os.path.exists("database/backups"):
        backups = os.listdir("database/backups")
        print(f"   • database/backups: {len(backups)} files")
    else:
        print(f"   • database/backups: NOT EXISTS")

    # Attachments/documents
    print(f"\n📎 ATTACHMENTS/DOCUMENTS:")
    doc_dirs = ['attachments', 'documents', 'uploads', 'files']
    for dir_name in doc_dirs:
        if os.path.exists(dir_name):
            files = glob.glob(f"{dir_name}/**/*", recursive=True)
            print(f"   • {dir_name}: {len(files)} files")
        else:
            print(f"   • {dir_name}: NOT EXISTS")

    # Configuration
    print(f"\n⚙️  CONFIGURATION:")
    config_files = ['.env', 'config.json', 'settings.py', '.env.example']
    for config in config_files:
        if os.path.exists(config):
            print(f"   ✅ {config}")
        else:
            print(f"   ❌ {config}")

def main():
    print("="*100)
    print("COMPLETE SYSTEM INVENTORY")
    print("="*100)

    # Check both databases
    check_database(ONEDRIVE_DB, "ONEDRIVE (Current Working)")
    check_database(DESKTOP_DB, "DESKTOP")

    # Check file system
    check_file_system()

    print(f"\n{'='*100}")
    print("SUMMARY & RECOMMENDATIONS")
    print(f"{'='*100}")

    # Load both and compare
    if os.path.exists(ONEDRIVE_DB) and os.path.exists(DESKTOP_DB):
        conn_od = sqlite3.connect(ONEDRIVE_DB)
        conn_dt = sqlite3.connect(DESKTOP_DB)

        # Compare key metrics
        print(f"\n📊 SIDE-BY-SIDE COMPARISON:")

        metrics = [
            ("Emails", "SELECT COUNT(*) FROM emails"),
            ("Proposals", "SELECT COUNT(*) FROM proposals"),
            ("Invoices", "SELECT COUNT(*) FROM invoices"),
            ("Invoice $ Outstanding", "SELECT SUM(invoice_amount - COALESCE(payment_amount, 0)) FROM invoices WHERE status='outstanding'"),
        ]

        print(f"\n{'Metric':<30} {'OneDrive':<20} {'Desktop':<20} {'Winner':<20}")
        print("-"*90)

        for metric_name, query in metrics:
            try:
                od_val = conn_od.execute(query).fetchone()[0] or 0
                dt_val = conn_dt.execute(query).fetchone()[0] or 0

                if '$' in metric_name:
                    od_str = f"${od_val:,.0f}"
                    dt_str = f"${dt_val:,.0f}"
                else:
                    od_str = f"{od_val:,}"
                    dt_str = f"{dt_val:,}"

                winner = "OneDrive" if od_val >= dt_val else "Desktop"
                print(f"{metric_name:<30} {od_str:<20} {dt_str:<20} {winner:<20}")
            except:
                print(f"{metric_name:<30} {'ERROR':<20} {'ERROR':<20} {'-':<20}")

        conn_od.close()
        conn_dt.close()

if __name__ == '__main__':
    main()
