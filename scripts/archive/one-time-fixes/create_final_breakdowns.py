#!/usr/bin/env python3
"""
Create fee breakdowns for Mandarin Oriental Bali and Capella Ubud
Then link their invoices to reach 100%
"""
import sqlite3

DB_PATH = "database/bensley_master.db"

# Breakdowns based on actual invoiced amounts
PROJECTS = {
    "23 BK-088": {
        "name": "Mandarin Oriental Bali",
        "total_fee": 575000.00,
        "discipline": "General",
        "phases": {
            "Concept Design": 201250.00,
            "Design Development": 201250.00,
            "Construction Documents": 43125.00
        }
    },
    "24 BK-021": {
        "name": "Capella Ubud",
        "total_fee": 750000.00,
        "discipline": "General",
        "phases": {
            "Mobilization": 51750.00,
            "Concept Design": 86250.00
        }
    }
}

def slugify(text: str) -> str:
    """Convert text to URL-safe slug"""
    if not text:
        return ''
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text

def main():
    print("🔨 Creating Final Fee Breakdowns\n")
    print("=" * 90)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    total_created = 0
    total_linked = 0

    for project_code, config in PROJECTS.items():
        print(f"\n📋 {project_code} - {config['name']}")
        print(f"   Total Fee: ${config['total_fee']:,.2f}")
        print(f"   Discipline: {config['discipline']}\n")

        # Get project_id
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            print(f"   ❌ Project not found!")
            continue

        project_id = project[0]

        # Create breakdowns for each phase
        for phase, phase_fee in config['phases'].items():
            # Generate breakdown_id (no scope for simple projects)
            clean_project = project_code.replace(' ', '-')
            clean_discipline = slugify(config['discipline'])
            clean_phase = slugify(phase)
            breakdown_id = f"{clean_project}_{clean_discipline}_{clean_phase}"

            # Check if exists
            cursor.execute("""
                SELECT breakdown_id FROM project_fee_breakdown
                WHERE breakdown_id = ?
            """, (breakdown_id,))

            if cursor.fetchone():
                print(f"   ℹ️  {phase:30} - Breakdown already exists")
            else:
                # Create breakdown
                cursor.execute("""
                    INSERT INTO project_fee_breakdown (
                        breakdown_id,
                        project_code,
                        scope,
                        discipline,
                        phase,
                        phase_fee_usd,
                        payment_status,
                        created_at
                    ) VALUES (?, ?, NULL, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                """, (breakdown_id, project_code, config['discipline'], phase, phase_fee))

                print(f"   ✅ Created: {phase:30} ${phase_fee:>12,.2f}")
                total_created += 1

            # Link invoices for this phase
            cursor.execute("""
                UPDATE invoices
                SET breakdown_id = ?
                WHERE project_id = ?
                AND (breakdown_id IS NULL OR breakdown_id = '')
                AND (description LIKE ? OR description LIKE ?)
            """, (breakdown_id, project_id, f"%{phase}%", f"%{phase.lower()}%"))

            rows_linked = cursor.rowcount
            if rows_linked > 0:
                print(f"      → Linked {rows_linked} invoice(s)")
                total_linked += rows_linked

    conn.commit()

    # Final status
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(f"✅ Created {total_created} new breakdowns")
    print(f"✅ Linked {total_linked} invoices")

    # Overall system status
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN breakdown_id IS NOT NULL AND breakdown_id != '' THEN 1 ELSE 0 END) as linked
        FROM invoices
    """)

    total, linked = cursor.fetchone()
    unlinked = total - linked
    percentage = 100 * linked / total if total > 0 else 0

    print(f"\n📊 Overall System Status:")
    print(f"   Linked: {linked}/{total} ({percentage:.1f}%)")
    print(f"   Unlinked: {unlinked}")

    if unlinked == 0:
        print("\n🎉 100% COMPLETE! All invoices linked!")
    else:
        print(f"\n⚠️  {unlinked} invoices still unlinked")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
