#!/usr/bin/env python3
"""
Contract Fee Breakdown Importer

This script helps you populate the project_fee_breakdown table with contract data.
You can import fees manually or from contract PDFs.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def list_active_projects():
    """List all active projects"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT project_code, project_name, client_company, total_fee_usd
        FROM projects
        WHERE is_active_project = 1 OR status IN ('active', 'active_project', 'Active')
        ORDER BY project_code DESC
    """)

    projects = cursor.fetchall()
    conn.close()

    print("\n" + "="*80)
    print("ACTIVE PROJECTS")
    print("="*80)
    for i, p in enumerate(projects, 1):
        print(f"{i:2d}. {p['project_code']:12s} | {p['project_name'][:40]:40s} | Total: ${p['total_fee_usd'] or 0:,.0f}")
    print("="*80 + "\n")

    return projects


def add_fee_breakdown_entry(project_code: str, discipline: str, phase: str, fee: float):
    """Add a single fee breakdown entry"""
    conn = get_connection()
    cursor = conn.cursor()

    breakdown_id = f"{project_code}-{discipline[:3].upper()}-{phase[:3].upper()}-{uuid.uuid4().hex[:8]}"

    cursor.execute("""
        INSERT INTO project_fee_breakdown (
            breakdown_id, project_code, discipline, phase, phase_fee_usd,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        breakdown_id,
        project_code,
        discipline,
        phase,
        fee,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    print(f"✓ Added: {discipline} - {phase}: ${fee:,.2f}")


def manual_import_for_project(project_code: str):
    """Manually import contract fees for a project"""
    print(f"\n📋 Importing contract fees for: {project_code}")
    print("\nDisciplines: Landscape, Interior, Architecture")
    print("Common Phases: Mobilization, Concept Design, Design Development, Construction Documents, Construction Observation\n")

    disciplines = ["Landscape", "Interior", "Architecture"]

    for discipline in disciplines:
        print(f"\n--- {discipline.upper()} ---")
        add_discipline = input(f"Add fees for {discipline}? (y/n): ").strip().lower()

        if add_discipline != 'y':
            continue

        while True:
            phase = input("  Phase name (or 'done' to finish this discipline): ").strip()
            if phase.lower() == 'done':
                break

            try:
                fee = float(input(f"  Fee for {phase}: $").strip().replace(",", ""))
                add_fee_breakdown_entry(project_code, discipline, phase, fee)
            except ValueError:
                print("  ❌ Invalid amount. Skipping.")
                continue


def batch_import_standard_phases(project_code: str):
    """Import a standard 5-phase breakdown for all three disciplines"""
    print(f"\n📋 Standard 5-Phase Import for: {project_code}")
    print("\nPhases: Mobilization, Concept Design, Design Development, Construction Documents, Construction Observation")

    disciplines = ["Landscape", "Interior", "Architecture"]
    phases = [
        "Mobilization",
        "Concept Design",
        "Design Development",
        "Construction Documents",
        "Construction Observation"
    ]

    fees = {}

    for discipline in disciplines:
        print(f"\n--- {discipline.upper()} ---")
        fees[discipline] = {}

        for phase in phases:
            try:
                fee = float(input(f"  {phase}: $").strip().replace(",", ""))
                fees[discipline][phase] = fee
            except ValueError:
                print(f"  ❌ Skipping {phase}")
                continue

    # Confirm before inserting
    print("\n" + "="*80)
    print("SUMMARY - Please confirm:")
    print("="*80)
    total = 0
    for discipline in disciplines:
        disc_total = sum(fees.get(discipline, {}).values())
        total += disc_total
        print(f"\n{discipline}: ${disc_total:,.2f}")
        for phase, fee in fees.get(discipline, {}).items():
            print(f"  • {phase}: ${fee:,.2f}")

    print(f"\n{'TOTAL CONTRACT FEE'}: ${total:,.2f}")
    print("="*80)

    confirm = input("\nImport these fees? (yes/no): ").strip().lower()

    if confirm == 'yes':
        for discipline in disciplines:
            for phase, fee in fees.get(discipline, {}).items():
                add_fee_breakdown_entry(project_code, discipline, phase, fee)
        print(f"\n✅ Successfully imported {sum(len(v) for v in fees.values())} fee entries!")
    else:
        print("\n❌ Import cancelled.")


def view_existing_breakdown(project_code: str):
    """View existing fee breakdown for a project"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT discipline, phase, phase_fee_usd
        FROM project_fee_breakdown
        WHERE project_code = ?
        ORDER BY discipline, phase
    """, (project_code,))

    breakdowns = cursor.fetchall()
    conn.close()

    if not breakdowns:
        print(f"\n⚠️  No fee breakdown found for {project_code}")
        return

    print(f"\n📊 CONTRACT FEE BREAKDOWN - {project_code}")
    print("="*80)

    current_discipline = None
    discipline_total = 0
    grand_total = 0

    for row in breakdowns:
        if current_discipline != row['discipline']:
            if current_discipline:
                print(f"  └─ Subtotal: ${discipline_total:,.2f}")
            current_discipline = row['discipline']
            discipline_total = 0
            print(f"\n{current_discipline}:")

        fee = row['phase_fee_usd'] or 0
        discipline_total += fee
        grand_total += fee
        print(f"  • {row['phase']:30s}: ${fee:,.2f}")

    if current_discipline:
        print(f"  └─ Subtotal: ${discipline_total:,.2f}")

    print(f"\n{'TOTAL CONTRACT FEE'}: ${grand_total:,.2f}")
    print("="*80)


def main():
    """Main menu"""
    print("\n" + "="*80)
    print(" CONTRACT FEE BREAKDOWN IMPORTER ".center(80, "="))
    print("="*80)

    while True:
        print("\nOptions:")
        print("1. View active projects")
        print("2. Manual import (custom phases)")
        print("3. Standard import (5-phase breakdown)")
        print("4. View existing breakdown")
        print("5. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            list_active_projects()

        elif choice == '2':
            projects = list_active_projects()
            try:
                idx = int(input("Select project number: ")) - 1
                if 0 <= idx < len(projects):
                    manual_import_for_project(projects[idx]['project_code'])
                else:
                    print("❌ Invalid selection")
            except (ValueError, IndexError):
                print("❌ Invalid input")

        elif choice == '3':
            projects = list_active_projects()
            try:
                idx = int(input("Select project number: ")) - 1
                if 0 <= idx < len(projects):
                    batch_import_standard_phases(projects[idx]['project_code'])
                else:
                    print("❌ Invalid selection")
            except (ValueError, IndexError):
                print("❌ Invalid input")

        elif choice == '4':
            project_code = input("Enter project code: ").strip()
            view_existing_breakdown(project_code)

        elif choice == '5':
            print("\n👋 Goodbye!\n")
            break

        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()
