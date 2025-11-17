#!/usr/bin/env python3
"""
Interactive Project Categorization Tool
Go through each project/proposal and properly categorize it
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db")

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def show_project(project, num, total):
    """Display project details"""
    clear_screen()
    print("=" * 100)
    print(f"PROJECT CATEGORIZATION ({num}/{total})")
    print("=" * 100)
    print(f"\nProject Code: {project['project_code']}")
    print(f"Project Name: {project['project_name']}")
    print(f"Source Table: {project['source_table']}")
    print(f"Current Status: {project['status']}")

    if project['source_table'] == 'projects':
        print(f"Is Active Project: {'YES' if project['is_active_project'] == 1 else 'NO'}")
        print(f"Health Score: {project['health_score']}%")
        print(f"Client: {project['client_company']}")
        print(f"Project Value: ${project['project_value']:,.0f}" if project['project_value'] else "Project Value: N/A")
    else:
        print(f"Total Fee: ${project['total_fee_usd']:,.0f}" if project['total_fee_usd'] else "Total Fee: N/A")

    print(f"\nEmails Linked: {project['email_count']}")
    print(f"Documents Linked: {project['doc_count']}")
    print("\n" + "-" * 100)

def get_choice(prompt, options):
    """Get user choice from options"""
    print(f"\n{prompt}")
    for key, value in options.items():
        print(f"  {key}) {value}")

    while True:
        choice = input("\nYour choice: ").strip().lower()
        if choice in options:
            return choice
        print("Invalid choice. Try again.")

def categorize_project(conn, project):
    """Interactive categorization for a single project"""
    cursor = conn.cursor()

    # Ask what this is
    type_choice = get_choice(
        "What is this?",
        {
            'a': 'Active Project (currently working on it)',
            'p': 'Proposal (still trying to win it)',
            'w': 'Won but not started yet',
            'f': 'Finished/Completed (project done)',
            'l': 'Lost (did not win proposal)',
            'c': 'Cancelled (killed/stopped)',
            'd': 'On Hold/Delayed',
            'x': 'Dead/Expired (old proposal, no longer relevant)',
            'r': 'Archive (old stuff to keep but inactive)',
            's': 'Skip (keep as-is)',
            'q': 'Quit categorization'
        }
    )

    if type_choice == 'q':
        return 'quit'

    if type_choice == 's':
        return 'skip'

    # Map choice to database values
    status_map = {
        'a': ('active_project', 1),
        'p': ('proposal', 0),
        'w': ('won_not_started', 0),
        'f': ('completed', 0),
        'l': ('lost', 0),
        'c': ('cancelled', 0),
        'd': ('on_hold', 0),
        'x': ('dead', 0),
        'r': ('archived', 0)
    }

    new_status, is_active = status_map[type_choice]

    # Ask for notes
    notes = input("\nAdd any notes? (press Enter to skip): ").strip()

    # Update the appropriate table
    if project['source_table'] == 'projects':
        # Update projects table
        if notes:
            cursor.execute("""
                UPDATE projects
                SET status = ?,
                    is_active_project = ?,
                    status_notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE project_code = ?
            """, (new_status, is_active, notes, project['project_code']))
        else:
            cursor.execute("""
                UPDATE projects
                SET status = ?,
                    is_active_project = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE project_code = ?
            """, (new_status, is_active, project['project_code']))
    else:
        # Update proposals table
        cursor.execute("""
            UPDATE proposals
            SET status = ?,
                notes = CASE
                    WHEN ? != '' THEN COALESCE(notes || '\n' || ?, ?)
                    ELSE notes
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE project_code = ?
        """, (new_status, notes, notes, notes, project['project_code']))

    conn.commit()

    print(f"\n✅ Updated {project['project_code']} to: {new_status}")
    input("\nPress Enter to continue...")

    return 'continue'

def main():
    """Main categorization loop"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all projects/proposals
    cursor.execute("""
        SELECT
            p.project_code,
            p.project_title as project_name,
            NULL as client_company,
            p.status,
            0 as is_active_project,
            NULL as health_score,
            p.total_fee_usd,
            NULL as project_value,
            COUNT(DISTINCT epl.email_id) as email_count,
            COUNT(DISTINCT dpl.document_id) as doc_count,
            'proposals' as source_table,
            p.project_id as id
        FROM proposals p
        LEFT JOIN email_proposal_links epl ON p.project_id = epl.proposal_id
        LEFT JOIN document_proposal_links dpl ON p.project_id = dpl.proposal_id
        GROUP BY p.project_code

        UNION ALL

        SELECT
            p.project_code,
            p.project_name,
            p.client_company,
            p.status,
            p.is_active_project,
            p.health_score,
            NULL as total_fee_usd,
            p.project_value,
            COUNT(DISTINCT e.email_id) as email_count,
            COUNT(DISTINCT d.document_id) as doc_count,
            'projects' as source_table,
            p.proposal_id as id
        FROM projects p
        LEFT JOIN email_project_links epl ON p.project_code = epl.project_code
        LEFT JOIN emails e ON epl.email_id = e.email_id
        LEFT JOIN project_documents pd ON p.proposal_id = pd.project_id
        LEFT JOIN documents d ON pd.document_id = d.document_id
        GROUP BY p.project_code

        ORDER BY project_code
    """)

    projects = cursor.fetchall()
    total = len(projects)

    clear_screen()
    print("=" * 100)
    print("BENSLEY PROJECT CATEGORIZATION TOOL")
    print("=" * 100)
    print(f"\nYou have {total} projects/proposals to categorize.")
    print("\nThis will help you go through each one and properly set its status.")

    start = input("\nPress Enter to start (or 'q' to quit): ").strip().lower()
    if start == 'q':
        print("Exiting...")
        return

    categorized = 0
    skipped = 0

    for i, project in enumerate(projects, 1):
        show_project(project, i, total)

        result = categorize_project(conn, project)

        if result == 'quit':
            print("\n\nQuitting...")
            break
        elif result == 'skip':
            skipped += 1
        else:
            categorized += 1

    conn.close()

    clear_screen()
    print("=" * 100)
    print("CATEGORIZATION COMPLETE!")
    print("=" * 100)
    print(f"\nCategorized: {categorized}")
    print(f"Skipped: {skipped}")
    print(f"Total: {total}")
    print("\n✅ All changes saved to database")
    print("\nRun simple_project_summary.py again to see the updated summary!")
    print("=" * 100)

if __name__ == "__main__":
    main()
