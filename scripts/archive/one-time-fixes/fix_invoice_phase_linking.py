#!/usr/bin/env python3
"""
Fix missing breakdown_id values in project_fee_breakdown and invoices tables

This script:
1. Generates unique breakdown_id for all project_fee_breakdown records
2. Links existing invoices to their correct phase/discipline via breakdown_id
"""
import sqlite3
import re
from typing import Tuple

DB_PATH = "database/bensley_master.db"

def slugify(text: str) -> str:
    """Convert text to URL-safe slug"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text

def generate_breakdown_id(project_code: str, discipline: str, phase: str) -> str:
    """Generate unique breakdown_id from project, discipline, and phase"""
    # Clean up project_code (remove spaces, lowercase)
    clean_project = project_code.replace(' ', '-').strip()
    clean_discipline = slugify(discipline) if discipline else 'unknown'
    clean_phase = slugify(phase) if phase else 'unknown'

    return f"{clean_project}_{clean_discipline}_{clean_phase}"

def parse_description(description: str) -> Tuple[str, str]:
    """Parse invoice description to extract discipline and phase
    Format: "Phase - Discipline" e.g. "mobilization - Landscape" (from import script)
    Returns: (discipline, phase)
    """
    if not description:
        return None, None

    parts = description.split(' - ')
    if len(parts) == 2:
        return parts[1].strip(), parts[0].strip()  # discipline, phase (swapped order)
    return None, None

def main():
    print("🔧 Fixing Invoice-Phase Linking\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1: Generate breakdown_id for project_fee_breakdown records
    print("📋 Step 1: Generating breakdown_id for project_fee_breakdown...")

    cursor.execute("""
        SELECT rowid, project_code, discipline, phase
        FROM project_fee_breakdown
        WHERE breakdown_id IS NULL OR breakdown_id = ''
    """)

    breakdown_rows = cursor.fetchall()
    print(f"   Found {len(breakdown_rows)} records without breakdown_id")

    updated_breakdowns = 0
    skipped_duplicates = 0
    seen_breakdown_ids = set()  # Track breakdown_ids we've already used

    for rowid, project_code, discipline, phase in breakdown_rows:
        breakdown_id = generate_breakdown_id(project_code, discipline, phase)

        # Check if this breakdown_id was already used (duplicate combination)
        if breakdown_id in seen_breakdown_ids:
            print(f"   ⚠️  Duplicate: {breakdown_id} (skipping rowid {rowid})")
            skipped_duplicates += 1
            continue

        try:
            cursor.execute("""
                UPDATE project_fee_breakdown
                SET breakdown_id = ?
                WHERE rowid = ?
            """, (breakdown_id, rowid))

            seen_breakdown_ids.add(breakdown_id)
            updated_breakdowns += 1
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  IntegrityError for {breakdown_id}: {e}")
            skipped_duplicates += 1

    conn.commit()
    print(f"   ✅ Updated {updated_breakdowns} project_fee_breakdown records")
    if skipped_duplicates > 0:
        print(f"   ⚠️  Skipped {skipped_duplicates} duplicate records\n")
    else:
        print()

    # Build breakdown_map from ALL existing records (not just newly updated ones)
    print("📋 Building breakdown_map from all records...")
    cursor.execute("""
        SELECT breakdown_id, project_code, discipline, phase
        FROM project_fee_breakdown
        WHERE breakdown_id IS NOT NULL AND breakdown_id != ''
    """)

    breakdown_map = {}  # Map of (project_code, discipline, phase) -> breakdown_id
    for breakdown_id, project_code, discipline, phase in cursor.fetchall():
        key = (project_code, discipline.lower().strip(), phase.lower().strip())
        breakdown_map[key] = breakdown_id

    print(f"   Built map with {len(breakdown_map)} entries\n")

    # Step 2: Link invoices to breakdown_id
    print("🔗 Step 2: Linking invoices to breakdown_id...")

    cursor.execute("""
        SELECT
            i.rowid,
            i.invoice_number,
            i.description,
            p.project_code
        FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE i.breakdown_id IS NULL OR i.breakdown_id = ''
    """)

    invoice_rows = cursor.fetchall()
    print(f"   Found {len(invoice_rows)} invoices without breakdown_id")

    linked_count = 0
    unlinked_count = 0
    errors = []

    for rowid, invoice_number, description, project_code in invoice_rows:
        # Parse description to get discipline and phase
        discipline, phase = parse_description(description)

        if not discipline or not phase:
            errors.append(f"   ⚠️  {invoice_number}: Cannot parse description '{description}'")
            unlinked_count += 1
            continue

        # Look up breakdown_id from map
        key = (project_code, discipline.lower().strip(), phase.lower().strip())
        breakdown_id = breakdown_map.get(key)

        if not breakdown_id:
            errors.append(f"   ⚠️  {invoice_number}: No matching breakdown for {project_code}/{discipline}/{phase}")
            unlinked_count += 1
            continue

        # Update invoice with breakdown_id
        cursor.execute("""
            UPDATE invoices
            SET breakdown_id = ?
            WHERE rowid = ?
        """, (breakdown_id, rowid))

        linked_count += 1

    conn.commit()

    print(f"   ✅ Linked {linked_count} invoices to breakdown_id")
    print(f"   ⚠️  {unlinked_count} invoices could not be linked\n")

    # Show errors if any
    if errors:
        print("❌ Errors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(error)
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more errors")
        print()

    # Step 3: Verification
    print("✅ Verification:")

    cursor.execute("SELECT COUNT(*) FROM project_fee_breakdown WHERE breakdown_id IS NOT NULL")
    breakdown_with_id = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM project_fee_breakdown")
    total_breakdowns = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices WHERE breakdown_id IS NOT NULL")
    invoices_with_id = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices")
    total_invoices = cursor.fetchone()[0]

    print(f"   project_fee_breakdown: {breakdown_with_id}/{total_breakdowns} have breakdown_id ({100*breakdown_with_id/total_breakdowns:.1f}%)")
    print(f"   invoices: {invoices_with_id}/{total_invoices} linked to breakdown_id ({100*invoices_with_id/total_invoices:.1f}%)")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
