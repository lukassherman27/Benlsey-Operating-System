#!/usr/bin/env python3
"""
Link Ultra Luxury Beach Resort mobilization invoice
"""
import sqlite3

DB_PATH = "database/bensley_master.db"
PROJECT_CODE = "23 BK-050"

def main():
    print("🔗 Linking Ultra Luxury Beach Resort Mobilization\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if mobilization breakdown exists
    cursor.execute("""
        SELECT breakdown_id FROM project_fee_breakdown
        WHERE project_code = ?
        AND phase LIKE '%mobilization%'
    """, (PROJECT_CODE,))

    breakdown = cursor.fetchone()

    if not breakdown:
        print("Creating mobilization breakdown...")

        # Create mobilization breakdown
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
            ) VALUES (
                '23-BK-050_general_mobilization',
                '23 BK-050',
                NULL,
                'General',
                'Mobilization',
                400000.00,
                'pending',
                CURRENT_TIMESTAMP
            )
        """)
        breakdown_id = '23-BK-050_general_mobilization'
        print(f"✅ Created breakdown: {breakdown_id}")
    else:
        breakdown_id = breakdown[0]
        print(f"✅ Found existing breakdown: {breakdown_id}")

    # Link the invoice
    cursor.execute("""
        UPDATE invoices
        SET breakdown_id = ?
        WHERE invoice_number = 'I24-031'
        AND project_id = (SELECT project_id FROM projects WHERE project_code = ?)
    """, (breakdown_id, PROJECT_CODE))

    rows_updated = cursor.rowcount
    print(f"✅ Linked invoice I24-031: {rows_updated} row(s) updated")

    conn.commit()

    # Verify
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

    conn.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
