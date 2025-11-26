#!/usr/bin/env python3
"""
Analyze the remaining unlinked invoices to identify issues
"""
import sqlite3
from collections import defaultdict

DB_PATH = "database/bensley_master.db"

def main():
    print("🔍 Analyzing Unlinked Invoices\n")
    print("=" * 100)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all unlinked invoices
    cursor.execute("""
        SELECT
            i.invoice_number,
            i.description,
            i.invoice_amount,
            p.project_code,
            p.project_title
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE i.breakdown_id IS NULL OR i.breakdown_id = ''
        ORDER BY p.project_code, i.invoice_number
    """)

    unlinked = cursor.fetchall()
    print(f"\nTotal unlinked: {len(unlinked)} invoices\n")

    # Group by project
    by_project = defaultdict(list)
    for inv_num, desc, amount, proj_code, proj_title in unlinked:
        by_project[proj_code].append((inv_num, desc, amount, proj_title))

    # Analyze each project
    issue_categories = defaultdict(list)

    for proj_code, invoices in sorted(by_project.items()):
        proj_title = invoices[0][3]
        print(f"\n📋 {proj_code} - {proj_title}")
        print(f"   Unlinked invoices: {len(invoices)}")

        # Check if project has ANY breakdowns
        cursor.execute("""
            SELECT COUNT(*) FROM project_fee_breakdown
            WHERE project_code = ?
        """, (proj_code,))
        breakdown_count = cursor.fetchone()[0]

        if breakdown_count == 0:
            issue_categories["No breakdowns exist for project"].append(proj_code)
            print(f"   ❌ Issue: Project has NO fee breakdowns")
            for inv_num, desc, amount, _ in invoices[:3]:
                print(f"      • {inv_num:12} ${amount:>12,.2f} - {desc}")
            if len(invoices) > 3:
                print(f"      ... and {len(invoices) - 3} more")
        else:
            print(f"   ℹ️  Project has {breakdown_count} breakdowns")

            # Check descriptions
            has_installment = any("installment" in (desc or "").lower() for _, desc, _, _ in invoices)
            has_incomplete_desc = any(desc and desc.strip().endswith(" - ") for _, desc, _, _ in invoices)
            has_empty_desc = any(not desc or desc.strip() == "" for _, desc, _, _ in invoices)

            if has_installment:
                issue_categories["Installment payments (missing breakdown)"].append(proj_code)
                print(f"   ⚠️  Has installment payments")

            if has_incomplete_desc:
                issue_categories["Incomplete descriptions"].append(proj_code)
                print(f"   ⚠️  Has incomplete descriptions (ending with ' - ')")

            if has_empty_desc:
                issue_categories["Empty/missing descriptions"].append(proj_code)
                print(f"   ⚠️  Has empty descriptions")

            # Show sample invoices
            for inv_num, desc, amount, _ in invoices[:3]:
                desc_display = desc if desc else "(empty)"
                print(f"      • {inv_num:12} ${amount:>12,.2f} - {desc_display}")
            if len(invoices) > 3:
                print(f"      ... and {len(invoices) - 3} more")

    # Summary by issue category
    print("\n" + "=" * 100)
    print("ISSUES BY CATEGORY")
    print("=" * 100)

    for category, projects in sorted(issue_categories.items(), key=lambda x: -len(x[1])):
        print(f"\n📌 {category}: {len(projects)} projects")
        for proj in projects[:10]:
            print(f"   - {proj}")
        if len(projects) > 10:
            print(f"   ... and {len(projects) - 10} more")

    # Recommendations
    print("\n" + "=" * 100)
    print("RECOMMENDATIONS TO GET TO 100%")
    print("=" * 100)

    recs = []

    if "No breakdowns exist for project" in issue_categories:
        count = len(issue_categories["No breakdowns exist for project"])
        recs.append(f"1. Create fee breakdowns for {count} projects with no breakdowns")

    if "Installment payments (missing breakdown)" in issue_categories:
        count = len(issue_categories["Installment payments (missing breakdown)"])
        recs.append(f"2. Create 'installment' breakdowns for {count} projects with monthly payments")

    if "Incomplete descriptions" in issue_categories:
        count = len(issue_categories["Incomplete descriptions"])
        recs.append(f"3. Fix descriptions or manually map {count} projects with incomplete invoice descriptions")

    if "Empty/missing descriptions" in issue_categories:
        count = len(issue_categories["Empty/missing descriptions"])
        recs.append(f"4. Add descriptions or manually map invoices for {count} projects")

    for rec in recs:
        print(f"\n{rec}")

    # Quick fix opportunities
    print("\n" + "=" * 100)
    print("QUICK FIXES")
    print("=" * 100)

    # Check for projects that just need installment breakdown
    cursor.execute("""
        SELECT DISTINCT p.project_code, p.project_title, COUNT(i.invoice_id) as inv_count
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE (i.breakdown_id IS NULL OR i.breakdown_id = '')
        AND (i.description LIKE '%installment%' OR i.description LIKE '%monthly%')
        GROUP BY p.project_code
        ORDER BY inv_count DESC
    """)

    installment_projects = cursor.fetchall()
    if installment_projects:
        print(f"\n💡 Create installment breakdowns for these projects:")
        for proj_code, proj_title, inv_count in installment_projects:
            print(f"   • {proj_code:15} ({inv_count} invoices) - {proj_title}")

    conn.close()

if __name__ == "__main__":
    main()
