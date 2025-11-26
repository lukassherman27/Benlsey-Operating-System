#!/usr/bin/env python3
"""
Link Wynn Marjan invoices to correct scope breakdowns

Strategy:
- Invoices with 3 entries (same invoice number, same amount pattern 1:1:2) → link to Indian Brasserie, Mediterranean Restaurant, Day Club
- Invoices with "Interior" in description → link to Night Club (Interior only)
- Use amount ratios to determine which entry goes to which scope
"""
import sqlite3
from collections import defaultdict

DB_PATH = "database/bensley_master.db"
PROJECT_CODE = "22 BK-095"

def parse_phase(description: str) -> str:
    """Extract phase from description"""
    if not description:
        return None

    # Remove trailing " - "
    desc = description.strip().rstrip('-').strip()

    phase_mapping = {
        'mobilization': 'Mobilization',
        'concept design': 'Conceptual Design',
        'conceptual design': 'Conceptual Design',
        'design development': 'Design Development',
        'construction documents': 'Construction Documents',
        'construction observation': 'Construction Observation'
    }

    desc_lower = desc.lower()
    for key, value in phase_mapping.items():
        if key in desc_lower:
            return value

    return None

def main():
    print("🔗 Linking Wynn Marjan Invoices to Scopes\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get project_id
    cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (PROJECT_CODE,))
    project = cursor.fetchone()
    if not project:
        print(f"❌ Project {PROJECT_CODE} not found!")
        return

    project_id = project[0]

    # Get all Wynn invoices
    cursor.execute("""
        SELECT invoice_id, invoice_number, description, invoice_amount, invoice_date
        FROM invoices
        WHERE project_id = ?
        ORDER BY invoice_date, invoice_number, invoice_amount
    """, (project_id,))

    invoices = cursor.fetchall()
    print(f"Found {len(invoices)} Wynn Marjan invoice entries\n")

    # Group by invoice number to find multi-entry invoices
    invoice_groups = defaultdict(list)
    for inv_id, inv_num, desc, amount, date in invoices:
        invoice_groups[inv_num].append((inv_id, desc, amount, date))

    linked_count = 0
    skipped_count = 0
    errors = []

    # Process each invoice group
    for inv_num, entries in invoice_groups.items():
        phase = None

        # Parse phase from first entry
        for inv_id, desc, amount, date in entries:
            phase = parse_phase(desc)
            if phase:
                break

        if not phase:
            print(f"⚠️  {inv_num}: Cannot determine phase from descriptions")
            skipped_count += len(entries)
            continue

        # Check if this is a Night Club invoice (has "Interior" in description)
        is_night_club = any("Interior" in (desc or "") for inv_id, desc, amount, date in entries if desc)

        if is_night_club:
            # Night Club invoices - link to night-club scope, Interior discipline
            print(f"🌙 {inv_num} ({phase}) - Night Club (Interior only):")

            for inv_id, desc, amount, date in entries:
                if "Interior" in (desc or ""):
                    # Find matching breakdown
                    cursor.execute("""
                        SELECT breakdown_id FROM project_fee_breakdown
                        WHERE project_code = ?
                        AND scope = 'night-club'
                        AND discipline = 'Interior'
                        AND phase = ?
                    """, (PROJECT_CODE, phase))

                    breakdown = cursor.fetchone()
                    if breakdown:
                        breakdown_id = breakdown[0]
                        cursor.execute("""
                            UPDATE invoices
                            SET breakdown_id = ?
                            WHERE invoice_id = ?
                        """, (breakdown_id, inv_id))

                        print(f"   ✅ ${amount:,.2f} → night-club / Interior / {phase}")
                        linked_count += 1
                    else:
                        print(f"   ❌ No matching breakdown for night-club / Interior / {phase}")
                        skipped_count += 1

        else:
            # Multi-scope invoices - 3 entries for Indian Brasserie, Mediterranean Restaurant, Day Club
            if len(entries) == 3:
                print(f"🏨 {inv_num} ({phase}) - Multi-scope (3 entries):")

                # Sort by amount to assign to scopes (smallest 2 are equal, largest is Day Club)
                sorted_entries = sorted(entries, key=lambda x: x[2])  # Sort by amount

                # Assign scopes
                scope_assignments = [
                    ('indian-brasserie', 'Interior & Landscape'),
                    ('mediterranean-restaurant', 'Interior & Landscape'),
                    ('day-club', 'Interior & Landscape')
                ]

                for i, (inv_id, desc, amount, date) in enumerate(sorted_entries):
                    if i < len(scope_assignments):
                        scope, discipline = scope_assignments[i]

                        # Find matching breakdown
                        cursor.execute("""
                            SELECT breakdown_id FROM project_fee_breakdown
                            WHERE project_code = ?
                            AND scope = ?
                            AND discipline = ?
                            AND phase = ?
                        """, (PROJECT_CODE, scope, discipline, phase))

                        breakdown = cursor.fetchone()
                        if breakdown:
                            breakdown_id = breakdown[0]
                            cursor.execute("""
                                UPDATE invoices
                                SET breakdown_id = ?
                                WHERE invoice_id = ?
                            """, (breakdown_id, inv_id))

                            print(f"   ✅ ${amount:,.2f} → {scope} / {discipline} / {phase}")
                            linked_count += 1
                        else:
                            print(f"   ❌ No matching breakdown for {scope} / {discipline} / {phase}")
                            skipped_count += 1
            else:
                print(f"⚠️  {inv_num}: Expected 3 entries, found {len(entries)} (skipping)")
                skipped_count += len(entries)

    conn.commit()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Linked: {linked_count} invoice entries")
    print(f"⚠️  Skipped: {skipped_count} entries")

    if errors:
        print(f"\n❌ Errors:")
        for error in errors[:10]:
            print(f"   {error}")

    # Verification
    cursor.execute("""
        SELECT COUNT(*) FROM invoices
        WHERE project_id = ? AND (breakdown_id IS NULL OR breakdown_id = '')
    """, (project_id,))
    still_unlinked = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices WHERE project_id = ?", (project_id,))
    total = cursor.fetchone()[0]

    print(f"\n📊 Wynn Marjan invoice status:")
    print(f"   Linked: {total - still_unlinked}/{total} ({100*(total-still_unlinked)/total:.1f}%)")
    print(f"   Unlinked: {still_unlinked}")

    # Overall system status
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE breakdown_id IS NOT NULL AND breakdown_id != ''")
    system_linked = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices")
    system_total = cursor.fetchone()[0]

    print(f"\n📊 Overall system:")
    print(f"   Linked: {system_linked}/{system_total} ({100*system_linked/system_total:.1f}%)")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
