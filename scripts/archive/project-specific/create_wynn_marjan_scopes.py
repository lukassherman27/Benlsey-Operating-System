#!/usr/bin/env python3
"""
Create multi-scope breakdowns for Wynn Marjan (22 BK-095)

Wynn Marjan has 4 separate scopes, each with full phase breakdown:
1. Indian Brasserie at Casino level (#473) - $831,250
2. Modern Mediterranean Restaurant on Casino Level (#477) - $831,250
3. Day Club on B2 Level including Dynamic outdoor Bar/swim up Bar (#650) - $1,662,500
4. Interior Design for Night Club (Addendum) - $450,000

Each scope has phases: Mobilization, Conceptual Design, Design Development, Construction Documents, Construction Observation
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
    """Generate unique breakdown_id"""
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
        "fee_breakdown": {
            "Mobilization": 41562.50,           # 5%
            "Conceptual Design": 99750.00,      # 12%
            "Design Development": 166250.00,    # 20%
            "Construction Documents": 374062.50, # 45%
            "Construction Observation": 149625.00 # 18%
        }
    },
    "mediterranean-restaurant": {
        "name": "Modern Mediterranean Restaurant on Casino Level",
        "total_fee": 831250,
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
        "fee_breakdown": {
            "Mobilization": 83125.00,           # 5%
            "Conceptual Design": 199500.00,     # 12%
            "Design Development": 332500.00,    # 20%
            "Construction Documents": 748125.00, # 45%
            "Construction Observation": 299250.00 # 18%
        }
    },
    "night-club": {
        "name": "Interior Design for Night Club",
        "total_fee": 450000,
        "fee_breakdown": {
            "Mobilization": 22500.00,           # 5%
            "Conceptual Design": 54000.00,      # 12%
            "Design Development": 90000.00,     # 20%
            "Construction Documents": 202500.00, # 45%
            "Construction Observation": 81000.00 # 18%
        }
    }
}

# Disciplines that apply to each scope
DISCIPLINES = ["Interior", "Landscape", "Architecture"]

def main():
    print("🏨 Creating Wynn Marjan Multi-Scope Breakdowns\n")
    print(f"Project: {PROJECT_CODE}")
    print(f"Scopes: {len(SCOPES)}\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # First, verify the project exists
    cursor.execute("SELECT project_id, project_title, total_fee_usd FROM projects WHERE project_code = ?", (PROJECT_CODE,))
    project = cursor.fetchone()

    if not project:
        print(f"❌ Error: Project {PROJECT_CODE} not found in database!")
        conn.close()
        return

    project_id, project_title, total_fee = project
    print(f"✅ Found project: {project_title}")
    print(f"   Total Fee: ${total_fee:,.2f}\n")

    total_created = 0
    total_skipped = 0
    errors = []

    # Create breakdowns for each scope
    for scope_slug, scope_data in SCOPES.items():
        print(f"📋 Creating breakdowns for scope: {scope_data['name']}")
        print(f"   Total Fee: ${scope_data['total_fee']:,.2f}\n")

        for discipline in DISCIPLINES:
            for phase, phase_fee in scope_data['fee_breakdown'].items():
                breakdown_id = generate_breakdown_id(PROJECT_CODE, scope_slug, discipline, phase)

                # Calculate percentage of scope total
                percentage = (phase_fee / scope_data['total_fee']) * 100

                try:
                    # Check if already exists
                    cursor.execute("SELECT breakdown_id FROM project_fee_breakdown WHERE breakdown_id = ?", (breakdown_id,))
                    if cursor.fetchone():
                        print(f"   ⚠️  Already exists: {breakdown_id}")
                        total_skipped += 1
                        continue

                    # Insert the breakdown
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
                        discipline,
                        phase,
                        phase_fee,
                        percentage
                    ))

                    total_created += 1
                    print(f"   ✅ Created: {discipline} - {phase} (${phase_fee:,.2f})")

                except sqlite3.IntegrityError as e:
                    errors.append(f"{breakdown_id}: {e}")
                    total_skipped += 1

        print()

    conn.commit()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Created: {total_created} breakdowns")
    print(f"⚠️  Skipped: {total_skipped} (already exist)")

    if errors:
        print(f"\n❌ Errors:")
        for error in errors[:10]:
            print(f"   {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more")

    # Verification
    print("\n📊 Verification:")
    cursor.execute("""
        SELECT scope, COUNT(*) as breakdown_count, SUM(phase_fee_usd) as total_fee
        FROM project_fee_breakdown
        WHERE project_code = ?
        GROUP BY scope
    """, (PROJECT_CODE,))

    for scope, count, fee_sum in cursor.fetchall():
        print(f"   {scope}: {count} breakdowns, ${fee_sum:,.2f} total")

    cursor.execute("""
        SELECT COUNT(*) FROM project_fee_breakdown WHERE project_code = ?
    """, (PROJECT_CODE,))
    total_breakdowns = cursor.fetchone()[0]
    print(f"\n   Total breakdowns for {PROJECT_CODE}: {total_breakdowns}")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
