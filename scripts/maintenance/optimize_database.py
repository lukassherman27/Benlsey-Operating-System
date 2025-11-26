#!/usr/bin/env python3
"""
Database Optimization Script

Optimizes the OneDrive master database:
1. Adds missing indexes on critical tables
2. Enables foreign keys for data integrity
3. Runs VACUUM to reclaim space
4. Runs ANALYZE to optimize query plans
5. Verifies all relationships
"""
import sqlite3
import os
from datetime import datetime

db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

def backup_database():
    """Create backup before optimization"""
    backup_path = f"database/backups/bensley_master_pre_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.makedirs("database/backups", exist_ok=True)
    os.system(f"cp {db_path} {backup_path}")
    print(f"✅ Backup: {backup_path}")
    return backup_path

def check_existing_indexes(conn):
    """Check what indexes already exist"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, tbl_name
        FROM sqlite_master
        WHERE type='index' AND sql IS NOT NULL
        ORDER BY tbl_name, name
    """)
    indexes = cursor.fetchall()

    print(f"\n📊 Existing Indexes: {len(indexes)}")

    # Group by table
    by_table = {}
    for idx_name, tbl_name in indexes:
        if tbl_name not in by_table:
            by_table[tbl_name] = []
        by_table[tbl_name].append(idx_name)

    for table in ['proposals', 'projects', 'invoices', 'emails', 'email_proposal_links']:
        if table in by_table:
            print(f"   {table}: {len(by_table[table])} indexes")

    return by_table

def add_critical_indexes(conn):
    """Add missing indexes on critical tables"""
    cursor = conn.cursor()

    # Critical indexes for performance
    indexes_to_add = [
        # Proposals
        ("idx_proposals_code", "CREATE INDEX IF NOT EXISTS idx_proposals_code ON proposals(project_code)"),
        ("idx_proposals_status", "CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status)"),
        ("idx_proposals_contact", "CREATE INDEX IF NOT EXISTS idx_proposals_contact ON proposals(contact_email)"),

        # Projects
        ("idx_projects_code", "CREATE INDEX IF NOT EXISTS idx_projects_code ON projects(project_code)"),
        ("idx_projects_status", "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)"),
        ("idx_projects_fee", "CREATE INDEX IF NOT EXISTS idx_projects_fee ON projects(total_fee_usd)"),

        # Invoices
        ("idx_invoices_project", "CREATE INDEX IF NOT EXISTS idx_invoices_project ON invoices(project_id)"),
        ("idx_invoices_project_code", "CREATE INDEX IF NOT EXISTS idx_invoices_project_code ON invoices(project_code)"),
        ("idx_invoices_number", "CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number)"),
        ("idx_invoices_status", "CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)"),
        ("idx_invoices_date", "CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)"),

        # Emails
        ("idx_emails_sender", "CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender)"),
        ("idx_emails_date", "CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date)"),
        ("idx_emails_subject", "CREATE INDEX IF NOT EXISTS idx_emails_subject ON emails(subject)"),

        # Email-Proposal Links
        ("idx_epl_email", "CREATE INDEX IF NOT EXISTS idx_epl_email ON email_proposal_links(email_id)"),
        ("idx_epl_proposal", "CREATE INDEX IF NOT EXISTS idx_epl_proposal ON email_proposal_links(proposal_id)"),
        ("idx_epl_category", "CREATE INDEX IF NOT EXISTS idx_epl_category ON email_proposal_links(category)"),

        # Project Fee Breakdown
        ("idx_fee_breakdown_code", "CREATE INDEX IF NOT EXISTS idx_fee_breakdown_code ON project_fee_breakdown(project_code)"),
        ("idx_fee_breakdown_phase", "CREATE INDEX IF NOT EXISTS idx_fee_breakdown_phase ON project_fee_breakdown(phase)"),

        # Invoice Aging
        ("idx_aging_project", "CREATE INDEX IF NOT EXISTS idx_aging_project ON invoice_aging(project_id)"),
        ("idx_aging_days", "CREATE INDEX IF NOT EXISTS idx_aging_days ON invoice_aging(days_outstanding)"),

        # Contacts
        ("idx_contacts_email", "CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email)"),
        ("idx_contacts_company", "CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company)"),

        # Proposal Tracker
        ("idx_tracker_code", "CREATE INDEX IF NOT EXISTS idx_tracker_code ON proposal_tracker(project_code)"),
        ("idx_tracker_status", "CREATE INDEX IF NOT EXISTS idx_tracker_status ON proposal_tracker(status)"),
    ]

    print(f"\n🔨 Adding/Verifying {len(indexes_to_add)} Critical Indexes...")
    added = 0

    for idx_name, sql in indexes_to_add:
        try:
            cursor.execute(sql)
            added += 1
            print(f"   ✅ {idx_name}")
        except Exception as e:
            if "already exists" not in str(e).lower():
                print(f"   ⚠️  {idx_name}: {e}")

    conn.commit()
    print(f"✅ Processed {added} indexes")

def enable_foreign_keys(conn):
    """Enable foreign key constraints"""
    cursor = conn.cursor()

    # Check current setting
    cursor.execute("PRAGMA foreign_keys")
    current = cursor.fetchone()[0]

    print(f"\n🔗 Foreign Keys Currently: {'ENABLED' if current else 'DISABLED'}")

    if not current:
        cursor.execute("PRAGMA foreign_keys = ON")
        print("   ✅ Enabled foreign key constraints")

    conn.commit()

def vacuum_database(conn):
    """Run VACUUM to reclaim space and defragment"""
    print("\n🧹 Running VACUUM (reclaim space, defragment)...")

    # Get size before
    cursor = conn.cursor()
    cursor.execute("PRAGMA page_count")
    page_count_before = cursor.fetchone()[0]
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    size_before = (page_count_before * page_size) / (1024 * 1024)  # MB

    print(f"   Database size before: {size_before:.2f} MB")

    # VACUUM must be run outside transaction
    conn.commit()
    conn.execute("VACUUM")

    # Get size after
    cursor.execute("PRAGMA page_count")
    page_count_after = cursor.fetchone()[0]
    size_after = (page_count_after * page_size) / (1024 * 1024)  # MB

    print(f"   Database size after: {size_after:.2f} MB")
    print(f"   ✅ Saved {size_before - size_after:.2f} MB")

def analyze_database(conn):
    """Run ANALYZE to update query optimizer statistics"""
    print("\n📊 Running ANALYZE (optimize query plans)...")
    conn.execute("ANALYZE")
    conn.commit()
    print("   ✅ Query optimizer statistics updated")

def verify_relationships(conn):
    """Verify critical table relationships"""
    cursor = conn.cursor()

    print("\n🔍 Verifying Data Relationships...")

    checks = [
        ("Proposals → Projects", """
            SELECT COUNT(*) FROM proposals p
            LEFT JOIN projects pr ON p.project_code = pr.project_code
            WHERE p.status = 'Won' AND pr.project_id IS NULL
        """),
        ("Invoices → Projects", """
            SELECT COUNT(*) FROM invoices i
            LEFT JOIN projects p ON i.project_id = p.project_id
            WHERE i.project_id IS NOT NULL AND p.project_id IS NULL
        """),
        ("Email Links → Emails", """
            SELECT COUNT(*) FROM email_proposal_links epl
            LEFT JOIN emails e ON epl.email_id = e.email_id
            WHERE e.email_id IS NULL
        """),
        ("Email Links → Proposals", """
            SELECT COUNT(*) FROM email_proposal_links epl
            LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE p.proposal_id IS NULL
        """),
        ("Fee Breakdown → Projects", """
            SELECT COUNT(*) FROM project_fee_breakdown fb
            LEFT JOIN projects p ON fb.project_code = p.project_code
            WHERE p.project_code IS NULL
        """),
    ]

    issues = 0
    for check_name, sql in checks:
        cursor.execute(sql)
        orphans = cursor.fetchone()[0]
        if orphans > 0:
            print(f"   ⚠️  {check_name}: {orphans} orphaned records")
            issues += 1
        else:
            print(f"   ✅ {check_name}: OK")

    if issues == 0:
        print("\n✅ All relationships verified!")
    else:
        print(f"\n⚠️  Found {issues} relationship issues (non-critical)")

def get_database_stats(conn):
    """Get overall database statistics"""
    cursor = conn.cursor()

    print("\n" + "="*80)
    print("DATABASE STATISTICS")
    print("="*80)

    # Table counts
    tables = ['proposals', 'projects', 'invoices', 'emails', 'email_proposal_links',
              'contacts', 'project_fee_breakdown', 'invoice_aging', 'proposal_tracker']

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table:30s}: {count:>6,} rows")
        except:
            pass

    # Index count
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
    idx_count = cursor.fetchone()[0]
    print(f"\n   Total Indexes: {idx_count}")

    # Database size
    cursor.execute("PRAGMA page_count")
    page_count = cursor.fetchone()[0]
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    size_mb = (page_count * page_size) / (1024 * 1024)
    print(f"   Database Size: {size_mb:.2f} MB")

    print("="*80)

def main():
    print("="*80)
    print("DATABASE OPTIMIZATION")
    print("="*80)

    # Backup first
    backup_path = backup_database()

    # Connect
    conn = sqlite3.connect(db_path)

    try:
        # 1. Check existing indexes
        existing_indexes = check_existing_indexes(conn)

        # 2. Add missing critical indexes
        add_critical_indexes(conn)

        # 3. Enable foreign keys
        enable_foreign_keys(conn)

        # 4. Verify relationships
        verify_relationships(conn)

        # 5. VACUUM (outside transaction)
        vacuum_database(conn)

        # 6. ANALYZE
        analyze_database(conn)

        # 7. Final stats
        get_database_stats(conn)

        print("\n" + "="*80)
        print("✅ OPTIMIZATION COMPLETE!")
        print("="*80)
        print(f"Backup saved: {backup_path}")
        print("Database is now optimized for performance and integrity.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"Restore from backup if needed: cp {backup_path} {db_path}")
        raise

    finally:
        conn.close()

if __name__ == '__main__':
    main()
