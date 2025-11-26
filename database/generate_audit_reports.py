#!/usr/bin/env python3
"""
Generate CSV audit reports for proposals and projects
"""

import sqlite3
import csv

DB_PATH = "bensley_master.db"

def generate_reports():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("📊 BENSLEY DATABASE AUDIT REPORTS")
    print("=" * 80)

    # PROPOSALS REPORT
    print("\n📄 Generating PROPOSALS audit report...")

    cursor.execute("""
        SELECT
            p.project_code,
            p.project_name,
            p.client_company,
            p.country,
            p.project_value,
            p.status,
            p.is_active_project,
            p.first_contact_date,
            p.proposal_sent_date,
            p.contract_signed_date,
            p.current_remark,
            p.project_summary,
            p.is_landscape,
            p.is_architect,
            p.is_interior,
            (SELECT COUNT(*) FROM email_proposal_links WHERE project_code = p.project_code) as email_count
        FROM proposals p
        ORDER BY
            CASE p.status
                WHEN 'proposal' THEN 1
                WHEN 'won' THEN 2
                WHEN 'lost' THEN 3
            END,
            p.project_code
    """)

    proposals = cursor.fetchall()

    with open('PROPOSALS_AUDIT.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Project Code', 'Project Name', 'Client Company', 'Country',
            'Value (USD)', 'Status', 'Is Active Project',
            'First Contact Date', 'Proposal Sent Date', 'Contract Signed Date',
            'Current Remark', 'Project Summary',
            'Landscape', 'Architecture', 'Interior', 'Linked Emails'
        ])
        writer.writerows(proposals)

    # Summary stats
    status_counts = {}
    for p in proposals:
        status = p[5]  # status column
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"✅ PROPOSALS_AUDIT.csv created - {len(proposals)} proposals")
    for status, count in status_counts.items():
        print(f"   - {status}: {count}")

    # PROJECTS REPORT
    print("\n📄 Generating PROJECTS audit report...")

    cursor.execute("""
        SELECT
            p.project_code,
            p.project_title,
            p.client_id,
            p.country,
            p.total_fee_usd,
            p.status,
            p.project_type,
            p.source_db,
            p.date_created,
            p.date_modified,
            p.notes,
            COALESCE(inv.invoice_count, 0) as invoice_count,
            COALESCE(inv.invoice_total, 0) as invoice_total,
            COALESCE(pay.payment_count, 0) as payment_count,
            COALESCE(pay.payment_total, 0) as payment_total,
            COALESCE(inv.invoice_total, 0) - COALESCE(pay.payment_total, 0) as balance
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
        ORDER BY
            CASE p.status
                WHEN 'Active' THEN 1
                WHEN 'On Hold' THEN 2
                WHEN 'Completed' THEN 3
                WHEN 'Cancelled' THEN 4
            END,
            p.project_code
    """)

    projects = cursor.fetchall()

    with open('PROJECTS_AUDIT.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Project Code', 'Title', 'Client ID', 'Country',
            'Fee (USD)', 'Status', 'Type', 'Source DB',
            'Date Created', 'Date Modified', 'Notes',
            'Invoice Count', 'Invoice Total', 'Payment Count', 'Payment Total', 'Balance Owed'
        ])
        writer.writerows(projects)

    # Summary stats
    status_counts = {}
    for p in projects:
        status = p[5]  # status column
        status_counts[status] = status_counts.get(status, 0) + 1

    print(f"✅ PROJECTS_AUDIT.csv created - {len(projects)} projects")
    for status, count in status_counts.items():
        print(f"   - {status}: {count}")

    # DATA QUALITY REPORT
    print("\n📋 GENERATING DATA QUALITY REPORT...")

    issues = []

    # Check proposals missing key data
    cursor.execute("""
        SELECT project_code, project_name
        FROM proposals
        WHERE status = 'proposal'
          AND (client_company IS NULL OR first_contact_date IS NULL OR project_value IS NULL)
    """)
    missing_data = cursor.fetchall()
    if missing_data:
        issues.append(f"⚠️  {len(missing_data)} active proposals missing key data (client/date/value)")
        for code, name in missing_data[:5]:
            issues.append(f"     - {code}: {name}")
        if len(missing_data) > 5:
            issues.append(f"     ... and {len(missing_data) - 5} more")

    # Check won proposals not in projects
    cursor.execute("""
        SELECT p.project_code, p.project_name
        FROM proposals p
        WHERE p.status = 'won'
          AND p.is_active_project = 1
          AND NOT EXISTS (
              SELECT 1 FROM projects pr WHERE pr.project_code = p.project_code
          )
    """)
    won_not_projects = cursor.fetchall()
    if won_not_projects:
        issues.append(f"⚠️  {len(won_not_projects)} won proposals NOT in projects table:")
        for code, name in won_not_projects:
            issues.append(f"     - {code}: {name}")

    # Check projects with no invoices (Active status)
    cursor.execute("""
        SELECT p.project_code, p.project_title
        FROM projects p
        WHERE p.status = 'Active'
          AND NOT EXISTS (SELECT 1 FROM invoices WHERE project_code = p.project_code)
    """)
    no_invoices = cursor.fetchall()
    if no_invoices:
        issues.append(f"⚠️  {len(no_invoices)} active projects with NO invoices:")
        for code, title in no_invoices[:5]:
            issues.append(f"     - {code}: {title}")
        if len(no_invoices) > 5:
            issues.append(f"     ... and {len(no_invoices) - 5} more")

    # Check projects with balance owed
    cursor.execute("""
        SELECT
            p.project_code,
            p.project_title,
            COALESCE(inv.total, 0) - COALESCE(pay.total, 0) as balance
        FROM projects p
        LEFT JOIN (SELECT project_code, SUM(CAST(invoice_amount AS REAL)) as total FROM invoices GROUP BY project_code) inv
            ON p.project_code = inv.project_code
        LEFT JOIN (SELECT project_code, SUM(CAST(payment_amount AS REAL)) as total FROM payments GROUP BY project_code) pay
            ON p.project_code = pay.project_code
        WHERE COALESCE(inv.total, 0) - COALESCE(pay.total, 0) > 1000
        ORDER BY balance DESC
    """)
    balances = cursor.fetchall()
    if balances:
        issues.append(f"💰 {len(balances)} projects with outstanding balances > $1,000:")
        for code, title, balance in balances[:5]:
            issues.append(f"     - {code}: ${balance:,.2f} owed - {title}")
        if len(balances) > 5:
            issues.append(f"     ... and {len(balances) - 5} more")

    # Check lost proposals with no reason
    cursor.execute("""
        SELECT project_code, project_name
        FROM proposals
        WHERE status = 'lost'
          AND (current_remark IS NULL OR current_remark = '')
    """)
    lost_no_reason = cursor.fetchall()
    if lost_no_reason:
        issues.append(f"📝 {len(lost_no_reason)} lost proposals with NO reason/remark")

    with open('DATA_QUALITY_ISSUES.txt', 'w', encoding='utf-8') as f:
        f.write("BENSLEY DATABASE - DATA QUALITY ISSUES\n")
        f.write("=" * 80 + "\n\n")
        if issues:
            for issue in issues:
                f.write(issue + "\n")
        else:
            f.write("✅ No major data quality issues found!\n")

    print(f"\n✅ DATA_QUALITY_ISSUES.txt created")

    if issues:
        print("\n⚠️  ISSUES FOUND:")
        for issue in issues:
            print(issue)
    else:
        print("\n✅ No major data quality issues!")

    print("\n" + "=" * 80)
    print("📂 FILES CREATED:")
    print("   - PROPOSALS_AUDIT.csv (open in Excel)")
    print("   - PROJECTS_AUDIT.csv (open in Excel)")
    print("   - DATA_QUALITY_ISSUES.txt (review issues)")
    print("\n💡 TIP: Run './comprehensive_audit_tool.py' for interactive editing")
    print("=" * 80)

    conn.close()

if __name__ == "__main__":
    generate_reports()
