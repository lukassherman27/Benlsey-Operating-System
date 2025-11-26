#!/usr/bin/env python3
"""
Investigate Missing Invoices, Projects, Proposals

Are they real or duplicates?
"""
import sqlite3

DESKTOP_DB = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
ONEDRIVE_DB = "database/bensley_master.db"

def investigate():
    """Investigate what Desktop has that OneDrive doesn't"""

    print("="*100)
    print("INVESTIGATING MISSING DATA")
    print("="*100)

    desktop_conn = sqlite3.connect(DESKTOP_DB)
    onedrive_conn = sqlite3.connect(ONEDRIVE_DB)

    desktop_conn.row_factory = sqlite3.Row
    onedrive_conn.row_factory = sqlite3.Row

    desktop_cursor = desktop_conn.cursor()
    onedrive_cursor = onedrive_conn.cursor()

    # 1. INVESTIGATE INVOICES
    print("\n" + "="*100)
    print("1. INVESTIGATING 294 EXTRA INVOICES IN DESKTOP")
    print("="*100)

    # Get Desktop invoice IDs
    desktop_cursor.execute("SELECT invoice_id FROM invoices")
    desktop_invoice_ids = {row[0] for row in desktop_cursor.fetchall()}

    # Get OneDrive invoice IDs
    onedrive_cursor.execute("SELECT invoice_id FROM invoices")
    onedrive_invoice_ids = {row[0] for row in onedrive_cursor.fetchall()}

    # Find invoices only in Desktop
    desktop_only_invoices = desktop_invoice_ids - onedrive_invoice_ids

    print(f"\nDesktop has {len(desktop_only_invoices)} invoices NOT in OneDrive")

    if desktop_only_invoices:
        # Sample 10 missing invoices
        sample_ids = list(desktop_only_invoices)[:10]
        placeholders = ','.join(['?' for _ in sample_ids])

        desktop_cursor.execute(f"""
            SELECT invoice_id, invoice_number, invoice_date, invoice_amount, status, discipline, phase
            FROM invoices
            WHERE invoice_id IN ({placeholders})
            ORDER BY invoice_date DESC
        """, sample_ids)

        print("\n📋 SAMPLE OF MISSING INVOICES:")
        for row in desktop_cursor.fetchall():
            print(f"   • {row['invoice_number']}: ${row['invoice_amount']:,.0f} | {row['status']} | {row['invoice_date']} | {row['discipline']} - {row['phase']}")

        # Check if they're for projects we don't have
        desktop_cursor.execute(f"""
            SELECT project_code, COUNT(*) as count, SUM(invoice_amount) as total
            FROM invoices
            WHERE invoice_id IN ({placeholders})
            GROUP BY project_code
        """, sample_ids)

        print("\n📊 PROJECTS FOR MISSING INVOICES:")
        for row in desktop_cursor.fetchall():
            project_code = row['project_code']

            # Check if this project exists in OneDrive
            onedrive_cursor.execute("SELECT COUNT(*) FROM projects WHERE project_code = ?", (project_code,))
            exists_in_onedrive = onedrive_cursor.fetchone()[0] > 0

            status = "✅ Project in OneDrive" if exists_in_onedrive else "❌ Project NOT in OneDrive"
            print(f"   • {project_code}: {row['count']} invoices, ${row['total']:,.0f} | {status}")

        # Summary of ALL missing invoices
        desktop_cursor.execute(f"""
            SELECT
                COUNT(*) as total_invoices,
                SUM(invoice_amount) as total_amount,
                COUNT(CASE WHEN status='outstanding' THEN 1 END) as outstanding_count,
                SUM(CASE WHEN status='outstanding' THEN invoice_amount - COALESCE(payment_amount, 0) ELSE 0 END) as outstanding_amount
            FROM invoices
            WHERE invoice_id IN ({','.join(['?' for _ in desktop_only_invoices])})
        """, list(desktop_only_invoices))

        summary = desktop_cursor.fetchone()
        print(f"\n💰 SUMMARY OF ALL {len(desktop_only_invoices)} MISSING INVOICES:")
        print(f"   Total invoiced: ${summary['total_amount']:,.0f}")
        print(f"   Outstanding: {summary['outstanding_count']} invoices, ${summary['outstanding_amount']:,.0f}")

    # 2. INVESTIGATE PROJECTS
    print("\n" + "="*100)
    print("2. INVESTIGATING 87 EXTRA PROJECTS IN DESKTOP")
    print("="*100)

    # Get Desktop project codes
    desktop_cursor.execute("SELECT project_code FROM projects")
    desktop_project_codes = {row[0] for row in desktop_cursor.fetchall()}

    # Get OneDrive project codes
    onedrive_cursor.execute("SELECT project_code FROM projects")
    onedrive_project_codes = {row[0] for row in onedrive_cursor.fetchall()}

    # Find projects only in Desktop
    desktop_only_projects = desktop_project_codes - onedrive_project_codes

    print(f"\nDesktop has {len(desktop_only_projects)} projects NOT in OneDrive")

    if desktop_only_projects:
        # Get details on missing projects
        placeholders = ','.join(['?' for _ in list(desktop_only_projects)[:20]])
        desktop_cursor.execute(f"""
            SELECT project_code, project_name, status, total_fee_usd
            FROM projects
            WHERE project_code IN ({placeholders})
            ORDER BY total_fee_usd DESC NULLS LAST
        """, list(desktop_only_projects)[:20])

        print("\n📋 TOP 20 MISSING PROJECTS BY FEE:")
        for row in desktop_cursor.fetchall():
            fee = f"${row['total_fee_usd']:,.0f}" if row['total_fee_usd'] else "N/A"
            print(f"   • {row['project_code']}: {row['project_name'][:60]} | {row['status']} | {fee}")

    # 3. INVESTIGATE PROPOSALS
    print("\n" + "="*100)
    print("3. INVESTIGATING 27 EXTRA PROPOSALS IN DESKTOP")
    print("="*100)

    # Get Desktop proposal IDs
    desktop_cursor.execute("SELECT proposal_id FROM proposals")
    desktop_proposal_ids = {row[0] for row in desktop_cursor.fetchall()}

    # Get OneDrive proposal IDs
    onedrive_cursor.execute("SELECT proposal_id FROM proposals")
    onedrive_proposal_ids = {row[0] for row in onedrive_cursor.fetchall()}

    # Find proposals only in Desktop
    desktop_only_proposals = desktop_proposal_ids - onedrive_proposal_ids

    print(f"\nDesktop has {len(desktop_only_proposals)} proposals NOT in OneDrive")

    if desktop_only_proposals:
        placeholders = ','.join(['?' for _ in list(desktop_only_proposals)[:20]])
        desktop_cursor.execute(f"""
            SELECT proposal_id, project_code, project_name, status
            FROM proposals
            WHERE proposal_id IN ({placeholders})
            ORDER BY proposal_id DESC
        """, list(desktop_only_proposals)[:20])

        print("\n📋 MISSING PROPOSALS:")
        for row in desktop_cursor.fetchall():
            print(f"   • {row['project_code']}: {row['project_name'][:60]} | {row['status']}")

    # FINAL RECOMMENDATION
    print("\n" + "="*100)
    print("RECOMMENDATION")
    print("="*100)

    print(f"""
Based on investigation:

1. INVOICES ({len(desktop_only_invoices)} missing):
   - Check if they're for projects OneDrive doesn't have
   - If yes: Need to migrate those projects first
   - If no: These might be old/duplicate data

2. PROJECTS ({len(desktop_only_projects)} missing):
   - Review the list above
   - Are these active projects you need?
   - Or are they old/cancelled/duplicate?

3. PROPOSALS ({len(desktop_only_proposals)} missing):
   - Similar - review if needed

NEXT STEPS:
- Review the lists above
- Tell me which ones to migrate
- OR tell me to skip them if they're old data
    """)

    desktop_conn.close()
    onedrive_conn.close()

if __name__ == '__main__':
    investigate()
