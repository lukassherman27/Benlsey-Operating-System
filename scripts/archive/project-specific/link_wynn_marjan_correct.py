#!/usr/bin/env python3
"""
Link Wynn Marjan invoices based on EXACT mapping from Excel
"""
import sqlite3

DB_PATH = "database/bensley_master.db"
PROJECT_CODE = "22 BK-095"

# Exact mapping from Excel: (invoice_number, amount) -> (scope, phase)
INVOICE_MAPPING = {
    # INDIAN BRASSERIE
    ("I23-018", 124690.00): ("indian-brasserie", "Mobilization"),
    ("I23-036", 51950.00): ("indian-brasserie", "Conceptual Design"),
    ("I23-110", 155850.00): ("indian-brasserie", "Conceptual Design"),
    ("I24-020", 249380.00): ("indian-brasserie", "Design Development"),
    ("I24-079", 124690.00): ("indian-brasserie", "Construction Documents"),
    ("I25-050", 31172.50): ("indian-brasserie", "Construction Observation"),

    # MEDITERRANEAN RESTAURANT
    ("I23-018", 124690.00): ("mediterranean-restaurant", "Mobilization"),  # Duplicate invoice number, different scope
    ("I23-036", 51950.00): ("mediterranean-restaurant", "Conceptual Design"),  # Duplicate
    ("I23-110", 155850.00): ("mediterranean-restaurant", "Conceptual Design"),  # Duplicate
    ("I25-008", 249380.00): ("mediterranean-restaurant", "Design Development"),
    ("I25-063", 124690.00): ("mediterranean-restaurant", "Construction Documents"),
    ("I25-109", 31172.50): ("mediterranean-restaurant", "Construction Observation"),

    # DAY CLUB
    ("I23-018", 249375.00): ("day-club", "Mobilization"),
    ("I23-036", 103906.25): ("day-club", "Conceptual Design"),
    ("I23-110", 311718.75): ("day-club", "Conceptual Design"),
    ("I25-008", 249375.00): ("day-club", "Design Development"),
    ("I25-063", 249375.00): ("day-club", "Design Development"),  # Duplicate invoice, different phase
    ("I25-063", 174562.50): ("day-club", "Construction Documents"),
    ("I25-107", 14962.50): ("day-club", "Construction Documents"),
    ("I25-109", 62343.75): ("day-club", "Construction Observation"),

    # NIGHT CLUB (Interior only)
    ("I24-014", 67500.00): ("night-club", "Mobilization"),
    ("I24-076", 56250.00): ("night-club", "Conceptual Design"),
    ("I25-009", 56250.00): ("night-club", "Conceptual Design"),
    ("I25-009", 67500.00): ("night-club", "Design Development"),
    ("I25-071", 67500.00): ("night-club", "Design Development"),
    ("I25-108", 47250.00): ("night-club", "Construction Documents"),
}

def main():
    print("🔗 Linking Wynn Marjan Invoices (Exact Mapping from Excel)\n")

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
        SELECT invoice_id, invoice_number, invoice_amount, description
        FROM invoices
        WHERE project_id = ?
        ORDER BY invoice_number, invoice_amount
    """, (project_id,))

    invoices = cursor.fetchall()
    print(f"Found {len(invoices)} Wynn Marjan invoice entries\n")

    linked_count = 0
    unlinked_count = 0
    errors = []

    for invoice_id, invoice_number, invoice_amount, description in invoices:
        # Round amount to 2 decimals for matching
        amount_rounded = round(invoice_amount, 2)

        # Look up mapping
        key = (invoice_number, amount_rounded)

        if key in INVOICE_MAPPING:
            scope, phase = INVOICE_MAPPING[key]

            # Determine discipline based on scope
            if scope == "night-club":
                discipline = "Interior"
            else:
                discipline = "Interior & Landscape"

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
                """, (breakdown_id, invoice_id))

                print(f"✅ {invoice_number:12} ${amount_rounded:>12,.2f} → {scope:25} / {phase}")
                linked_count += 1
            else:
                error_msg = f"No breakdown found for {scope}/{discipline}/{phase}"
                print(f"❌ {invoice_number:12} ${amount_rounded:>12,.2f} - {error_msg}")
                errors.append(error_msg)
                unlinked_count += 1
        else:
            print(f"⚠️  {invoice_number:12} ${amount_rounded:>12,.2f} - Not in mapping (desc: {description})")
            unlinked_count += 1

    conn.commit()

    # Summary
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(f"✅ Linked: {linked_count} invoice entries")
    print(f"⚠️  Unlinked: {unlinked_count} entries")

    if errors:
        print(f"\n❌ Errors:")
        for error in set(errors):  # Show unique errors
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
    print(f"   Unlinked: {system_total - system_linked}")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
