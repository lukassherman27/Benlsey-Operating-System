#!/usr/bin/env python3
"""
Create special breakdown categories for:
1. Installment payments (monthly payments not tied to specific phases)
2. Artwork category (for Proscenium Manila mural work)
3. Any other special categories needed

This handles the 19 installment invoices + 2 artwork invoices
"""
import sqlite3
import re

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
    """Generate unique breakdown_id"""
    clean_project = project_code.replace(' ', '-').strip()
    clean_scope = slugify(scope)
    clean_discipline = slugify(discipline)
    clean_phase = slugify(phase)
    return f"{clean_project}_{clean_scope}_{clean_discipline}_{clean_phase}"

# Projects with installment payments
INSTALLMENT_PROJECTS = [
    "20 BK-047",  # Audley Square (4 invoices)
    "22 BK-013",  # Tel Aviv (6 invoices)
    "24 BK-017",  # Ritz Carlton (need to find correct code)
    "24 BK-018",  # Four Seasons Renovation (5 invoices)
]

# Special categories
SPECIAL_CATEGORIES = {
    "23 BK-028": {  # Proscenium Manila
        "category": "artwork",
        "phase": "design-execution",
        "description": "Mural artwork design and execution"
    }
}

def main():
    print("🔧 Creating Special Breakdown Categories\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    total_created = 0
    total_skipped = 0
    errors = []

    # ========================================
    # 1. Create Installment Breakdowns
    # ========================================
    print("💰 Creating Installment Payment breakdowns...\n")

    for project_code in INSTALLMENT_PROJECTS:
        # Verify project exists
        cursor.execute("SELECT project_id, project_title FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()

        if not project:
            print(f"   ⚠️  Project {project_code} not found, skipping")
            continue

        project_id, project_title = project
        breakdown_id = generate_breakdown_id(project_code, "general", "installment", "monthly-payment")

        try:
            # Check if already exists
            cursor.execute("SELECT breakdown_id FROM project_fee_breakdown WHERE breakdown_id = ?", (breakdown_id,))
            if cursor.fetchone():
                print(f"   ⚠️  Already exists: {breakdown_id}")
                total_skipped += 1
            else:
                # Create the breakdown
                cursor.execute("""
                    INSERT INTO project_fee_breakdown (
                        breakdown_id, project_code, scope, discipline, phase,
                        payment_status, created_at
                    ) VALUES (?, ?, 'general', 'installment', 'monthly-payment', 'pending', CURRENT_TIMESTAMP)
                """, (breakdown_id, project_code))

                print(f"   ✅ Created installment breakdown for {project_code} ({project_title})")
                total_created += 1

                # Link all installment invoices to this breakdown
                cursor.execute("""
                    UPDATE invoices
                    SET breakdown_id = ?
                    WHERE project_id = (SELECT project_id FROM projects WHERE project_code = ?)
                    AND (description LIKE '%installment%' OR description LIKE '%monthly%')
                    AND (breakdown_id IS NULL OR breakdown_id = '')
                """, (breakdown_id, project_code))

                linked_count = cursor.rowcount
                print(f"      → Linked {linked_count} installment invoices")

        except sqlite3.IntegrityError as e:
            errors.append(f"{breakdown_id}: {e}")
            total_skipped += 1

    print()

    # ========================================
    # 2. Create Special Category Breakdowns
    # ========================================
    print("🎨 Creating Special Category breakdowns...\n")

    for project_code, category_info in SPECIAL_CATEGORIES.items():
        # Verify project exists
        cursor.execute("SELECT project_id, project_title FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()

        if not project:
            print(f"   ⚠️  Project {project_code} not found, skipping")
            continue

        project_id, project_title = project
        breakdown_id = generate_breakdown_id(
            project_code,
            "general",
            category_info["category"],
            category_info["phase"]
        )

        try:
            # Check if already exists
            cursor.execute("SELECT breakdown_id FROM project_fee_breakdown WHERE breakdown_id = ?", (breakdown_id,))
            if cursor.fetchone():
                print(f"   ⚠️  Already exists: {breakdown_id}")
                total_skipped += 1
            else:
                # Create the breakdown
                cursor.execute("""
                    INSERT INTO project_fee_breakdown (
                        breakdown_id, project_code, scope, discipline, phase,
                        payment_status, created_at
                    ) VALUES (?, ?, 'general', ?, ?, 'pending', CURRENT_TIMESTAMP)
                """, (
                    breakdown_id,
                    project_code,
                    category_info["category"],
                    category_info["phase"]
                ))

                print(f"   ✅ Created {category_info['category']} breakdown for {project_code} ({project_title})")
                print(f"      Description: {category_info['description']}")
                total_created += 1

                # Link relevant invoices
                cursor.execute("""
                    UPDATE invoices
                    SET breakdown_id = ?
                    WHERE project_id = (SELECT project_id FROM projects WHERE project_code = ?)
                    AND description LIKE ?
                    AND (breakdown_id IS NULL OR breakdown_id = '')
                """, (breakdown_id, project_code, f"%{category_info['category']}%"))

                linked_count = cursor.rowcount
                if linked_count > 0:
                    print(f"      → Linked {linked_count} invoices")

        except sqlite3.IntegrityError as e:
            errors.append(f"{breakdown_id}: {e}")
            total_skipped += 1

    print()

    conn.commit()

    # ========================================
    # Summary
    # ========================================
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Created: {total_created} special breakdowns")
    print(f"⚠️  Skipped: {total_skipped} (already exist)")

    if errors:
        print(f"\n❌ Errors:")
        for error in errors[:10]:
            print(f"   {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more")

    # Verification
    print("\n📊 Verification:")

    # Count installment breakdowns
    cursor.execute("""
        SELECT COUNT(*) FROM project_fee_breakdown WHERE discipline = 'installment'
    """)
    installment_count = cursor.fetchone()[0]
    print(f"   Installment breakdowns: {installment_count}")

    # Count installment invoices linked
    cursor.execute("""
        SELECT COUNT(*) FROM invoices i
        JOIN project_fee_breakdown pfb ON i.breakdown_id = pfb.breakdown_id
        WHERE pfb.discipline = 'installment'
    """)
    installment_invoices = cursor.fetchone()[0]
    print(f"   Installment invoices linked: {installment_invoices}")

    # Count special category breakdowns
    cursor.execute("""
        SELECT COUNT(*) FROM project_fee_breakdown
        WHERE discipline NOT IN ('Landscape', 'Architecture', 'Interior', 'installment')
    """)
    special_count = cursor.fetchone()[0]
    print(f"   Special category breakdowns: {special_count}")

    # Overall invoice linking status
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE breakdown_id IS NOT NULL AND breakdown_id != ''")
    total_linked = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices")
    total_invoices = cursor.fetchone()[0]

    print(f"\n   Total invoices: {total_invoices}")
    print(f"   Linked to breakdown: {total_linked} ({100*total_linked/total_invoices:.1f}%)")
    print(f"   Still unlinked: {total_invoices - total_linked}")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
