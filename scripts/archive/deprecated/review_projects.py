#!/usr/bin/env python3
"""
Comprehensive Project Review Tool
For reviewing all projects with your dad - see invoices, delete duplicates, add context
"""
import sqlite3
from datetime import datetime

DB_PATH = "database/bensley_master.db"

def format_currency(amount):
    if amount is None or amount == 0:
        return "$0"
    return f"${amount:,.2f}"

def get_project_details(cursor, project_id):
    """Get full project details including invoices"""
    cursor.execute("""
        SELECT
            p.project_code,
            p.project_title,
            p.project_type,
            p.total_fee_usd,
            p.status,
            p.project_stage,
            p.notes,
            p.date_created
        FROM projects p
        WHERE p.project_id = ?
    """, (project_id,))

    return cursor.fetchone()

def get_project_invoices(cursor, project_id):
    """Get all invoices for a project"""
    cursor.execute("""
        SELECT
            invoice_number,
            invoice_date,
            invoice_amount,
            payment_amount,
            status
        FROM invoices
        WHERE project_id = ?
        ORDER BY invoice_date
    """, (project_id,))

    return cursor.fetchall()

def show_project(proj_id, code, title, proj_type, fee, status, stage, notes, created, invoice_count, total_invoiced, total_paid):
    """Display project details"""
    print(f"\n{'='*100}")
    print(f"PROJECT: {code} - {title}")
    print(f"{'='*100}")
    print(f"Type: {proj_type or 'N/A'}")
    print(f"Contract Fee: {format_currency(fee)}")
    print(f"Status: {status} | Stage: {stage or 'UNCLASSIFIED'}")
    print(f"Created: {created or 'Unknown'}")

    if notes:
        print(f"\nNotes: {notes}")

    print(f"\n{'─'*100}")
    print(f"INVOICES: {invoice_count} invoices")
    if invoice_count > 0:
        print(f"  Total Invoiced: {format_currency(total_invoiced)}")
        print(f"  Total Paid: {format_currency(total_paid)}")
        print(f"  Outstanding: {format_currency(total_invoiced - total_paid)}")
    print(f"{'─'*100}")

def show_invoices(invoices):
    """Display invoice details"""
    if not invoices:
        print("\n  No invoices attached")
        return

    print("\n  Invoice Details:")
    for inv_num, inv_date, inv_amt, paid_amt, inv_status in invoices:
        outstanding = (inv_amt or 0) - (paid_amt or 0)
        print(f"    • {inv_num} | {inv_date or 'No date'} | "
              f"Invoice: {format_currency(inv_amt)} | "
              f"Paid: {format_currency(paid_amt)} | "
              f"Outstanding: {format_currency(outstanding)} | "
              f"Status: {inv_status}")

def review_projects():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all projects
    cursor.execute("""
        SELECT
            p.project_id,
            p.project_code,
            p.project_title,
            p.project_type,
            p.total_fee_usd,
            p.status,
            p.project_stage,
            p.notes,
            p.date_created,
            COUNT(i.invoice_id) as invoice_count,
            COALESCE(SUM(i.invoice_amount), 0) as total_invoiced,
            COALESCE(SUM(i.payment_amount), 0) as total_paid
        FROM projects p
        LEFT JOIN invoices i ON p.project_id = i.project_id
        WHERE p.status = 'Active'
        GROUP BY p.project_id
        ORDER BY p.total_fee_usd DESC NULLS LAST, p.project_code
    """)

    projects = cursor.fetchall()
    total_projects = len(projects)

    print("=" * 100)
    print("COMPREHENSIVE PROJECT REVIEW TOOL")
    print("=" * 100)
    print(f"\nTotal projects to review: {total_projects}")
    print("\nActions:")
    print("  P = Mark as PROPOSAL (pipeline)")
    print("  A = Mark as ACTIVE CONTRACT")
    print("  C = Mark as CANCELLED")
    print("  X = Mark as ARCHIVED/COMPLETED")
    print("  N = Add/Edit NOTES")
    print("  D = DELETE this project")
    print("  I = Show detailed INVOICE list")
    print("  F = FLAG for missing invoices")
    print("  S = SKIP (next project)")
    print("  Q = QUIT and save")
    print("=" * 100)

    idx = 0
    while idx < total_projects:
        proj = projects[idx]
        proj_id, code, title, proj_type, fee, status, stage, notes, created, inv_count, total_inv, total_paid = proj

        # Show project
        show_project(proj_id, code, title, proj_type, fee, status, stage, notes, created,
                    inv_count, total_inv, total_paid)

        # Show invoice summary
        if inv_count > 0:
            invoices = get_project_invoices(cursor, proj_id)
            print(f"\n  {len(invoices)} invoice(s) - type 'I' to see details")

        print(f"\n[{idx + 1}/{total_projects}]")
        choice = input("Action (P/A/C/X/N/D/I/F/S/Q): ").strip().upper()

        if choice == 'Q':
            print("\n💾 Saving and quitting...")
            break

        elif choice == 'S':
            print("→ Skipped")
            idx += 1

        elif choice == 'P':
            cursor.execute("UPDATE projects SET project_stage = 'proposal' WHERE project_id = ?", (proj_id,))
            print("→ Marked as PROPOSAL")
            conn.commit()
            idx += 1

        elif choice == 'A':
            cursor.execute("UPDATE projects SET project_stage = 'active_contract' WHERE project_id = ?", (proj_id,))
            print("→ Marked as ACTIVE CONTRACT")
            conn.commit()
            idx += 1

        elif choice == 'C':
            cursor.execute("UPDATE projects SET project_stage = 'archived', status = 'Cancelled' WHERE project_id = ?", (proj_id,))
            print("→ Marked as CANCELLED")
            conn.commit()
            idx += 1

        elif choice == 'X':
            cursor.execute("UPDATE projects SET project_stage = 'archived', status = 'Completed' WHERE project_id = ?", (proj_id,))
            print("→ Marked as ARCHIVED/COMPLETED")
            conn.commit()
            idx += 1

        elif choice == 'N':
            print(f"\nCurrent notes: {notes or '(none)'}")
            new_notes = input("Enter new notes (or press Enter to keep current): ").strip()
            if new_notes:
                cursor.execute("UPDATE projects SET notes = ? WHERE project_id = ?", (new_notes, proj_id))
                print("→ Notes updated")
                conn.commit()
            idx += 1

        elif choice == 'D':
            confirm = input(f"⚠️  DELETE project {code}? This will also delete {inv_count} invoices! (yes/no): ").strip().lower()
            if confirm == 'yes':
                cursor.execute("DELETE FROM invoices WHERE project_id = ?", (proj_id,))
                cursor.execute("DELETE FROM projects WHERE project_id = ?", (proj_id,))
                print(f"→ DELETED project {code} and {inv_count} invoices")
                conn.commit()
                projects.pop(idx)  # Remove from list
                total_projects -= 1
            else:
                print("→ Deletion cancelled")

        elif choice == 'I':
            invoices = get_project_invoices(cursor, proj_id)
            show_invoices(invoices)
            input("\nPress Enter to continue...")

        elif choice == 'F':
            flag_note = f"[FLAGGED {datetime.now().strftime('%Y-%m-%d')}] Missing invoices - needs completion"
            current_notes = notes or ""
            updated_notes = f"{current_notes}\n{flag_note}".strip()
            cursor.execute("UPDATE projects SET notes = ? WHERE project_id = ?", (updated_notes, proj_id))
            print("→ FLAGGED for missing invoices")
            conn.commit()
            idx += 1

        else:
            print("Invalid choice. Try again.")

        # Auto-save every 5 projects
        if (idx + 1) % 5 == 0:
            conn.commit()
            print(f"\n💾 Auto-saved progress ({idx + 1}/{total_projects})")

    # Final summary
    cursor.execute("""
        SELECT
            project_stage,
            COUNT(*) as count,
            COALESCE(SUM(total_fee_usd), 0) as total_value
        FROM projects
        WHERE status IN ('Active', 'Completed', 'Cancelled')
        GROUP BY project_stage
    """)

    print("\n" + "=" * 100)
    print("FINAL SUMMARY")
    print("=" * 100)
    for stage, count, value in cursor.fetchall():
        stage_name = stage or "unclassified"
        print(f"{stage_name:20} {count:4} projects  {format_currency(value)}")

    conn.close()
    print("\n✅ Review complete!\n")

if __name__ == '__main__':
    review_projects()
