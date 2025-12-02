#!/usr/bin/env python3
"""
Project Classification Tool
Lets you classify projects as: proposal, active_contract, or archived
"""
import sqlite3

DB_PATH = "database/bensley_master.db"

def classify_projects():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all projects that need classification
    cursor.execute("""
        SELECT project_id, project_code, project_title, total_fee_usd, project_stage
        FROM projects
        WHERE status = 'Active'
        ORDER BY total_fee_usd DESC NULLS LAST
    """)

    projects = cursor.fetchall()

    print("=" * 100)
    print("PROJECT CLASSIFICATION TOOL")
    print("=" * 100)
    print(f"\nFound {len(projects)} projects to classify\n")
    print("Categories:")
    print("  P = Proposal (pipeline - not won yet)")
    print("  A = Active Contract (won project)")
    print("  X = Archived (completed/closed)")
    print("  S = Skip (keep current classification)")
    print("=" * 100)

    for idx, (proj_id, code, title, fee, current_stage) in enumerate(projects, 1):
        fee_str = f"${fee:,.0f}" if fee else "$0"
        current = current_stage or "unclassified"

        print(f"\n[{idx}/{len(projects)}] {code} - {title}")
        print(f"         Fee: {fee_str} | Current: {current}")

        while True:
            choice = input("         Classify as (P/A/X/S): ").strip().upper()

            if choice == 'S':
                print(f"         → Skipped")
                break
            elif choice == 'P':
                cursor.execute("UPDATE projects SET project_stage = 'proposal' WHERE project_id = ?", (proj_id,))
                print(f"         → Set to PROPOSAL")
                break
            elif choice == 'A':
                cursor.execute("UPDATE projects SET project_stage = 'active_contract' WHERE project_id = ?", (proj_id,))
                print(f"         → Set to ACTIVE CONTRACT")
                break
            elif choice == 'X':
                cursor.execute("UPDATE projects SET project_stage = 'archived' WHERE project_id = ?", (proj_id,))
                print(f"         → Set to ARCHIVED")
                break
            else:
                print("         Invalid choice. Use P, A, X, or S")

        # Save every 10 projects
        if idx % 10 == 0:
            conn.commit()
            print(f"\n>>> Progress saved ({idx}/{len(projects)})")

    conn.commit()

    # Show summary
    cursor.execute("""
        SELECT
            project_stage,
            COUNT(*) as count,
            COALESCE(SUM(total_fee_usd), 0) as total_value
        FROM projects
        WHERE status = 'Active'
        GROUP BY project_stage
    """)

    print("\n" + "=" * 100)
    print("CLASSIFICATION SUMMARY")
    print("=" * 100)
    for stage, count, value in cursor.fetchall():
        stage_name = stage or "unclassified"
        print(f"{stage_name:20} {count:4} projects  ${value:,.2f}")

    conn.close()
    print("\n✅ Classification complete!\n")

if __name__ == '__main__':
    classify_projects()
