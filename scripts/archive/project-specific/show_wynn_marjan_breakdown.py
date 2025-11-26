#!/usr/bin/env python3
"""
Show complete financial breakdown for Wynn Marjan project
"""
import sqlite3

DB_PATH = "database/bensley_master.db"
PROJECT_CODE = "22 BK-095"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get project info
    cursor.execute("""
        SELECT project_code, project_title, total_fee_usd, country, city
        FROM projects
        WHERE project_code = ?
    """, (PROJECT_CODE,))

    project = cursor.fetchone()
    if not project:
        print(f"❌ Project {PROJECT_CODE} not found!")
        return

    project_code, title, total_fee, country, city = project

    print("=" * 100)
    print(f"WYNN MARJAN FINANCIAL BREAKDOWN")
    print("=" * 100)
    print(f"\n📋 Project: {project_code} - {title}")
    print(f"   Location: {city}, {country}")
    print(f"   Total Contract Value: ${total_fee:,.2f}\n")

    # Get all breakdowns grouped by scope
    cursor.execute("""
        SELECT scope, discipline, phase, phase_fee_usd, percentage_of_total, breakdown_id
        FROM project_fee_breakdown
        WHERE project_code = ?
        ORDER BY
            CASE scope
                WHEN 'indian-brasserie' THEN 1
                WHEN 'mediterranean-restaurant' THEN 2
                WHEN 'day-club' THEN 3
                WHEN 'night-club' THEN 4
                ELSE 5
            END,
            CASE phase
                WHEN 'Mobilization' THEN 1
                WHEN 'Conceptual Design' THEN 2
                WHEN 'Design Development' THEN 3
                WHEN 'Construction Documents' THEN 4
                WHEN 'Construction Observation' THEN 5
                ELSE 6
            END
    """, (PROJECT_CODE,))

    breakdowns = cursor.fetchall()

    if not breakdowns:
        print("⚠️  No fee breakdowns found!\n")
    else:
        print(f"💰 FEE BREAKDOWN BY SCOPE ({len(breakdowns)} total breakdowns):\n")

        current_scope = None
        scope_total = 0

        for scope, discipline, phase, fee, percentage, breakdown_id in breakdowns:
            # New scope - print header
            if scope != current_scope:
                if current_scope:
                    print(f"      Scope Total: ${scope_total:,.2f}\n")

                scope_total = 0
                current_scope = scope

                scope_names = {
                    'indian-brasserie': 'Indian Brasserie at Casino Level',
                    'mediterranean-restaurant': 'Modern Mediterranean Restaurant on Casino Level',
                    'day-club': 'Day Club on B2 Level',
                    'night-club': 'Interior Design for Night Club'
                }

                print(f"   📍 {scope_names.get(scope, scope.upper())}")
                print(f"      Discipline(s): {discipline}")
                print()

            print(f"      • {phase:30} ${fee:>12,.2f}  ({percentage:>5.1f}%)")
            scope_total += fee

        # Print last scope total
        if current_scope:
            print(f"      Scope Total: ${scope_total:,.2f}\n")

    # Get all invoices
    cursor.execute("""
        SELECT
            i.invoice_number,
            i.description,
            i.invoice_date,
            i.invoice_amount,
            i.payment_date,
            i.payment_amount,
            i.status,
            i.breakdown_id,
            pfb.scope,
            pfb.discipline,
            pfb.phase
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        LEFT JOIN project_fee_breakdown pfb ON i.breakdown_id = pfb.breakdown_id
        WHERE p.project_code = ?
        ORDER BY i.invoice_date, i.invoice_number
    """, (PROJECT_CODE,))

    invoices = cursor.fetchall()

    print(f"📄 INVOICES ({len(invoices)} total):\n")

    if not invoices:
        print("   No invoices found\n")
    else:
        total_invoiced = 0
        total_paid = 0
        linked_count = 0
        unlinked_count = 0

        for inv_num, desc, inv_date, inv_amt, pay_date, pay_amt, status, breakdown_id, scope, discipline, phase in invoices:
            total_invoiced += inv_amt or 0
            total_paid += pay_amt or 0

            if breakdown_id:
                linked_count += 1
                link_status = f"✅ Linked: {scope}/{discipline}/{phase}" if scope else f"✅ Linked: {breakdown_id}"
            else:
                unlinked_count += 1
                link_status = "❌ UNLINKED"

            print(f"   {inv_num:12} | {inv_date:10} | ${inv_amt:>12,.2f} | {status:12} | {link_status}")
            if desc and desc.strip():
                print(f"                Description: {desc}")

        print(f"\n   {'─' * 95}")
        print(f"   Total Invoiced:  ${total_invoiced:>12,.2f}")
        print(f"   Total Paid:      ${total_paid:>12,.2f}")
        print(f"   Outstanding:     ${total_invoiced - total_paid:>12,.2f}")
        print()
        print(f"   Linked:   {linked_count}/{len(invoices)} ({100*linked_count/len(invoices):.1f}%)")
        print(f"   Unlinked: {unlinked_count}/{len(invoices)}")

    # Overall invoice linking status
    print("\n" + "=" * 100)
    print("OVERALL SYSTEM STATUS")
    print("=" * 100)

    cursor.execute("SELECT COUNT(*) FROM invoices WHERE breakdown_id IS NOT NULL AND breakdown_id != ''")
    total_linked = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices")
    total_invoices = cursor.fetchone()[0]

    print(f"\nTotal invoices in system: {total_invoices}")
    print(f"Linked to breakdown: {total_linked} ({100*total_linked/total_invoices:.1f}%)")
    print(f"Still unlinked: {total_invoices - total_linked}")

    conn.close()

if __name__ == "__main__":
    main()
