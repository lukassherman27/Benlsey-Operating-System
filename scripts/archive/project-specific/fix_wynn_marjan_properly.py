#!/usr/bin/env python3
"""
Fix Wynn Marjan breakdowns properly:
- Indian Brasserie: 5 phases (Interior + Landscape combined)
- Mediterranean Restaurant: 5 phases (Interior + Landscape combined)
- Day Club: 5 phases (Interior + Landscape combined)
- Night Club: 5 phases (Interior ONLY)

Total: 20 breakdowns (not 45)
"""
import sqlite3
import re

DB_PATH = "database/bensley_master.db"
PROJECT_CODE = "22 BK-095"

def slugify(text: str) -> str:
    """Convert text to URL-safe slug"""
    if not text:
        return ''
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text

def generate_breakdown_id(project_code: str, scope: str, discipline: str, phase: str) -> str:
    """Generate breakdown_id with scope"""
    clean_project = project_code.replace(' ', '-').strip()
    clean_scope = slugify(scope)
    clean_discipline = slugify(discipline)
    clean_phase = slugify(phase)
    return f"{clean_project}_{clean_scope}_{clean_discipline}_{clean_phase}"

# Define the 4 scopes with their fee breakdowns
SCOPES = {
    "indian-brasserie": {
        "name": "Indian Brasserie at Casino Level",
        "total_fee": 831250,
        "disciplines": "Interior & Landscape",  # Combined
        "fee_breakdown": {
            "Mobilization": 41562.50,
            "Conceptual Design": 99750.00,
            "Design Development": 166250.00,
            "Construction Documents": 374062.50,
            "Construction Observation": 149625.00
        }
    },
    "mediterranean-restaurant": {
        "name": "Modern Mediterranean Restaurant on Casino Level",
        "total_fee": 831250,
        "disciplines": "Interior & Landscape",  # Combined
        "fee_breakdown": {
            "Mobilization": 41562.50,
            "Conceptual Design": 99750.00,
            "Design Development": 166250.00,
            "Construction Documents": 374062.50,
            "Construction Observation": 149625.00
        }
    },
    "day-club": {
        "name": "Day Club on B2 Level including Dynamic outdoor Bar/swim up Bar",
        "total_fee": 1662500,
        "disciplines": "Interior & Landscape",  # Combined
        "fee_breakdown": {
            "Mobilization": 83125.00,
            "Conceptual Design": 199500.00,
            "Design Development": 332500.00,
            "Construction Documents": 748125.00,
            "Construction Observation": 299250.00
        }
    },
    "night-club": {
        "name": "Interior Design for Night Club",
        "total_fee": 450000,
        "disciplines": "Interior",  # Interior ONLY
        "fee_breakdown": {
            "Mobilization": 22500.00,
            "Conceptual Design": 54000.00,
            "Design Development": 90000.00,
            "Construction Documents": 202500.00,
            "Construction Observation": 81000.00
        }
    }
}

def main():
    print("🔧 Fixing Wynn Marjan Breakdowns Properly\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1: Delete ALL existing Wynn Marjan breakdowns
    print("1️⃣ Deleting all existing Wynn Marjan breakdowns...\n")

    cursor.execute("""
        SELECT COUNT(*) FROM project_fee_breakdown
        WHERE project_code = ?
    """, (PROJECT_CODE,))

    old_count = cursor.fetchone()[0]
    print(f"   Found {old_count} existing breakdowns")

    cursor.execute("DELETE FROM project_fee_breakdown WHERE project_code = ?", (PROJECT_CODE,))
    conn.commit()
    print(f"   ✅ Deleted all {old_count} breakdowns\n")

    # Step 2: Create new breakdowns (ONE per scope per phase)
    print("2️⃣ Creating new breakdowns (1 per scope per phase)...\n")

    created_count = 0

    for scope_slug, scope_data in SCOPES.items():
        print(f"📋 {scope_data['name']}")
        print(f"   Discipline(s): {scope_data['disciplines']}")
        print(f"   Total Fee: ${scope_data['total_fee']:,.2f}\n")

        for phase, phase_fee in scope_data['fee_breakdown'].items():
            breakdown_id = generate_breakdown_id(
                PROJECT_CODE,
                scope_slug,
                scope_data['disciplines'],
                phase
            )

            # Calculate percentage of scope total
            percentage = (phase_fee / scope_data['total_fee']) * 100

            try:
                cursor.execute("""
                    INSERT INTO project_fee_breakdown (
                        breakdown_id, project_code, scope, discipline, phase,
                        phase_fee_usd, percentage_of_total, payment_status,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                """, (
                    breakdown_id,
                    PROJECT_CODE,
                    scope_slug,
                    scope_data['disciplines'],
                    phase,
                    phase_fee,
                    percentage
                ))

                created_count += 1
                print(f"   ✅ {phase} (${phase_fee:,.2f})")

            except sqlite3.IntegrityError as e:
                print(f"   ❌ Error creating {breakdown_id}: {e}")

        print()

    conn.commit()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"🗑️  Deleted: {old_count} old breakdowns")
    print(f"✅ Created: {created_count} new breakdowns")
    print(f"\n   Expected: 20 (5 phases × 4 scopes)")
    print(f"   Actual: {created_count}")

    # Verification
    print("\n📊 Verification:")
    cursor.execute("""
        SELECT scope, discipline, COUNT(*) as breakdown_count, SUM(phase_fee_usd) as total_fee
        FROM project_fee_breakdown
        WHERE project_code = ?
        GROUP BY scope, discipline
    """, (PROJECT_CODE,))

    for scope, discipline, count, fee_sum in cursor.fetchall():
        print(f"   {scope} ({discipline}): {count} breakdowns, ${fee_sum:,.2f}")

    cursor.execute("""
        SELECT COUNT(*) FROM project_fee_breakdown WHERE project_code = ?
    """, (PROJECT_CODE,))
    total_breakdowns = cursor.fetchone()[0]
    print(f"\n   Total breakdowns for {PROJECT_CODE}: {total_breakdowns}")

    # Check invoice linking (should be 0 for now since breakdowns changed)
    cursor.execute("""
        SELECT COUNT(*) FROM invoices i
        JOIN projects p ON i.project_id = p.project_id
        WHERE p.project_code = ? AND i.breakdown_id IS NOT NULL
    """, (PROJECT_CODE,))
    linked_invoices = cursor.fetchone()[0]
    print(f"   Invoices linked: {linked_invoices} (will need to re-link)")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
