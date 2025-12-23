#!/usr/bin/env python3
"""Complete Database Audit - Check everything"""
import sqlite3
import os

db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*80)
print("COMPREHENSIVE DATABASE AUDIT")
print("="*80)

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = [row[0] for row in cursor.fetchall()]
print(f"\n📊 Total Tables: {len(all_tables)}")

# Check critical tables with data
critical_checks = {
    'Core Data': [
        'proposals',
        'projects',
        'invoices',
        'emails',
        'email_proposal_links'
    ],
    'Contract Data': [
        'contract_metadata',
        'contract_phases',
        'contract_terms',
        'project_fee_breakdown',
        'contract_fee_breakdown'
    ],
    'Financial': [
        'invoice_aging',
        'payment_schedule'
    ],
    'People': [
        'contacts',
        'team_members'
    ],
    'Tracking': [
        'proposal_tracker',
        'schedule_entries',
        'email_attachments'
    ]
}

for category, tables in critical_checks.items():
    print(f"\n{category}:")
    for table in tables:
        if table in all_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                status = "✅" if count > 0 else "⚠️ "
                print(f"   {status} {table:30s}: {count:>6,} rows")
            except Exception as e:
                print(f"   ❌ {table:30s}: ERROR - {e}")
        else:
            print(f"   ❌ {table:30s}: TABLE MISSING")

# Check for contract-related data specifically
print("\n" + "="*80)
print("CONTRACT DATA DETAILS")
print("="*80)

# Check project_fee_breakdown detail
cursor.execute("""
    SELECT project_code, COUNT(*) as phases, SUM(phase_fee_usd) as total_fee
    FROM project_fee_breakdown
    GROUP BY project_code
    ORDER BY total_fee DESC
    LIMIT 10
""")
print("\nTop 10 Projects by Fee Breakdown:")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]} phases, ${row[2]:,.0f}")

# Check contract metadata
try:
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT project_id) FROM contract_metadata")
    contracts, unique_projects = cursor.fetchone()
    print(f"\nContract Metadata: {contracts} contracts for {unique_projects} projects")
except:
    print("\nContract Metadata: Table exists but may be empty or has issues")

# Check contract phases
try:
    cursor.execute("""
        SELECT COUNT(*), COUNT(DISTINCT project_id), COUNT(DISTINCT phase)
        FROM contract_phases
    """)
    total, projects, unique_phases = cursor.fetchone()
    print(f"Contract Phases: {total} phase entries, {projects} projects, {unique_phases} unique phases")
except:
    print("Contract Phases: Table exists but may be empty or has issues")

# Check contract terms
try:
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT project_id) FROM contract_terms")
    terms, projects = cursor.fetchone()
    print(f"Contract Terms: {terms} term entries for {projects} projects")
except:
    print("Contract Terms: Table exists but may be empty or has issues")

# Check projects with/without fee breakdowns
cursor.execute("""
    SELECT
        COUNT(DISTINCT p.project_code) as total_projects,
        COUNT(DISTINCT CASE WHEN fb.project_code IS NOT NULL THEN p.project_code END) as with_breakdown
    FROM projects p
    LEFT JOIN project_fee_breakdown fb ON p.project_code = fb.project_code
""")
total_proj, with_breakdown = cursor.fetchone()
missing = total_proj - with_breakdown
print(f"\nProjects with Fee Breakdown: {with_breakdown}/{total_proj}")
if missing > 0:
    print(f"⚠️  Missing fee breakdown: {missing} projects")
    cursor.execute("""
        SELECT p.project_code, p.project_title
        FROM projects p
        LEFT JOIN project_fee_breakdown fb ON p.project_code = fb.project_code
        WHERE fb.project_code IS NULL
        LIMIT 10
    """)
    print("\nProjects without fee breakdown:")
    for code, title in cursor.fetchall():
        print(f"   • {code}: {title}")

# Check invoices linked to projects
cursor.execute("""
    SELECT
        COUNT(*) as total_invoices,
        COUNT(CASE WHEN project_id IS NOT NULL THEN 1 END) as linked,
        COUNT(CASE WHEN project_id IS NULL THEN 1 END) as orphaned
    FROM invoices
""")
total_inv, linked, orphaned = cursor.fetchone()
print(f"\nInvoices: {total_inv} total, {linked} linked to projects, {orphaned} orphaned")

# Check email processing status
cursor.execute("""
    SELECT
        COUNT(*) as total_emails,
        COUNT(DISTINCT epl.email_id) as processed
    FROM emails e
    LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
""")
total_emails, processed_emails = cursor.fetchone()
unprocessed = total_emails - processed_emails
print(f"\nEmails: {total_emails} total, {processed_emails} processed, {unprocessed} unprocessed")

# Check proposal tracker
cursor.execute("""
    SELECT COUNT(*),
           COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
           COUNT(CASE WHEN status = 'won' THEN 1 END) as won,
           COUNT(CASE WHEN status = 'lost' THEN 1 END) as lost
    FROM proposal_tracker
""")
result = cursor.fetchone()
if result:
    total, active, won, lost = result
    print(f"\nProposal Tracker: {total} tracked ({active} active, {won} won, {lost} lost)")

conn.close()
print("\n" + "="*80)
print("AUDIT COMPLETE")
print("="*80)
