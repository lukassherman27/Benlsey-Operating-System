#!/usr/bin/env python3
"""
Comprehensive Data Audit Tool
Shows ALL active projects, proposals, invoices, and fees
Highlights missing data that needs manual input
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import json

DB_PATH = Path(__file__).parent / "database" / "bensley_master.db"

def audit_active_projects():
    """Show all active projects with completeness metrics"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "="*100)
    print("ACTIVE PROJECTS AUDIT")
    print("="*100)

    cursor.execute("""
        SELECT
            p.project_code,
            p.project_title,
            p.total_fee_usd,
            p.status,
            p.team_lead,
            p.country,
            COUNT(DISTINCT i.invoice_number) as invoice_count,
            SUM(CASE WHEN i.status NOT IN ('paid', 'cancelled') THEN i.invoice_amount - COALESCE(i.payment_amount, 0) ELSE 0 END) as outstanding_amount,
            COUNT(DISTINCT pfb.breakdown_id) as fee_breakdown_count,
            p.notes
        FROM projects p
        LEFT JOIN invoices i ON p.project_code = i.project_code
        LEFT JOIN project_fee_breakdown pfb ON p.project_code = pfb.project_code
        WHERE p.is_active_project = 1
        GROUP BY p.project_code
        ORDER BY p.project_code
    """)

    projects = cursor.fetchall()

    print(f"\nTotal Active Projects: {len(projects)}\n")

    missing_data_projects = []

    for proj in projects:
        print(f"\n{'─'*100}")
        print(f"📋 {proj['project_code']} - {proj['project_title'] or '⚠️  MISSING TITLE'}")
        print(f"{'─'*100}")
        print(f"Status: {proj['status'] or 'N/A'}")
        print(f"Total Fee: ${proj['total_fee_usd']:,.2f}" if proj['total_fee_usd'] else "Total Fee: ⚠️  NOT SET")
        print(f"Team Lead: {proj['team_lead'] or '⚠️  NOT SET'}")
        print(f"Country: {proj['country'] or '⚠️  NOT SET'}")
        print(f"Invoices: {proj['invoice_count']} invoices")
        print(f"Outstanding: ${proj['outstanding_amount']:,.2f}" if proj['outstanding_amount'] else "Outstanding: $0.00")
        print(f"Fee Breakdown Records: {proj['fee_breakdown_count']}")

        # Flag missing data
        missing = []
        if not proj['project_title']:
            missing.append("Project Title")
        if not proj['total_fee_usd']:
            missing.append("Total Fee")
        if not proj['team_lead']:
            missing.append("Team Lead")
        if not proj['country']:
            missing.append("Country")
        if proj['invoice_count'] == 0:
            missing.append("Invoices")
        if proj['fee_breakdown_count'] == 0:
            missing.append("Fee Breakdown")

        if missing:
            print(f"\n🚨 MISSING DATA: {', '.join(missing)}")
            missing_data_projects.append({
                'project_code': proj['project_code'],
                'missing': missing
            })

        if proj['notes']:
            print(f"Notes: {proj['notes'][:100]}...")

    conn.close()
    return missing_data_projects


def audit_all_proposals():
    """Show all proposals with tracking status"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n\n" + "="*100)
    print("ALL PROPOSALS AUDIT")
    print("="*100)

    cursor.execute("""
        SELECT
            p.project_code,
            p.project_name,
            p.project_value,
            p.country,
            p.status,
            p.proposal_sent_date,
            p.contract_signed_date,
            p.is_landscape,
            p.is_architect,
            p.is_interior,
            pt.id as in_tracker,
            pt.current_status as tracker_status,
            pt.first_contact_date,
            pt.waiting_on,
            pt.next_steps
        FROM proposals p
        LEFT JOIN proposal_tracker pt ON p.project_code = pt.project_code
        ORDER BY p.project_code DESC
    """)

    proposals = cursor.fetchall()

    print(f"\nTotal Proposals: {len(proposals)}\n")

    missing_data = []

    for prop in proposals:
        print(f"\n{'─'*100}")
        print(f"📄 {prop['project_code']} - {prop['project_name'] or '⚠️  MISSING NAME'}")
        print(f"{'─'*100}")
        print(f"Value: ${prop['project_value']:,.2f}" if prop['project_value'] else "Value: ⚠️  NOT SET")
        print(f"Country: {prop['country'] or '⚠️  NOT SET'}")
        print(f"Status: {prop['status'] or 'N/A'}")

        # Disciplines
        disciplines = []
        if prop['is_landscape']:
            disciplines.append("Landscape")
        if prop['is_architect']:
            disciplines.append("Architecture")
        if prop['is_interior']:
            disciplines.append("Interior")
        print(f"Disciplines: {', '.join(disciplines) if disciplines else '⚠️  NOT SET'}")

        # Dates
        print(f"Proposal Sent: {prop['proposal_sent_date'] or '⚠️  NOT SET'}")
        print(f"Contract Signed: {prop['contract_signed_date'] or 'N/A'}")

        # Tracker status
        if prop['in_tracker']:
            print(f"✅ In Proposal Tracker")
            print(f"   Tracker Status: {prop['tracker_status']}")
            print(f"   First Contact: {prop['first_contact_date'] or 'NOT SET'}")
            if prop['waiting_on']:
                print(f"   Waiting On: {prop['waiting_on']}")
            if prop['next_steps']:
                print(f"   Next Steps: {prop['next_steps'][:80]}...")
        else:
            print(f"⚠️  NOT in Proposal Tracker")

        # Flag missing critical data
        missing = []
        if not prop['project_name']:
            missing.append("Project Name")
        if not prop['project_value']:
            missing.append("Project Value")
        if not prop['country']:
            missing.append("Country")
        if not any([prop['is_landscape'], prop['is_architect'], prop['is_interior']]):
            missing.append("Disciplines")
        if prop['status'] == 'won' and not prop['contract_signed_date']:
            missing.append("Contract Signed Date")

        if missing:
            print(f"\n🚨 MISSING DATA: {', '.join(missing)}")
            missing_data.append({
                'project_code': prop['project_code'],
                'missing': missing
            })

    conn.close()
    return missing_data


def audit_invoices_per_project():
    """Show all invoices grouped by project"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n\n" + "="*100)
    print("INVOICES PER PROJECT AUDIT")
    print("="*100)

    cursor.execute("""
        SELECT
            i.project_code,
            p.project_title,
            i.invoice_number,
            i.invoice_date,
            i.invoice_amount,
            COALESCE(i.payment_amount, 0) as payment_amount,
            (i.invoice_amount - COALESCE(i.payment_amount, 0)) as outstanding,
            i.status,
            CAST(JULIANDAY('now') - JULIANDAY(i.invoice_date) AS INTEGER) as days_outstanding,
            pfb.phase as phase_name,
            pfb.discipline
        FROM invoices i
        LEFT JOIN projects p ON i.project_code = p.project_code
        LEFT JOIN project_fee_breakdown pfb ON i.project_code = pfb.project_code AND i.phase_id = pfb.breakdown_id
        ORDER BY i.project_code, i.invoice_date
    """)

    invoices = cursor.fetchall()

    # Group by project
    by_project = {}
    for inv in invoices:
        code = inv['project_code']
        if code not in by_project:
            by_project[code] = {
                'project_title': inv['project_title'],
                'invoices': []
            }
        by_project[code]['invoices'].append(inv)

    print(f"\nProjects with Invoices: {len(by_project)}")
    print(f"Total Invoices: {len(invoices)}\n")

    missing_phase_data = []

    for code, data in by_project.items():
        print(f"\n{'─'*100}")
        print(f"💰 {code} - {data['project_title'] or '⚠️  MISSING TITLE'}")
        print(f"{'─'*100}")
        print(f"Total Invoices: {len(data['invoices'])}\n")

        total_invoiced = sum(inv['invoice_amount'] for inv in data['invoices'])
        total_paid = sum(inv['payment_amount'] for inv in data['invoices'])
        total_outstanding = sum(inv['outstanding'] for inv in data['invoices'] if inv['outstanding'] > 0)

        print(f"Total Invoiced: ${total_invoiced:,.2f}")
        print(f"Total Paid: ${total_paid:,.2f}")
        print(f"Total Outstanding: ${total_outstanding:,.2f}\n")

        # List each invoice
        for inv in data['invoices']:
            status_emoji = "✅" if inv['status'] == 'paid' else "⏳" if inv['outstanding'] > 0 else "❓"
            print(f"  {status_emoji} {inv['invoice_number']}")
            print(f"     Date: {inv['invoice_date']}")
            print(f"     Amount: ${inv['invoice_amount']:,.2f}")
            print(f"     Paid: ${inv['payment_amount']:,.2f}")
            print(f"     Outstanding: ${inv['outstanding']:,.2f}")
            print(f"     Status: {inv['status']}")

            if inv['outstanding'] > 0:
                print(f"     Days Outstanding: {inv['days_outstanding']} days")

            if inv['phase_name']:
                print(f"     Phase: {inv['phase_name']}")
            else:
                print(f"     Phase: ⚠️  NOT LINKED TO PHASE")
                missing_phase_data.append(inv['invoice_number'])

            if inv['discipline']:
                print(f"     Discipline: {inv['discipline']}")
            else:
                print(f"     Discipline: ⚠️  NOT SET")
            print()

    conn.close()
    return missing_phase_data


def audit_fee_breakdown():
    """Show fee breakdown completeness per project"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n\n" + "="*100)
    print("FEE BREAKDOWN / SCOPE AUDIT")
    print("="*100)

    cursor.execute("""
        SELECT
            pfb.project_code,
            p.project_title,
            pfb.discipline,
            pfb.phase,
            pfb.phase_fee_usd,
            pfb.total_invoiced,
            pfb.percentage_invoiced,
            pfb.total_paid,
            pfb.percentage_paid,
            (pfb.phase_fee_usd - COALESCE(pfb.total_invoiced, 0)) as remaining
        FROM project_fee_breakdown pfb
        LEFT JOIN projects p ON pfb.project_code = p.project_code
        ORDER BY pfb.project_code, pfb.discipline, pfb.phase
    """)

    breakdowns = cursor.fetchall()

    # Group by project
    by_project = {}
    for bd in breakdowns:
        code = bd['project_code']
        if code not in by_project:
            by_project[code] = {
                'project_title': bd['project_title'],
                'breakdowns': []
            }
        by_project[code]['breakdowns'].append(bd)

    print(f"\nProjects with Fee Breakdowns: {len(by_project)}")
    print(f"Total Fee Breakdown Records: {len(breakdowns)}\n")

    for code, data in by_project.items():
        print(f"\n{'─'*100}")
        print(f"💵 {code} - {data['project_title'] or '⚠️  MISSING TITLE'}")
        print(f"{'─'*100}")

        # Group by discipline
        by_discipline = {}
        for bd in data['breakdowns']:
            disc = bd['discipline'] or 'Unknown'
            if disc not in by_discipline:
                by_discipline[disc] = []
            by_discipline[disc].append(bd)

        for disc, phases in by_discipline.items():
            print(f"\n  📐 {disc}")
            total_fee = sum(ph['phase_fee_usd'] or 0 for ph in phases)
            total_invoiced = sum(ph['total_invoiced'] or 0 for ph in phases)
            total_remaining = sum(ph['remaining'] or 0 for ph in phases)

            print(f"     Total Fee: ${total_fee:,.2f}")
            print(f"     Invoiced: ${total_invoiced:,.2f}")
            print(f"     Remaining: ${total_remaining:,.2f}")
            print(f"     Phases: {len(phases)}\n")

            for ph in phases:
                pct_invoiced = ph['percentage_invoiced'] or 0
                pct_paid = ph['percentage_paid'] or 0
                print(f"       • {ph['phase']}")
                print(f"         Fee: ${ph['phase_fee_usd']:,.2f}" if ph['phase_fee_usd'] else "         Fee: ⚠️  NOT SET")
                print(f"         Invoiced: ${ph['total_invoiced']:,.2f}" if ph['total_invoiced'] else "         Invoiced: $0.00")
                print(f"         Paid: ${ph['total_paid']:,.2f}" if ph['total_paid'] else "         Paid: $0.00")
                print(f"         Remaining: ${ph['remaining']:,.2f}" if ph['remaining'] else "         Remaining: ⚠️  NOT CALCULATED")
                print(f"         % Invoiced: {pct_invoiced:.1f}% | % Paid: {pct_paid:.1f}%")

    conn.close()


def generate_summary_report(missing_projects, missing_proposals, missing_phases):
    """Generate summary of all missing data"""
    print("\n\n" + "="*100)
    print("📊 SUMMARY - DATA GAPS REQUIRING MANUAL INPUT")
    print("="*100)

    print("\n🚨 ACTIVE PROJECTS WITH MISSING DATA:")
    if missing_projects:
        for proj in missing_projects:
            print(f"   • {proj['project_code']}: {', '.join(proj['missing'])}")
    else:
        print("   ✅ All active projects have complete data!")

    print("\n🚨 PROPOSALS WITH MISSING DATA:")
    if missing_proposals:
        for prop in missing_proposals:
            print(f"   • {prop['project_code']}: {', '.join(prop['missing'])}")
    else:
        print("   ✅ All proposals have complete data!")

    print("\n🚨 INVOICES WITHOUT PHASE/DISCIPLINE:")
    if missing_phases:
        print(f"   • {len(missing_phases)} invoices not linked to phases")
        print(f"   • Invoice numbers: {', '.join(missing_phases[:10])}")
        if len(missing_phases) > 10:
            print(f"   • ... and {len(missing_phases) - 10} more")
    else:
        print("   ✅ All invoices properly linked to phases!")

    print("\n" + "="*100)
    print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)


def main():
    """Run complete audit"""
    print("\n🔍 COMPREHENSIVE DATA AUDIT")
    print(f"Database: {DB_PATH}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    missing_projects = audit_active_projects()
    missing_proposals = audit_all_proposals()
    missing_phases = audit_invoices_per_project()
    audit_fee_breakdown()
    generate_summary_report(missing_projects, missing_proposals, missing_phases)

    print("\n\n💡 NEXT STEPS:")
    print("1. Review missing data flagged above")
    print("2. Gather missing information from finance team, contracts, emails")
    print("3. Use manual import scripts to add missing data")
    print("4. Re-run this audit to verify completeness\n")


if __name__ == "__main__":
    main()
