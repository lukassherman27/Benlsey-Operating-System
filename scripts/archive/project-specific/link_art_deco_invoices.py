#!/usr/bin/env python3
"""
Custom parser for Art Deco invoices
Format: "Concept Design - Sale Center - Landscape"
Parse as: Phase - Scope - Discipline
"""
import sqlite3
import re

DB_PATH = "database/bensley_master.db"
PROJECT_CODE = "23 BK-093"

def slugify(text: str) -> str:
    """Convert text to URL-safe slug"""
    if not text:
        return ''
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text

def parse_art_deco_description(description: str):
    """Parse Art Deco invoice description
    Format: "Phase - Scope - Discipline"
    Example: "Concept Design - Sale Center - Landscape"
    Returns: (phase, scope, discipline) or (None, None, None)
    """
    if not description:
        return None, None, None

    # Split by " - "
    parts = [p.strip() for p in description.split(' - ')]

    if len(parts) == 3:
        phase = parts[0]
        scope = parts[1]
        discipline = parts[2]
        return phase, scope, discipline

    return None, None, None

def main():
    print("🎨 Linking Art Deco Invoices\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get project_id
    cursor.execute("SELECT project_id, project_title FROM projects WHERE project_code = ?", (PROJECT_CODE,))
    project = cursor.fetchone()
    if not project:
        print(f"❌ Project {PROJECT_CODE} not found!")
        return

    project_id, project_title = project
    print(f"📋 Project: {PROJECT_CODE} - {project_title}\n")

    # Get all Art Deco unlinked invoices
    cursor.execute("""
        SELECT invoice_id, invoice_number, description, invoice_amount
        FROM invoices
        WHERE project_id = ?
        AND (breakdown_id IS NULL OR breakdown_id = '')
        ORDER BY invoice_number
    """, (project_id,))

    invoices = cursor.fetchall()
    print(f"Found {len(invoices)} unlinked Art Deco invoices\n")

    linked_count = 0
    unlinked_count = 0
    errors = []

    for invoice_id, invoice_number, description, invoice_amount in invoices:
        # Parse description
        phase, scope, discipline = parse_art_deco_description(description)

        if not phase or not scope or not discipline:
            print(f"⚠️  {invoice_number:12} ${invoice_amount:>12,.2f} - Cannot parse: {description}")
            unlinked_count += 1
            continue

        # Find matching breakdown
        # Try to match with scope in the phase field (the current format)
        cursor.execute("""
            SELECT breakdown_id FROM project_fee_breakdown
            WHERE project_code = ?
            AND discipline = ?
            AND phase LIKE ?
        """, (PROJECT_CODE, discipline, f"%{scope}%"))

        breakdown = cursor.fetchone()

        if not breakdown:
            # Try alternate matching - check if scope is NULL and phase matches
            phase_slug = slugify(phase)
            scope_slug = slugify(scope)
            discipline_slug = slugify(discipline)

            # The breakdown_id format might be: {project}_{discipline}_{phase}-{scope}
            # Try to find by pattern matching
            cursor.execute("""
                SELECT breakdown_id FROM project_fee_breakdown
                WHERE project_code = ?
                AND discipline = ?
                AND (phase LIKE ? OR breakdown_id LIKE ?)
            """, (PROJECT_CODE, discipline, f"%{scope}%", f"%{scope_slug}%"))

            breakdown = cursor.fetchone()

        if breakdown:
            breakdown_id = breakdown[0]
            cursor.execute("""
                UPDATE invoices
                SET breakdown_id = ?
                WHERE invoice_id = ?
            """, (breakdown_id, invoice_id))

            print(f"✅ {invoice_number:12} ${invoice_amount:>12,.2f} → {discipline} / {phase} / {scope}")
            linked_count += 1
        else:
            error_msg = f"No breakdown found for {discipline}/{phase}/{scope}"
            print(f"❌ {invoice_number:12} ${invoice_amount:>12,.2f} - {error_msg}")
            errors.append((invoice_number, description, error_msg))
            unlinked_count += 1

    conn.commit()

    # Summary
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(f"✅ Linked: {linked_count} invoices")
    print(f"❌ Unlinked: {unlinked_count} invoices")

    if errors:
        print(f"\n⚠️  Failed to link:")
        for inv_num, desc, error in errors[:10]:
            print(f"   {inv_num:12} - {desc}")
            print(f"                {error}")

    # Show available breakdowns for reference
    if unlinked_count > 0:
        print(f"\n📋 Available Art Deco breakdowns:")
        cursor.execute("""
            SELECT breakdown_id, discipline, phase
            FROM project_fee_breakdown
            WHERE project_code = ?
            ORDER BY discipline, phase
        """, (PROJECT_CODE,))

        for breakdown_id, discipline, phase in cursor.fetchall()[:10]:
            print(f"   {breakdown_id:50} {discipline:12} / {phase}")

    # Overall status
    cursor.execute("""
        SELECT COUNT(*) FROM invoices
        WHERE project_id = ? AND (breakdown_id IS NULL OR breakdown_id = '')
    """, (project_id,))
    still_unlinked = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices WHERE project_id = ?", (project_id,))
    total = cursor.fetchone()[0]

    print(f"\n📊 Art Deco invoice status:")
    print(f"   Linked: {total - still_unlinked}/{total} ({100*(total-still_unlinked)/total:.1f}%)")
    print(f"   Unlinked: {still_unlinked}")

    # Overall system status
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE breakdown_id IS NOT NULL AND breakdown_id != ''")
    system_linked = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices")
    system_total = cursor.fetchone()[0]

    print(f"\n📊 Overall system:")
    print(f"   Linked: {system_linked}/{system_total} ({100*system_linked/system_total:.1f}%)")
    print(f"   Unlinked: {system_total - system_linked}")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
