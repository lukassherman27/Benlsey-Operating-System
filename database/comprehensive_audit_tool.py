#!/usr/bin/env python3
"""
Comprehensive Database Audit Tool
Allows manual review and update of all proposals and projects
"""

import sqlite3
import sys
from datetime import datetime
from typing import Optional

DB_PATH = "bensley_master.db"

def clear_screen():
    print("\n" * 2)

def show_proposal(conn, proposal):
    """Display a single proposal with all its details"""
    cursor = conn.cursor()

    print("=" * 80)
    print(f"PROJECT CODE: {proposal['project_code']}")
    print("=" * 80)

    print(f"\n📋 BASIC INFO:")
    print(f"  Name: {proposal['project_name']}")
    print(f"  Client: {proposal['client_company'] or 'NOT SET'}")
    print(f"  Contact: {proposal.get('contact_person') or 'NOT SET'}")
    print(f"  Value: ${proposal['project_value']:,.0f}" if proposal['project_value'] else "  Value: NOT SET")

    print(f"\n📊 STATUS:")
    print(f"  Current Status: {proposal['status']}")
    print(f"  Is Active Project: {'YES' if proposal['is_active_project'] else 'NO'}")
    if proposal.get('on_hold'):
        print(f"  On Hold: YES - {proposal.get('on_hold_reason') or 'No reason'}")

    print(f"\n📅 DATES:")
    print(f"  Last Contact: {proposal.get('last_contact_date') or 'NOT SET'}")
    print(f"  Days Since Contact: {proposal.get('days_since_contact') or 'N/A'}")
    print(f"  Contract Signed: {proposal.get('contract_signed_date') or 'NOT SET'}")
    print(f"  Created: {proposal.get('created_at') or 'NOT SET'}")
    print(f"  Updated: {proposal.get('updated_at') or 'NOT SET'}")

    print(f"\n🏗️ PROJECT TYPE:")
    print(f"  Landscape: {'YES' if proposal.get('is_landscape') else 'NO'}")
    print(f"  Architecture: {'YES' if proposal.get('is_architect') else 'NO'}")
    print(f"  Interior: {'YES' if proposal.get('is_interior') else 'NO'}")

    print(f"\n💬 NOTES:")
    print(f"  Status Notes: {proposal.get('status_notes') or 'NONE'}")
    print(f"  Phase: {proposal.get('project_phase') or 'NOT SET'}")

    # Get linked emails
    cursor.execute("""
        SELECT COUNT(*) FROM email_proposal_links
        WHERE proposal_id = ?
    """, (proposal['proposal_id'],))
    email_count = cursor.fetchone()[0]
    print(f"\n📧 LINKED EMAILS: {email_count}")

    # Get timeline entries (if table exists)
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM proposal_timeline
            WHERE proposal_id = ?
        """, (proposal['proposal_id'],))
        timeline_count = cursor.fetchone()[0]
        print(f"📜 TIMELINE ENTRIES: {timeline_count}")
    except:
        pass  # Table might not exist

    print("\n" + "=" * 80)

def show_project(conn, project):
    """Display a single project with all its details"""
    cursor = conn.cursor()

    print("=" * 80)
    print(f"PROJECT CODE: {project['project_code']}")
    print("=" * 80)

    print(f"\n📋 BASIC INFO:")
    print(f"  Title: {project['project_title']}")
    print(f"  Client ID: {project['client_id'] or 'NOT SET'}")
    print(f"  Country: {project['country'] or 'NOT SET'}")
    print(f"  Fee: ${project['total_fee_usd']:,.0f}" if project['total_fee_usd'] else "  Fee: NOT SET")

    print(f"\n📊 STATUS:")
    print(f"  Status: {project['status']}")
    print(f"  Type: {project['project_type'] or 'NOT SET'}")
    print(f"  Source: {project['source_db'] or 'UNKNOWN'}")

    print(f"\n📅 DATES:")
    print(f"  Created: {project['date_created'] or 'NOT SET'}")
    print(f"  Last Modified: {project['date_modified'] or 'NOT SET'}")

    print(f"\n💬 NOTES:")
    print(f"  {project['notes'] or 'NONE'}")

    # Check for invoices
    cursor.execute("""
        SELECT COUNT(*), SUM(CAST(invoice_amount AS REAL))
        FROM invoices
        WHERE project_code = ?
    """, (project['project_code'],))
    invoice_data = cursor.fetchone()
    invoice_count = invoice_data[0] or 0
    invoice_total = invoice_data[1] or 0
    print(f"\n💰 INVOICES: {invoice_count} invoices, ${invoice_total:,.2f} total")

    # Check for payments
    cursor.execute("""
        SELECT COUNT(*), SUM(CAST(payment_amount AS REAL))
        FROM payments
        WHERE project_code = ?
    """, (project['project_code'],))
    payment_data = cursor.fetchone()
    payment_count = payment_data[0] or 0
    payment_total = payment_data[1] or 0
    print(f"💳 PAYMENTS: {payment_count} payments, ${payment_total:,.2f} received")

    if invoice_total > 0 or payment_total > 0:
        balance = invoice_total - payment_total
        print(f"📊 BALANCE: ${balance:,.2f} {'OWED' if balance > 0 else 'OVERPAID' if balance < 0 else 'PAID IN FULL'}")

    print("\n" + "=" * 80)

def update_proposal(conn, project_code):
    """Interactive update for a proposal"""
    cursor = conn.cursor()

    print("\n🔧 UPDATE PROPOSAL")
    print("Leave blank to keep current value, type 'null' to clear\n")

    updates = {}

    # Status
    print("Status options: proposal, won, lost")
    new_status = input("New status: ").strip()
    if new_status:
        if new_status.lower() == 'null':
            updates['status'] = None
        else:
            updates['status'] = new_status

    # Client company
    new_client = input("Client company: ").strip()
    if new_client:
        updates['client_company'] = None if new_client.lower() == 'null' else new_client

    # Contact person
    new_contact_person = input("Contact person: ").strip()
    if new_contact_person:
        updates['contact_person'] = None if new_contact_person.lower() == 'null' else new_contact_person

    # Project value
    new_value = input("Project value (USD): ").strip()
    if new_value:
        if new_value.lower() == 'null':
            updates['project_value'] = None
        else:
            try:
                updates['project_value'] = float(new_value.replace(',', ''))
            except ValueError:
                print("Invalid value, skipping")

    # Last contact date
    new_contact = input("Last contact date (YYYY-MM-DD): ").strip()
    if new_contact:
        updates['last_contact_date'] = None if new_contact.lower() == 'null' else new_contact

    # Contract signed date
    new_signed = input("Contract signed date (YYYY-MM-DD): ").strip()
    if new_signed:
        updates['contract_signed_date'] = None if new_signed.lower() == 'null' else new_signed

    # Status notes
    new_notes = input("Status notes/remarks: ").strip()
    if new_notes:
        updates['status_notes'] = None if new_notes.lower() == 'null' else new_notes

    # On hold
    new_hold = input("On hold? (y/n): ").strip().lower()
    if new_hold in ['y', 'n']:
        updates['on_hold'] = 1 if new_hold == 'y' else 0
        if new_hold == 'y':
            hold_reason = input("On hold reason: ").strip()
            if hold_reason:
                updates['on_hold_reason'] = hold_reason

    # Is active project
    new_active = input("Is active project? (y/n): ").strip().lower()
    if new_active in ['y', 'n']:
        updates['is_active_project'] = 1 if new_active == 'y' else 0

    if not updates:
        print("No changes made.")
        return

    # Add provenance
    updates['updated_by'] = 'manual_audit_tool'
    updates['source_type'] = 'manual'
    updates['updated_at'] = datetime.now().isoformat()

    # Build UPDATE query
    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [project_code]

    cursor.execute(f"""
        UPDATE proposals
        SET {set_clause}
        WHERE project_code = ?
    """, values)

    conn.commit()
    print(f"\n✅ Updated {project_code} - {cursor.rowcount} row(s) affected")

def update_project(conn, project_code):
    """Interactive update for a project"""
    cursor = conn.cursor()

    print("\n🔧 UPDATE PROJECT")
    print("Leave blank to keep current value, type 'null' to clear\n")

    updates = {}

    # Status
    print("Status options: Active, Completed, Cancelled, On Hold")
    new_status = input("New status: ").strip()
    if new_status:
        updates['status'] = None if new_status.lower() == 'null' else new_status

    # Notes
    new_notes = input("Notes (e.g., 'Cancelled but client owes $50k'): ").strip()
    if new_notes:
        updates['notes'] = None if new_notes.lower() == 'null' else new_notes

    # Total fee
    new_fee = input("Total fee (USD): ").strip()
    if new_fee:
        if new_fee.lower() == 'null':
            updates['total_fee_usd'] = None
        else:
            try:
                updates['total_fee_usd'] = float(new_fee.replace(',', ''))
            except ValueError:
                print("Invalid value, skipping")

    # Country
    new_country = input("Country: ").strip()
    if new_country:
        updates['country'] = None if new_country.lower() == 'null' else new_country

    if not updates:
        print("No changes made.")
        return

    # Add metadata
    updates['date_modified'] = datetime.now().isoformat()

    # Build UPDATE query
    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [project_code]

    cursor.execute(f"""
        UPDATE projects
        SET {set_clause}
        WHERE project_code = ?
    """, values)

    conn.commit()
    print(f"\n✅ Updated {project_code} - {cursor.rowcount} row(s) affected")

def audit_proposals(conn):
    """Audit all proposals"""
    cursor = conn.cursor()

    # Get proposals grouped by status
    cursor.execute("""
        SELECT * FROM proposals
        ORDER BY
            CASE status
                WHEN 'proposal' THEN 1
                WHEN 'won' THEN 2
                WHEN 'lost' THEN 3
            END,
            project_code
    """)

    proposals = [dict(row) for row in cursor.fetchall()]

    print(f"\n📊 PROPOSALS AUDIT - {len(proposals)} total")
    print(f"  - proposal: {sum(1 for p in proposals if p['status'] == 'proposal')}")
    print(f"  - won: {sum(1 for p in proposals if p['status'] == 'won')}")
    print(f"  - lost: {sum(1 for p in proposals if p['status'] == 'lost')}")

    current_status = None
    for i, proposal in enumerate(proposals):
        # Show status header
        if proposal['status'] != current_status:
            current_status = proposal['status']
            print(f"\n\n{'='*80}")
            print(f"STATUS: {current_status.upper()}")
            print(f"{'='*80}")

        show_proposal(conn, proposal)

        print(f"\n[{i+1}/{len(proposals)}] Options:")
        print("  [Enter] = Next")
        print("  u = Update this proposal")
        print("  q = Quit audit")

        choice = input("\nChoice: ").strip().lower()

        if choice == 'q':
            break
        elif choice == 'u':
            update_proposal(conn, proposal['project_code'])
            # Reload proposal to show updates
            cursor.execute("SELECT * FROM proposals WHERE project_code = ?", (proposal['project_code'],))
            updated = dict(cursor.fetchone())
            show_proposal(conn, updated)
            input("\nPress Enter to continue...")

def audit_projects(conn):
    """Audit all projects"""
    cursor = conn.cursor()

    # Get projects grouped by status
    cursor.execute("""
        SELECT * FROM projects
        ORDER BY
            CASE status
                WHEN 'Active' THEN 1
                WHEN 'On Hold' THEN 2
                WHEN 'Completed' THEN 3
                WHEN 'Cancelled' THEN 4
            END,
            project_code
    """)

    projects = [dict(row) for row in cursor.fetchall()]

    print(f"\n📊 PROJECTS AUDIT - {len(projects)} total")
    print(f"  - Active: {sum(1 for p in projects if p['status'] == 'Active')}")
    print(f"  - Completed: {sum(1 for p in projects if p['status'] == 'Completed')}")
    print(f"  - Cancelled: {sum(1 for p in projects if p['status'] == 'Cancelled')}")
    print(f"  - Other: {sum(1 for p in projects if p['status'] not in ['Active', 'Completed', 'Cancelled'])}")

    current_status = None
    for i, project in enumerate(projects):
        # Show status header
        if project['status'] != current_status:
            current_status = project['status']
            print(f"\n\n{'='*80}")
            print(f"STATUS: {current_status.upper()}")
            print(f"{'='*80}")

        show_project(conn, project)

        print(f"\n[{i+1}/{len(projects)}] Options:")
        print("  [Enter] = Next")
        print("  u = Update this project")
        print("  q = Quit audit")

        choice = input("\nChoice: ").strip().lower()

        if choice == 'q':
            break
        elif choice == 'u':
            update_project(conn, project['project_code'])
            # Reload project to show updates
            cursor.execute("SELECT * FROM projects WHERE project_code = ?", (project['project_code'],))
            updated = dict(cursor.fetchone())
            show_project(conn, updated)
            input("\nPress Enter to continue...")

def export_to_csv(conn):
    """Export proposals and projects to CSV for Excel review"""
    import csv

    cursor = conn.cursor()

    # Export proposals
    print("\n📄 Exporting proposals to CSV...")
    cursor.execute("""
        SELECT
            project_code, project_name, client_company, country,
            project_value, status, is_active_project,
            first_contact_date, proposal_sent_date, contract_signed_date,
            current_remark, project_summary
        FROM proposals
        ORDER BY status, project_code
    """)

    with open('PROPOSALS_AUDIT.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Project Code', 'Project Name', 'Client', 'Country',
            'Value (USD)', 'Status', 'Is Active Project',
            'First Contact', 'Proposal Sent', 'Contract Signed',
            'Current Remark', 'Summary'
        ])
        writer.writerows(cursor.fetchall())

    print("✅ Created: PROPOSALS_AUDIT.csv")

    # Export projects
    print("\n📄 Exporting projects to CSV...")
    cursor.execute("""
        SELECT
            p.project_code, p.project_title, p.client_id, p.country,
            p.total_fee_usd, p.status, p.project_type, p.source_db,
            p.date_created, p.date_modified, p.notes,
            COALESCE(inv.invoice_count, 0) as invoice_count,
            COALESCE(inv.invoice_total, 0) as invoice_total,
            COALESCE(pay.payment_count, 0) as payment_count,
            COALESCE(pay.payment_total, 0) as payment_total
        FROM projects p
        LEFT JOIN (
            SELECT project_code,
                   COUNT(*) as invoice_count,
                   SUM(CAST(invoice_amount AS REAL)) as invoice_total
            FROM invoices GROUP BY project_code
        ) inv ON p.project_code = inv.project_code
        LEFT JOIN (
            SELECT project_code,
                   COUNT(*) as payment_count,
                   SUM(CAST(payment_amount AS REAL)) as payment_total
            FROM payments GROUP BY project_code
        ) pay ON p.project_code = pay.project_code
        ORDER BY status, project_code
    """)

    with open('PROJECTS_AUDIT.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Project Code', 'Title', 'Client ID', 'Country',
            'Fee (USD)', 'Status', 'Type', 'Source',
            'Created', 'Modified', 'Notes',
            'Invoice Count', 'Invoice Total', 'Payment Count', 'Payment Total'
        ])
        writer.writerows(cursor.fetchall())

    print("✅ Created: PROJECTS_AUDIT.csv")
    print("\nYou can open these files in Excel to review and edit, then import updates.")

def main():
    """Main audit menu"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    while True:
        clear_screen()
        print("=" * 80)
        print("BENSLEY DATABASE COMPREHENSIVE AUDIT TOOL")
        print("=" * 80)
        print("\nWhat would you like to audit?\n")
        print("  1. Proposals (87 records)")
        print("  2. Projects (46 records)")
        print("  3. Export to CSV (for Excel review)")
        print("  4. Exit")

        choice = input("\nChoice: ").strip()

        if choice == '1':
            audit_proposals(conn)
        elif choice == '2':
            audit_projects(conn)
        elif choice == '3':
            export_to_csv(conn)
            input("\nPress Enter to continue...")
        elif choice == '4':
            break
        else:
            print("Invalid choice")

    conn.close()
    print("\n✅ Audit complete!")

if __name__ == "__main__":
    main()
