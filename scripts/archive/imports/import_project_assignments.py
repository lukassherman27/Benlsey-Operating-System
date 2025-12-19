#!/usr/bin/env python3
"""
Import Project Assignments - Links team members to projects

This script imports project-staff assignments from a CSV template into the
project_pm_assignments table. It:
- Validates project codes exist in the projects table
- Validates staff emails exist in the team_members table
- Creates assignment records with role, phase, and primary flag
- Supports dry-run mode for preview

Usage:
  python import_project_assignments.py --template exports/project_staff_assignment_template.csv
  python import_project_assignments.py --template exports/project_staff_assignment_template.csv --dry-run
  python import_project_assignments.py --generate-template  # Creates a new template
  python import_project_assignments.py --status  # Shows current status
"""

import sqlite3
import csv
import os
from pathlib import Path
from datetime import datetime

# Paths
WORKING_DIR = Path(__file__).parent.parent.parent
DB_PATH = WORKING_DIR / "database" / "bensley_master.db"
DEFAULT_TEMPLATE = WORKING_DIR / "exports" / "project_staff_assignment_template.csv"
STAFF_LOOKUP = WORKING_DIR / "exports" / "staff_lookup.csv"

VALID_ROLES = ['lead', 'assigned', 'support', 'reviewer']
VALID_PHASES = ['concept', 'schematic', 'DD', 'CD', 'construction', None]


def generate_template():
    """Generate a template CSV for manual assignment input"""
    print("\n" + "="*80)
    print("GENERATING PROJECT ASSIGNMENT TEMPLATE")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all projects
    cursor.execute("""
        SELECT project_id, project_code, project_title
        FROM projects
        ORDER BY project_code DESC
    """)
    projects = cursor.fetchall()

    # Get all active team members
    cursor.execute("""
        SELECT member_id, email, full_name, discipline
        FROM team_members
        WHERE is_active = 1
        ORDER BY discipline, full_name
    """)
    team_members = cursor.fetchall()

    conn.close()

    # Create exports directory
    DEFAULT_TEMPLATE.parent.mkdir(exist_ok=True)

    # Create template CSV
    with open(DEFAULT_TEMPLATE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['project_code', 'project_title', 'member_email', 'role', 'is_primary', 'phase', 'notes'])

        for pid, code, title in projects:
            # Write one empty row per project (to be filled in manually)
            writer.writerow([code, title or '', '', 'assigned', '0', '', ''])

    print(f"\n✅ Created template: {DEFAULT_TEMPLATE}")
    print(f"   Projects: {len(projects)}")

    # Also create a staff lookup file
    with open(STAFF_LOOKUP, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'name', 'discipline'])
        for mid, email, name, disc in team_members:
            writer.writerow([email, name, disc])

    print(f"✅ Created lookup: {STAFF_LOOKUP}")
    print(f"   Team members: {len(team_members)}")

    print("\n📝 Instructions:")
    print("   1. Open the template CSV")
    print("   2. For each project, add one row per assigned staff member")
    print("   3. Use emails from staff_lookup.csv")
    print("   4. Role options: lead, assigned, support, reviewer")
    print("   5. Set is_primary=1 for the main contact")
    print("   6. Phase options: concept, schematic, DD, CD, construction (or leave blank)")
    print("   7. Run: python import_project_assignments.py --template <file.csv>")


def validate_row(row, valid_projects, valid_emails):
    """Validate a single row from the template"""
    errors = []

    project_code = row.get('project_code', '').strip()
    member_email = row.get('member_email', '').strip()
    role = row.get('role', 'assigned').strip().lower()
    is_primary = row.get('is_primary', '0').strip()
    phase = row.get('phase', '').strip() or None

    # Skip empty rows
    if not project_code or not member_email:
        return None, ['Empty row - skipping']

    if project_code not in valid_projects:
        errors.append(f"Unknown project: {project_code}")

    if member_email.lower() not in valid_emails:
        errors.append(f"Unknown email: {member_email}")

    if role not in VALID_ROLES:
        errors.append(f"Invalid role '{role}' - must be: {', '.join(VALID_ROLES)}")

    if is_primary not in ['0', '1', 'true', 'false', 'yes', 'no']:
        errors.append(f"Invalid is_primary: {is_primary}")

    if phase and phase not in VALID_PHASES:
        errors.append(f"Invalid phase '{phase}' - must be: {', '.join(str(p) for p in VALID_PHASES)}")

    return {
        'project_code': project_code,
        'member_email': member_email.lower(),
        'role': role,
        'is_primary': 1 if is_primary in ['1', 'true', 'yes'] else 0,
        'phase': phase,
        'notes': row.get('notes', '').strip()
    }, errors


def import_assignments(template_path, dry_run=False):
    """Import project assignments from a CSV template"""
    print("\n" + "="*80)
    print("IMPORT PROJECT ASSIGNMENTS")
    print("="*80)

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")

    template_path = Path(template_path)
    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        return 0

    print(f"\n📂 Database: {DB_PATH}")
    print(f"📂 Template: {template_path}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get valid projects
    cursor.execute("SELECT project_code, project_id FROM projects")
    valid_projects = {row[0]: row[1] for row in cursor.fetchall()}
    print(f"📋 Valid projects: {len(valid_projects)}")

    # Get valid team members
    cursor.execute("SELECT email, member_id FROM team_members")
    valid_emails = {row[0].lower(): row[1] for row in cursor.fetchall()}
    print(f"📋 Valid team members: {len(valid_emails)}")

    # Read template
    with open(template_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"📋 Template rows: {len(rows)}")

    imported = 0
    skipped = 0
    validation_errors = 0

    print("\n" + "-"*60)
    print("PROCESSING ASSIGNMENTS")
    print("-"*60)

    for i, row in enumerate(rows, 1):
        parsed, errors = validate_row(row, valid_projects, valid_emails)

        if errors and parsed is None:
            # Empty row - skip silently
            skipped += 1
            continue

        if errors:
            print(f"  ❌ Row {i}: {', '.join(errors)}")
            validation_errors += 1
            continue

        project_id = valid_projects[parsed['project_code']]
        member_id = valid_emails[parsed['member_email']]

        if not dry_run:
            try:
                cursor.execute("""
                    INSERT INTO project_pm_assignments (
                        project_id, project_code, member_id, role, phase,
                        is_primary, notes, start_date, assigned_by, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, date('now'), 'import_script', datetime('now'))
                """, (
                    project_id,
                    parsed['project_code'],
                    member_id,
                    parsed['role'],
                    parsed['phase'],
                    parsed['is_primary'],
                    parsed['notes']
                ))
                imported += 1
                print(f"  ✅ Assigned: {parsed['member_email']} → {parsed['project_code']} ({parsed['role']})")
            except sqlite3.IntegrityError as e:
                print(f"  ⚠️  Skipped (duplicate): {parsed['member_email']} → {parsed['project_code']}")
                skipped += 1
        else:
            imported += 1
            print(f"  📋 Would assign: {parsed['member_email']} → {parsed['project_code']} ({parsed['role']})")

    if not dry_run:
        conn.commit()

    conn.close()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"  ✅ Imported: {imported}")
    print(f"  ⏭️  Skipped (empty/duplicate): {skipped}")
    print(f"  ❌ Validation errors: {validation_errors}")

    if dry_run:
        print("\n🔍 This was a DRY RUN - no changes were made")
        print("   Run without --dry-run to actually import")

    return imported


def show_status():
    """Show current assignment status"""
    print("\n" + "="*80)
    print("PROJECT ASSIGNMENT STATUS")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total projects
    cursor.execute("SELECT COUNT(*) FROM projects")
    project_count = cursor.fetchone()[0]

    # Total assignments
    cursor.execute("SELECT COUNT(*) FROM project_pm_assignments")
    assignment_count = cursor.fetchone()[0]

    # Projects with assignments
    cursor.execute("""
        SELECT COUNT(DISTINCT project_code) FROM project_pm_assignments
    """)
    projects_with_assignments = cursor.fetchone()[0]

    print(f"\n📊 Projects: {project_count}")
    print(f"📊 Total assignments: {assignment_count}")
    print(f"📊 Projects with assignments: {projects_with_assignments}/{project_count}")

    if assignment_count > 0:
        # Top assigned team members
        cursor.execute("""
            SELECT tm.full_name, tm.discipline, COUNT(*) as count
            FROM project_pm_assignments pma
            JOIN team_members tm ON pma.member_id = tm.member_id
            GROUP BY pma.member_id
            ORDER BY count DESC
            LIMIT 10
        """)
        top_assigned = cursor.fetchall()

        print("\n📊 Top assigned team members:")
        for name, disc, count in top_assigned:
            print(f"   - {name} ({disc}): {count} projects")

        # Role breakdown
        cursor.execute("""
            SELECT role, COUNT(*) as count
            FROM project_pm_assignments
            GROUP BY role
            ORDER BY count DESC
        """)
        role_breakdown = cursor.fetchall()

        print("\n📊 Role breakdown:")
        for role, count in role_breakdown:
            print(f"   - {role}: {count}")

    conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import project assignments from CSV template')
    parser.add_argument('--template', type=str, help='Path to the CSV template file')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying database')
    parser.add_argument('--generate-template', action='store_true', help='Generate a new template file')
    parser.add_argument('--status', action='store_true', help='Show current assignment status')
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.generate_template:
        generate_template()
        return

    if not args.template:
        print("❌ Please provide a template file with --template <path>")
        print("   Or use --generate-template to create a new template")
        print("   Or use --status to see current status")
        return

    if args.dry_run:
        import_assignments(args.template, dry_run=True)
    else:
        print("\n" + "="*80)
        print("IMPORT PROJECT ASSIGNMENTS")
        print("="*80)
        print(f"\nTemplate: {args.template}")
        print("\nThis will import staff-project assignments.")

        response = input("\nProceed with import? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return

        import_assignments(args.template, dry_run=False)

        print("\n✅ Import complete!")
        show_status()


if __name__ == "__main__":
    main()
