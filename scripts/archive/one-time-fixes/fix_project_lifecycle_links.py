#!/usr/bin/env python3
"""
Fix Bensley Project Lifecycle Links
Links proposals → projects → invoices properly
"""

import sqlite3
import os
import re
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv('DATABASE_PATH', './database/bensley_master.db')

def extract_project_code_from_invoice(invoice_number):
    """Extract project code from invoice number (e.g., I24-017 → 017)"""
    match = re.search(r'I?\d{2}-?(\d{3})', invoice_number)
    if match:
        return match.group(1)
    return None

def find_project_by_code(cursor, code_num):
    """Find project by code number (handles both BK-017 and 25 BK-017 formats)"""
    # Try multiple formats
    codes_to_try = [
        f'BK-{code_num}',
        f'25 BK-{code_num}',
        f'25BK-{code_num}',
        f'23 BK-{code_num}',  # Some projects use 23
        f'24 BK-{code_num}',  # Some use 24
    ]

    for code in codes_to_try:
        cursor.execute("SELECT project_id, project_code FROM projects WHERE project_code = ?", (code,))
        result = cursor.fetchone()
        if result:
            return result

    return None

def main(dry_run=True):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("="*80)
    print("BENSLEY PROJECT LIFECYCLE FIX")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("="*80)

    # STEP 1: Add linking columns if they don't exist
    print("\n[1/4] Adding linking columns...")

    try:
        if not dry_run:
            # Add proposal_id to projects table
            cursor.execute("ALTER TABLE projects ADD COLUMN proposal_id INTEGER")
            print("  ✅ Added projects.proposal_id")
        else:
            print("  [DRY RUN] Would add projects.proposal_id")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ℹ️  projects.proposal_id already exists")
        else:
            print(f"  ⚠️  Error: {e}")

    try:
        if not dry_run:
            # Add active_project_id to proposals table
            cursor.execute("ALTER TABLE proposals ADD COLUMN active_project_id INTEGER")
            print("  ✅ Added proposals.active_project_id")
        else:
            print("  [DRY RUN] Would add proposals.active_project_id")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("  ℹ️  proposals.active_project_id already exists")
        else:
            print(f"  ⚠️  Error: {e}")

    # STEP 2: Link proposals to projects
    print("\n[2/4] Linking proposals → projects...")

    cursor.execute("""
        SELECT proposal_id, project_code, project_name, status
        FROM proposals
        WHERE status IN ('won', 'active')
    """)

    won_proposals = cursor.fetchall()
    print(f"  Found {len(won_proposals)} won/active proposals")

    linked_count = 0
    for prop_id, prop_code, prop_name, status in won_proposals:
        # Extract code number (e.g., BK-017 → 017)
        code_match = re.search(r'BK-?(\d{3})', prop_code)
        if not code_match:
            continue

        code_num = code_match.group(1)

        # Find matching project
        project = find_project_by_code(cursor, code_num)
        if project:
            project_id, project_code = project

            if dry_run:
                print(f"  [DRY RUN] Would link:")
                print(f"    Proposal {prop_code} (id={prop_id})")
                print(f"    → Project {project_code} (id={project_id})")
            else:
                # Link both ways
                cursor.execute("UPDATE proposals SET active_project_id = ? WHERE proposal_id = ?",
                             (project_id, prop_id))
                cursor.execute("UPDATE projects SET proposal_id = ? WHERE project_id = ?",
                             (prop_id, project_id))
                print(f"  ✅ Linked {prop_code} → {project_code}")

            linked_count += 1

    print(f"  Total linked: {linked_count}/{len(won_proposals)}")

    # STEP 3: Fix invoice links
    print("\n[3/4] Fixing invoice → project links...")

    cursor.execute("SELECT invoice_id, invoice_number, project_id FROM invoices")
    all_invoices = cursor.fetchall()

    fixed_count = 0
    for inv_id, inv_number, current_project_id in all_invoices:
        # Extract project code from invoice number
        code_num = extract_project_code_from_invoice(inv_number)
        if not code_num:
            continue

        # Find correct project
        project = find_project_by_code(cursor, code_num)
        if not project:
            continue

        correct_project_id, project_code = project

        # Check if already correct
        if current_project_id == correct_project_id:
            continue

        if dry_run:
            print(f"  [DRY RUN] Would fix: {inv_number}")
            print(f"    Current: project_id {current_project_id}")
            print(f"    Correct: project_id {correct_project_id} ({project_code})")
        else:
            cursor.execute("UPDATE invoices SET project_id = ? WHERE invoice_id = ?",
                         (correct_project_id, inv_id))
            print(f"  ✅ Fixed {inv_number} → {project_code}")

        fixed_count += 1

    print(f"  Total fixed: {fixed_count}/{len(all_invoices)}")

    # STEP 4: Summary
    print("\n[4/4] Generating summary...")

    # Count linked proposals
    cursor.execute("""
        SELECT COUNT(*) FROM proposals WHERE active_project_id IS NOT NULL
    """)
    linked_proposals = cursor.fetchone()[0]

    # Count projects with proposal links
    cursor.execute("""
        SELECT COUNT(*) FROM projects WHERE proposal_id IS NOT NULL
    """)
    linked_projects = cursor.fetchone()[0]

    # Count correctly linked invoices
    cursor.execute("""
        SELECT COUNT(DISTINCT i.invoice_id)
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
    """)
    correct_invoices = cursor.fetchone()[0]

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Proposals linked to projects: {linked_proposals if not dry_run else linked_count}")
    print(f"Projects linked to proposals: {linked_projects if not dry_run else linked_count}")
    print(f"Invoices correctly linked: {correct_invoices if not dry_run else f'{fixed_count} would be fixed'}")

    if not dry_run:
        conn.commit()
        print("\n✅ Changes committed to database")
    else:
        print("\n[DRY RUN] No changes made - run with --live to apply fixes")

    conn.close()

if __name__ == '__main__':
    import sys
    dry_run = '--live' not in sys.argv
    main(dry_run=dry_run)
