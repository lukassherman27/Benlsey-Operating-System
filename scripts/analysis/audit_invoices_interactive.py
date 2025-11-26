#!/usr/bin/env python3
"""
Interactive Invoice Audit Tool
Allows manual verification and correction of invoice-project linkages
"""

import sqlite3
from datetime import datetime
import json

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
PROGRESS_FILE = "invoice_audit_progress.json"


def load_progress():
    """Load audit progress from file"""
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_invoice_id": None, "audited_count": 0, "corrections": []}


def save_progress(progress):
    """Save audit progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def get_invoice_details(conn, invoice_id):
    """Get detailed information about an invoice"""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            i.invoice_id,
            i.invoice_number,
            i.invoice_date,
            i.payment_date,
            i.invoice_amount,
            i.payment_amount,
            i.project_id,
            i.project_code,
            i.phase,
            i.discipline,
            i.description,
            i.status,
            p.project_name,
            p.total_fee_usd
        FROM invoices i
        LEFT JOIN projects p ON i.project_code = p.project_code
        WHERE i.invoice_id = ?
    """, (invoice_id,))

    return cursor.fetchone()


def get_all_projects(conn):
    """Get list of all active projects for selection"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_code, project_name, total_fee_usd, status
        FROM projects
        WHERE status IN ('active', 'proposal')
        ORDER BY project_code
    """)
    return cursor.fetchall()


def get_phase_breakdown(conn, project_code):
    """Get fee breakdown for a project to calculate percentages"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT phase, phase_fee_usd, percentage_of_total
        FROM project_fee_breakdown
        WHERE project_code = ?
        ORDER BY breakdown_id
    """, (project_code,))
    return cursor.fetchall()


def update_invoice(conn, invoice_id, project_code, phase, discipline=None):
    """Update invoice with corrected information"""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE invoices
        SET project_code = ?,
            phase = ?,
            discipline = ?,
            updated_at = ?
        WHERE invoice_id = ?
    """, (project_code, phase, discipline, datetime.now().isoformat(), invoice_id))
    conn.commit()


def display_invoice(invoice_data, phases=None):
    """Display invoice details in a readable format"""
    if not invoice_data:
        return

    (invoice_id, invoice_number, invoice_date, payment_date, invoice_amount,
     payment_amount, project_id, project_code, phase, discipline, description,
     status, project_name, total_fee) = invoice_data

    print("\n" + "=" * 100)
    print(f"INVOICE #{invoice_id}")
    print("=" * 100)

    print(f"\n📄 Invoice Details:")
    print(f"   Invoice Number:  {invoice_number or 'N/A'}")
    print(f"   Invoice Date:    {invoice_date or 'N/A'}")
    print(f"   Payment Date:    {payment_date or 'NOT PAID'}")
    print(f"   Invoice Amount:  ${invoice_amount:,.2f}" if invoice_amount else "   Invoice Amount:  N/A")
    print(f"   Payment Amount:  ${payment_amount:,.2f}" if payment_amount else "   Payment Amount:  N/A")
    print(f"   Status:          {status or 'N/A'}")

    print(f"\n🏗️  Current Linkage:")
    print(f"   Old Project ID:  {project_id}")
    print(f"   Project Code:    {project_code or 'NOT LINKED'}")
    print(f"   Project Name:    {project_name or 'N/A'}")
    print(f"   Phase:           {phase or 'N/A'}")
    print(f"   Discipline:      {discipline or 'N/A'}")

    print(f"\n📝 Description:")
    print(f"   {description or 'No description'}")

    if phases and invoice_amount and project_code:
        print(f"\n💰 Phase Breakdown for {project_code}:")
        for p_phase, p_fee, p_pct in phases:
            if invoice_amount and p_fee:
                pct_of_phase = (invoice_amount / p_fee) * 100 if p_fee > 0 else 0
                match = "✓" if p_phase == phase else " "
                print(f"   {match} {p_phase:15s}: ${p_fee:>10,.2f} ({p_pct*100:>5.1f}% of total) - This invoice: {pct_of_phase:>5.1f}%")
            else:
                match = "✓" if p_phase == phase else " "
                print(f"   {match} {p_phase:15s}: ${p_fee:>10,.2f} ({p_pct*100:>5.1f}% of total)")


def main():
    """Main interactive audit loop"""
    conn = sqlite3.connect(DB_PATH)
    progress = load_progress()

    print("\n" + "=" * 100)
    print("INVOICE AUDIT TOOL")
    print("=" * 100)
    print(f"\nProgress: {progress['audited_count']} invoices audited")
    print(f"Last invoice: {progress['last_invoice_id']}")

    # Get all invoices to audit
    cursor = conn.cursor()
    if progress['last_invoice_id']:
        cursor.execute("""
            SELECT invoice_id FROM invoices
            WHERE invoice_id > ?
            ORDER BY invoice_id
        """, (progress['last_invoice_id'],))
    else:
        cursor.execute("SELECT invoice_id FROM invoices ORDER BY invoice_id")

    invoice_ids = [row[0] for row in cursor.fetchall()]
    total_invoices = len(invoice_ids)

    print(f"\nRemaining invoices to audit: {total_invoices}")

    if total_invoices == 0:
        print("\n✅ All invoices have been audited!")
        conn.close()
        return

    print("\nCommands:")
    print("  [Enter]     - Confirm current linkage is correct")
    print("  c <code>    - Change project code (e.g., 'c 25 BK-030')")
    print("  p <phase>   - Change phase (e.g., 'p mobilization')")
    print("  d <disc>    - Change discipline (e.g., 'd Landscape')")
    print("  both        - Change both project and phase")
    print("  skip        - Skip this invoice")
    print("  quit        - Save progress and quit")
    print("  list        - Show available projects")

    for idx, invoice_id in enumerate(invoice_ids, 1):
        # Get invoice details
        invoice_data = get_invoice_details(conn, invoice_id)
        if not invoice_data:
            continue

        project_code = invoice_data[7]

        # Get phase breakdown if project is linked
        phases = None
        if project_code:
            phases = get_phase_breakdown(conn, project_code)

        # Display invoice
        display_invoice(invoice_data, phases)

        print(f"\n[{idx}/{total_invoices}] ")
        command = input("Action: ").strip().lower()

        if command == "quit":
            print("\n💾 Saving progress...")
            progress['last_invoice_id'] = invoice_id
            save_progress(progress)
            print(f"✅ Progress saved. {progress['audited_count']} invoices audited.")
            break

        elif command == "skip":
            print("⏭️  Skipped")
            continue

        elif command == "list":
            print("\n📋 Available Projects:")
            projects = get_all_projects(conn)
            for proj_code, proj_name, fee, status in projects[:30]:
                print(f"   {proj_code:15s} | {proj_name:50s} | ${fee:>12,.2f} | {status}")
            print(f"   ... (showing first 30)")
            # Re-display the current invoice
            display_invoice(invoice_data, phases)
            command = input("\nAction: ").strip().lower()

        if command.startswith("c "):
            # Change project code
            new_code = command[2:].strip().upper()
            update_invoice(conn, invoice_id, new_code, invoice_data[8], invoice_data[9])
            print(f"✅ Updated project code to: {new_code}")
            progress['corrections'].append({
                "invoice_id": invoice_id,
                "old_code": project_code,
                "new_code": new_code,
                "timestamp": datetime.now().isoformat()
            })

        elif command.startswith("p "):
            # Change phase
            new_phase = command[2:].strip().lower()
            update_invoice(conn, invoice_id, project_code, new_phase, invoice_data[9])
            print(f"✅ Updated phase to: {new_phase}")

        elif command.startswith("d "):
            # Change discipline
            new_discipline = command[2:].strip()
            update_invoice(conn, invoice_id, project_code, invoice_data[8], new_discipline)
            print(f"✅ Updated discipline to: {new_discipline}")

        elif command == "both":
            new_code = input("  New project code: ").strip().upper()
            new_phase = input("  New phase: ").strip().lower()
            new_disc = input("  New discipline (or Enter to skip): ").strip()
            update_invoice(conn, invoice_id, new_code, new_phase, new_disc if new_disc else invoice_data[9])
            print(f"✅ Updated to: {new_code} / {new_phase}" + (f" / {new_disc}" if new_disc else ""))
            progress['corrections'].append({
                "invoice_id": invoice_id,
                "old_code": project_code,
                "new_code": new_code,
                "new_phase": new_phase,
                "timestamp": datetime.now().isoformat()
            })

        elif command == "" or command == "ok":
            # Confirmed correct
            print("✓ Confirmed")

        progress['audited_count'] += 1
        progress['last_invoice_id'] = invoice_id

        # Auto-save every 10 invoices
        if progress['audited_count'] % 10 == 0:
            save_progress(progress)
            print(f"\n💾 Auto-saved progress ({progress['audited_count']} audited)")

    # Final save
    save_progress(progress)
    conn.close()

    print("\n" + "=" * 100)
    print(f"✅ AUDIT COMPLETE")
    print(f"   Total audited: {progress['audited_count']}")
    print(f"   Corrections made: {len(progress['corrections'])}")
    print("=" * 100)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Progress auto-saved.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
