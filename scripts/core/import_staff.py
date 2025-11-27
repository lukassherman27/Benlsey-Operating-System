#!/usr/bin/env python3
"""
Import Staff Data - Syncs team_members table to staff table

This script consolidates staff data by syncing from team_members (98 records)
into the more detailed staff table. It:
- Maps discipline to department (Design for all design roles, Leadership for management)
- Parses full_name into first_name/last_name
- Preserves existing staff records (doesn't overwrite)
- Links via email as the unique key
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

# Paths
WORKING_DIR = Path(__file__).parent.parent.parent
DB_PATH = WORKING_DIR / "database" / "bensley_master.db"

# Discipline to Department mapping
DISCIPLINE_TO_DEPARTMENT = {
    'Architecture': 'Design',
    'Interior': 'Design',
    'Landscape': 'Design',
    'Artwork': 'Design',
    'Management': 'Leadership',
}

# Seniority based on is_team_lead
def get_seniority(is_team_lead):
    return 'Senior' if is_team_lead else 'Mid'


def parse_name(full_name):
    """Split full_name into first_name and last_name"""
    if not full_name or full_name.strip() == '':
        return None, None

    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], None
    else:
        return parts[0], ' '.join(parts[1:])


def validate_team_member(row):
    """Validate a team_member record before import"""
    errors = []

    email = row[1]  # email column
    full_name = row[2]  # full_name column
    discipline = row[5]  # discipline column

    if not email or '@' not in email:
        errors.append(f"Invalid email: {email}")

    if not full_name or len(full_name.strip()) < 2:
        errors.append(f"Invalid name: {full_name}")

    if discipline not in DISCIPLINE_TO_DEPARTMENT:
        errors.append(f"Unknown discipline: {discipline}")

    return errors


def import_staff(dry_run=False):
    """Sync team_members to staff table"""
    print("\n" + "="*80)
    print("IMPORT STAFF DATA - Sync from team_members to staff")
    print("="*80)

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")

    print(f"\n📂 Database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get existing staff emails (to avoid duplicates)
    cursor.execute("SELECT email FROM staff WHERE email IS NOT NULL")
    existing_emails = set(row[0].lower() for row in cursor.fetchall() if row[0])
    print(f"📋 Existing staff records: {len(existing_emails)}")

    # Get all team_members
    cursor.execute("""
        SELECT
            member_id, email, full_name, nickname, office,
            discipline, is_active, is_team_lead, sub_specialty
        FROM team_members
        ORDER BY discipline, full_name
    """)
    team_members = cursor.fetchall()
    print(f"📋 Team members to process: {len(team_members)}")

    imported = 0
    skipped = 0
    validation_errors = 0
    already_exists = 0

    print("\n" + "-"*60)
    print("PROCESSING TEAM MEMBERS")
    print("-"*60)

    for row in team_members:
        member_id, email, full_name, nickname, office, discipline, is_active, is_team_lead, sub_specialty = row

        # Validate
        errors = validate_team_member(row)
        if errors:
            print(f"  ❌ Validation failed for {email}: {', '.join(errors)}")
            validation_errors += 1
            continue

        # Skip if already in staff
        if email and email.lower() in existing_emails:
            skipped += 1
            already_exists += 1
            continue

        # Parse name
        first_name, last_name = parse_name(full_name)

        # Map discipline to department
        department = DISCIPLINE_TO_DEPARTMENT.get(discipline, 'Design')

        # Determine role from discipline + sub_specialty
        role = sub_specialty if sub_specialty else discipline

        # Determine seniority
        seniority = 'Senior' if is_team_lead else 'Mid'

        # Normalize office
        if office == 'Thailand':
            office = 'Bangkok'

        if not dry_run:
            try:
                cursor.execute("""
                    INSERT INTO staff (
                        first_name, last_name, nickname, email, office,
                        department, role, seniority, employment_type, is_active,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'full-time', ?, datetime('now'), datetime('now'))
                """, (
                    first_name,
                    last_name,
                    nickname,
                    email,
                    office,
                    department,
                    role,
                    seniority,
                    is_active
                ))
                imported += 1
                print(f"  ✅ Imported: {full_name} ({email}) - {discipline}")
            except sqlite3.IntegrityError as e:
                print(f"  ⚠️  Skipped (duplicate): {email}")
                skipped += 1
        else:
            imported += 1
            print(f"  📋 Would import: {full_name} ({email}) - {discipline} → {department}")

    if not dry_run:
        conn.commit()

    conn.close()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"  ✅ Imported: {imported}")
    print(f"  ⏭️  Already existed: {already_exists}")
    print(f"  ⏭️  Skipped (other): {skipped - already_exists}")
    print(f"  ❌ Validation errors: {validation_errors}")
    print(f"  📊 Total processed: {len(team_members)}")

    if dry_run:
        print("\n🔍 This was a DRY RUN - no changes were made")
        print("   Run without --dry-run to actually import")

    return imported


def show_current_status():
    """Show current state of staff and team_members tables"""
    print("\n" + "="*80)
    print("CURRENT DATABASE STATUS")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Staff table
    cursor.execute("SELECT COUNT(*) FROM staff")
    staff_count = cursor.fetchone()[0]

    cursor.execute("SELECT department, COUNT(*) as count FROM staff GROUP BY department ORDER BY count DESC")
    staff_by_dept = cursor.fetchall()

    print(f"\n📊 STAFF TABLE: {staff_count} records")
    for dept, count in staff_by_dept:
        print(f"   - {dept or 'Unknown'}: {count}")

    # Team members table
    cursor.execute("SELECT COUNT(*) FROM team_members")
    team_count = cursor.fetchone()[0]

    cursor.execute("SELECT discipline, COUNT(*) as count FROM team_members GROUP BY discipline ORDER BY count DESC")
    team_by_discipline = cursor.fetchall()

    print(f"\n📊 TEAM_MEMBERS TABLE: {team_count} records")
    for disc, count in team_by_discipline:
        print(f"   - {disc}: {count}")

    # Project assignments
    cursor.execute("SELECT COUNT(*) FROM project_pm_assignments")
    assignment_count = cursor.fetchone()[0]
    print(f"\n📊 PROJECT ASSIGNMENTS: {assignment_count} records")

    conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import staff data from team_members table')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without modifying database')
    parser.add_argument('--status', action='store_true', help='Show current database status only')
    args = parser.parse_args()

    if args.status:
        show_current_status()
        return

    print("\n" + "="*80)
    print("STAFF DATA IMPORT")
    print("="*80)
    print("\nThis script syncs team_members (98 records) into the staff table.")
    print("It maps disciplines to departments and parses names.")
    print("\nExisting staff records will NOT be overwritten.")

    if args.dry_run:
        print("\n🔍 Running in DRY RUN mode...")
        import_staff(dry_run=True)
    else:
        response = input("\nProceed with import? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return

        import_staff(dry_run=False)

        print("\n✅ Staff import complete!")
        show_current_status()


if __name__ == "__main__":
    main()
