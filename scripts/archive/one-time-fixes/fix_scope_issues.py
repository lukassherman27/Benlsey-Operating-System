#!/usr/bin/env python3
"""
Fix scope-related issues:
1. Change scope='general' to scope=NULL for simple single-scope projects
2. Delete Architecture breakdowns from Wynn Marjan (only keep Interior + Landscape)
3. Update breakdown_ids to remove "general" from simple projects
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
    """Generate breakdown_id - if scope is NULL, omit it"""
    clean_project = project_code.replace(' ', '-').strip()
    clean_discipline = slugify(discipline) if discipline else 'unknown'
    clean_phase = slugify(phase) if phase else 'unknown'

    if scope:
        clean_scope = slugify(scope)
        return f"{clean_project}_{clean_scope}_{clean_discipline}_{clean_phase}"
    else:
        # Simple project - no scope in breakdown_id
        return f"{clean_project}_{clean_discipline}_{clean_phase}"

def main():
    print("🔧 Fixing Scope Issues\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ========================================
    # Issue 1: Delete Wynn Marjan Architecture breakdowns
    # ========================================
    print("1️⃣ Deleting Architecture breakdowns from Wynn Marjan...\n")

    cursor.execute("""
        SELECT breakdown_id, scope, phase
        FROM project_fee_breakdown
        WHERE project_code = '22 BK-095'
        AND discipline = 'Architecture'
    """)

    arch_breakdowns = cursor.fetchall()
    print(f"   Found {len(arch_breakdowns)} Architecture breakdowns")

    for breakdown_id, scope, phase in arch_breakdowns:
        print(f"   🗑️  Deleting: {breakdown_id} ({scope}/{phase})")
        cursor.execute("DELETE FROM project_fee_breakdown WHERE breakdown_id = ?", (breakdown_id,))

    conn.commit()
    print(f"   ✅ Deleted {len(arch_breakdowns)} Architecture breakdowns\n")

    # ========================================
    # Issue 2: Change scope='general' to scope=NULL for single-scope projects
    # ========================================
    print("2️⃣ Removing 'general' scope from simple projects...\n")

    # Get all projects with ONLY 'general' scope (no other scopes)
    cursor.execute("""
        SELECT DISTINCT p.project_code
        FROM projects p
        JOIN project_fee_breakdown pfb ON p.project_code = pfb.project_code
        WHERE pfb.scope = 'general'
        AND p.project_code NOT IN (
            SELECT project_code
            FROM project_fee_breakdown
            WHERE scope != 'general' AND scope IS NOT NULL
        )
    """)

    simple_projects = [row[0] for row in cursor.fetchall()]
    print(f"   Found {len(simple_projects)} simple single-scope projects")

    # For each simple project, change scope='general' to NULL and update breakdown_id
    updated_count = 0
    id_mapping = {}  # old_id -> new_id

    for project_code in simple_projects:
        cursor.execute("""
            SELECT breakdown_id, discipline, phase
            FROM project_fee_breakdown
            WHERE project_code = ? AND scope = 'general'
        """, (project_code,))

        for old_id, discipline, phase in cursor.fetchall():
            # Generate new breakdown_id without scope
            new_id = generate_breakdown_id(project_code, None, discipline, phase)

            if old_id != new_id:
                print(f"   🔄 {old_id} → {new_id}")

                try:
                    # Update breakdown
                    cursor.execute("""
                        UPDATE project_fee_breakdown
                        SET scope = NULL, breakdown_id = ?
                        WHERE breakdown_id = ?
                    """, (new_id, old_id))

                    id_mapping[old_id] = new_id
                    updated_count += 1

                except sqlite3.IntegrityError as e:
                    print(f"      ⚠️  Error: {e}")

    conn.commit()
    print(f"   ✅ Updated {updated_count} breakdowns to remove 'general' scope\n")

    # ========================================
    # Issue 3: Update invoice.breakdown_id references
    # ========================================
    print("3️⃣ Updating invoice breakdown_id references...\n")

    invoice_updated = 0
    for old_id, new_id in id_mapping.items():
        cursor.execute("""
            UPDATE invoices
            SET breakdown_id = ?
            WHERE breakdown_id = ?
        """, (new_id, old_id))

        invoice_updated += cursor.rowcount

    conn.commit()
    print(f"   ✅ Updated {invoice_updated} invoice references\n")

    # ========================================
    # Verification
    # ========================================
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    # Check Wynn Marjan breakdown count
    cursor.execute("""
        SELECT COUNT(*), discipline
        FROM project_fee_breakdown
        WHERE project_code = '22 BK-095'
        GROUP BY discipline
    """)
    print("\n📊 Wynn Marjan breakdown count by discipline:")
    for count, discipline in cursor.fetchall():
        print(f"   {discipline}: {count}")

    # Check scope usage
    cursor.execute("""
        SELECT
            CASE WHEN scope IS NULL THEN 'NULL' ELSE scope END as scope_val,
            COUNT(*) as count
        FROM project_fee_breakdown
        GROUP BY scope
        ORDER BY count DESC
    """)
    print("\n📊 Breakdown count by scope:")
    for scope_val, count in cursor.fetchall():
        print(f"   {scope_val}: {count}")

    # Sample breakdown_ids
    print("\n📋 Sample breakdown_ids:")
    cursor.execute("""
        SELECT breakdown_id, project_code, scope, discipline, phase
        FROM project_fee_breakdown
        LIMIT 5
    """)
    for breakdown_id, proj, scope, disc, phase in cursor.fetchall():
        print(f"   {breakdown_id}")
        print(f"      → {proj} / scope={scope or 'NULL'} / {disc} / {phase}")

    # Check invoice linking
    cursor.execute("SELECT COUNT(*) FROM invoices WHERE breakdown_id IS NOT NULL AND breakdown_id != ''")
    linked = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices")
    total = cursor.fetchone()[0]

    print(f"\n📊 Invoice linking status:")
    print(f"   Linked: {linked}/{total} ({100*linked/total:.1f}%)")
    print(f"   Unlinked: {total - linked}")

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
