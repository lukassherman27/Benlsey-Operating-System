#!/usr/bin/env python3
"""
Regenerate all breakdown_ids to include scope field

OLD FORMAT: {project_code}_{discipline}_{phase}
NEW FORMAT: {project_code}_{scope}_{discipline}_{phase}

This script:
1. Updates all project_fee_breakdown records with new breakdown_ids
2. Updates all invoice.breakdown_id references to match
3. Handles duplicate conflicts
"""
import sqlite3
import re
from typing import Dict, Tuple

DB_PATH = "database/bensley_master.db"

def slugify(text: str) -> str:
    """Convert text to URL-safe slug"""
    if not text:
        return ''
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text

def generate_breakdown_id(project_code: str, scope: str, discipline: str, phase: str) -> str:
    """Generate unique breakdown_id including scope"""
    clean_project = project_code.replace(' ', '-').strip()
    clean_scope = slugify(scope) if scope else 'general'
    clean_discipline = slugify(discipline) if discipline else 'unknown'
    clean_phase = slugify(phase) if phase else 'unknown'

    return f"{clean_project}_{clean_scope}_{clean_discipline}_{clean_phase}"

def main():
    print("🔧 Regenerating breakdown_ids with scope field\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1: Get all project_fee_breakdown records
    print("📋 Step 1: Loading all project_fee_breakdown records...")
    cursor.execute("""
        SELECT breakdown_id, project_code, scope, discipline, phase
        FROM project_fee_breakdown
    """)

    breakdown_rows = cursor.fetchall()
    print(f"   Found {len(breakdown_rows)} records\n")

    # Step 2: Generate new breakdown_ids and create mapping
    print("🔄 Step 2: Generating new breakdown_ids...")
    id_mapping = {}  # old_id -> new_id
    conflicts = []

    for old_id, project_code, scope, discipline, phase in breakdown_rows:
        # Use 'general' if scope is None
        scope = scope or 'general'

        new_id = generate_breakdown_id(project_code, scope, discipline, phase)

        # Check for conflicts (different old_ids mapping to same new_id)
        if new_id in id_mapping.values() and old_id not in id_mapping:
            conflicts.append((old_id, new_id, project_code, scope, discipline, phase))
        else:
            id_mapping[old_id] = new_id

    print(f"   Generated {len(id_mapping)} new breakdown_ids")
    if conflicts:
        print(f"   ⚠️  Found {len(conflicts)} conflicts (will skip these):\n")
        for old_id, new_id, proj, scope, disc, phase in conflicts[:5]:
            print(f"      {old_id} -> {new_id} ({proj}/{scope}/{disc}/{phase})")
        if len(conflicts) > 5:
            print(f"      ... and {len(conflicts) - 5} more")
    print()

    # Step 3: Update project_fee_breakdown records
    print("💾 Step 3: Updating project_fee_breakdown records...")

    updated_count = 0
    skipped_count = 0

    for old_id, new_id in id_mapping.items():
        if old_id == new_id:
            # No change needed
            continue

        try:
            # Check if new_id already exists
            cursor.execute("SELECT breakdown_id FROM project_fee_breakdown WHERE breakdown_id = ?", (new_id,))
            if cursor.fetchone():
                print(f"   ⚠️  Conflict: {new_id} already exists, skipping {old_id}")
                skipped_count += 1
                continue

            # Update the breakdown_id
            cursor.execute("""
                UPDATE project_fee_breakdown
                SET breakdown_id = ?
                WHERE breakdown_id = ?
            """, (new_id, old_id))

            updated_count += 1

        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  IntegrityError updating {old_id} -> {new_id}: {e}")
            skipped_count += 1

    conn.commit()
    print(f"   ✅ Updated {updated_count} breakdown_ids")
    if skipped_count > 0:
        print(f"   ⚠️  Skipped {skipped_count} due to conflicts\n")
    else:
        print()

    # Step 4: Update invoice.breakdown_id references
    print("🔗 Step 4: Updating invoice breakdown_id references...")

    cursor.execute("""
        SELECT invoice_id, breakdown_id
        FROM invoices
        WHERE breakdown_id IS NOT NULL AND breakdown_id != ''
    """)

    invoice_rows = cursor.fetchall()
    print(f"   Found {len(invoice_rows)} invoices with breakdown_id")

    invoice_updated = 0
    invoice_skipped = 0

    for invoice_id, old_breakdown_id in invoice_rows:
        new_breakdown_id = id_mapping.get(old_breakdown_id)

        if not new_breakdown_id:
            # Breakdown not in mapping (probably a conflict)
            invoice_skipped += 1
            continue

        if old_breakdown_id == new_breakdown_id:
            # No change needed
            continue

        cursor.execute("""
            UPDATE invoices
            SET breakdown_id = ?
            WHERE invoice_id = ?
        """, (new_breakdown_id, invoice_id))

        invoice_updated += 1

    conn.commit()
    print(f"   ✅ Updated {invoice_updated} invoice references")
    if invoice_skipped > 0:
        print(f"   ⚠️  Skipped {invoice_skipped} invoices (breakdown not mapped)\n")
    else:
        print()

    # Step 5: Verification
    print("✅ Verification:")

    cursor.execute("SELECT COUNT(*) FROM project_fee_breakdown")
    total_breakdowns = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT breakdown_id) FROM project_fee_breakdown")
    unique_breakdowns = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices WHERE breakdown_id IS NOT NULL")
    invoices_with_breakdown = cursor.fetchone()[0]

    print(f"   project_fee_breakdown: {total_breakdowns} total, {unique_breakdowns} unique breakdown_ids")
    print(f"   invoices: {invoices_with_breakdown} linked to breakdown_ids")

    # Show sample of new breakdown_ids
    print("\n📊 Sample of new breakdown_ids:")
    cursor.execute("""
        SELECT breakdown_id, project_code, scope, discipline, phase
        FROM project_fee_breakdown
        LIMIT 5
    """)
    for breakdown_id, proj, scope, disc, phase in cursor.fetchall():
        print(f"   {breakdown_id}")
        print(f"      → {proj} / {scope or 'general'} / {disc} / {phase}")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
