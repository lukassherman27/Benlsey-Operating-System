#!/usr/bin/env python3
"""
Update ALL project financial data with CORRECT totals from accountant's PDF
Date: 2025-11-14
"""

import sqlite3
from datetime import datetime
from decimal import Decimal

# Database path
DB_PATH = '/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db'

# CORRECTED PROJECT DATA - Aggregated totals from detailed analysis
CORRECTED_PROJECTS = {
    '20 BK-047': {
        'name': 'Audley Square House-Communal Spa',
        'total_fee': 148000.00,
        'outstanding': 8000.00,
        'remaining': 116000.00,
        'paid_to_date': 24000.00,
        'expiry': '2026-09-30',
        'status': 'CA',
        'client': 'Uri Mizrahi',
    },
    '19 BK-018': {
        'name': 'Villa Project in Ahmedabad, India (Landscape/Arch/Interior)',
        'total_fee': 1900000.00,
        'outstanding': 152000.00,
        'remaining': 0.00,
        'paid_to_date': 1748000.00,
        'expiry': '2023-11-30',
        'status': 'CO',
        'client': 'Ingit Anand / Kalpesh Shah',
    },
    '22 BK-013': {
        'name': 'Tel Aviv High Rise Project (Landscape/Interior + Monthly)',
        'total_fee': 4155000.00,
        'outstanding': 231000.00,
        'remaining': 2067000.00,
        'paid_to_date': 1857000.00,
        'expiry': '2025-08-31',
        'status': 'DD',
        'client': 'Ronen Lavan',
    },
    '22 BK-046': {
        'name': 'Resort and Hotel Project at Nusa Penida (Landscape/Arch/Interior)',
        'total_fee': 1700000.00,
        'outstanding': 255000.00,
        'remaining': 765000.00,
        'paid_to_date': 680000.00,
        'expiry': '2026-06-30',
        'status': 'DD',
        'client': 'Suwito Gunawan',
    },
    '22 BK-095': {
        'name': 'Wynn Al Marjan Island (Indian Brasserie + Mediterranean Restaurant + Day Club + Night Club)',
        'total_fee': 3775000.00,
        'outstanding': 155728.75,
        'remaining': 521666.25,
        'paid_to_date': 3097605.00,
        'expiry': '2026-12-31',
        'status': 'CO',
        'client': 'Wynn Al Marjan',
    },
    '25 BK-039': {
        'name': 'Wynn Al Marjan Island - Additional Service',
        'total_fee': 250000.00,
        'outstanding': 0.00,
        'remaining': 250000.00,
        'paid_to_date': 0.00,
        'expiry': '2026-12-31',
        'status': 'Design',
        'client': 'Wynn Al Marjan',
    },
    '23 BK-009': {
        'name': 'Villa Project in Ahmedabad, India (Le Parqe Sector 5 and 7)',
        'total_fee': 730000.00,
        'outstanding': 219000.00,
        'remaining': 0.00,
        'paid_to_date': 511000.00,
        'expiry': '2024-09-30',
        'status': 'CD',
        'client': 'Le Parqe',
    },
    '23 BK-028': {
        'name': 'Proscenium Penthouse in Manila + Mural',
        'total_fee': 1797520.00,
        'outstanding': 0.00,
        'remaining': 168000.00,
        'paid_to_date': 1629520.00,
        'expiry': '2024-11-30',
        'status': 'CO',
        'client': 'Proscenium',
    },
    '23 BK-088': {
        'name': 'Mandarin Oriental Bali Hotel and Branded Residential',
        'total_fee': 575000.00,
        'outstanding': 43125.00,
        'remaining': 129375.00,
        'paid_to_date': 402500.00,
        'expiry': '2025-09-30',
        'status': 'CD',
        'client': 'Mandarin Oriental',
    },
    '25 BK-030': {
        'name': 'Beach Club at Mandarin Oriental Bali (Arch/Interior)',
        'total_fee': 550000.00,
        'outstanding': 137500.00,
        'remaining': 330000.00,
        'paid_to_date': 82500.00,
        'expiry': '2027-06-30',
        'status': 'CD',
        'client': 'Mandarin Oriental',
    },
    '25 BK-018': {
        'name': 'The Ritz Carlton Hotel Nanyan Bay, China (Extension)',
        'total_fee': 225000.00,
        'outstanding': 56250.00,
        'remaining': 56250.00,
        'paid_to_date': 112500.00,
        'expiry': '2026-03-31',
        'status': 'Extension',
        'client': 'Ritz Carlton',
    },
    '23 BK-071': {
        'name': 'St. Regis Hotel in Thousand Island Lake, China (Interior)',
        'total_fee': 1350000.00,
        'outstanding': 101250.00,
        'remaining': 708750.00,
        'paid_to_date': 540000.00,
        'expiry': '2026-02-28',
        'status': 'DD',
        'client': 'St. Regis',
    },
    '23 BK-096': {
        'name': 'St. Regis Hotel in Thousand Island Lake (Landscape/Arch Addendum)',
        'total_fee': 500000.00,
        'outstanding': 75000.00,
        'remaining': 112500.00,
        'paid_to_date': 312500.00,
        'expiry': '2026-02-28',
        'status': 'CD',
        'client': 'St. Regis',
    },
    '23 BK-067': {
        'name': 'Treasure Island Resort, Intercontinental Hotel (Interior)',
        'total_fee': 1200000.00,
        'outstanding': 0.00,
        'remaining': 648000.00,
        'paid_to_date': 552000.00,
        'expiry': '2025-11-30',
        'status': 'DD',
        'client': 'Intercontinental',
    },
    '23 BK-080': {
        'name': 'Treasure Island Resort, Intercontinental Hotel (Landscape)',
        'total_fee': 400000.00,
        'outstanding': 0.00,
        'remaining': 216000.00,
        'paid_to_date': 184000.00,
        'expiry': '2025-11-30',
        'status': 'DD',
        'client': 'Intercontinental',
    },
    '23 BK-093': {
        'name': '25 Downtown Mumbai (Landscape/Interior + Redesign)',
        'total_fee': 3250000.00,
        'outstanding': 262500.00,
        'remaining': 600000.00,
        'paid_to_date': 2387500.00,
        'expiry': '2025-11-30',
        'status': 'CD',
        'client': 'Khilen Shah',
    },
    '23 BK-089': {
        'name': "Jyoti's farm house in Delhi, India",
        'total_fee': 1000000.00,
        'outstanding': 0.00,
        'remaining': 225000.00,
        'paid_to_date': 775000.00,
        'expiry': '2025-12-31',
        'status': 'CD',
        'client': 'Jyoti',
    },
    '23 BK-050': {
        'name': 'Ultra Luxury Beach Resort Hotel and Residence, Bodrum, Turkey',
        'total_fee': 4650000.00,
        'outstanding': 0.00,
        'remaining': 2561359.38,
        'paid_to_date': 2088640.63,
        'expiry': '2027-05-31',
        'status': 'SD',
        'client': 'Elif Gizem KAYA / Semra HALEPLI',
    },
    '24 BK-021': {
        'name': 'Capella Hotel and Resort, Ubud Bali (Extension)',
        'total_fee': 345000.00,
        'outstanding': 43125.00,
        'remaining': 207000.00,
        'paid_to_date': 94875.00,
        'expiry': '2026-03-31',
        'status': 'CD',
        'client': 'Capella',
    },
    '24 BK-018': {
        'name': 'Luang Prabang Heritage Arcade and Hotel (Landscape/Arch/Interior)',
        'total_fee': 1450000.00,
        'outstanding': 0.00,
        'remaining': 870000.00,
        'paid_to_date': 580000.00,
        'expiry': '2026-03-31',
        'status': 'CD',
        'client': 'Shinta Mani',
    },
    '24 BK-029': {
        'name': 'Qinhu Resort Project, China (Landscape/Arch/Interior)',
        'total_fee': 3250000.00,
        'outstanding': 650000.00,
        'remaining': 2356250.00,
        'paid_to_date': 243750.00,
        'expiry': '2026-09-30',
        'status': 'CD',
        'client': 'Qinhu',
    },
    '19 BK-052': {
        'name': 'The Siam Hotel Chiangmai (Landscape/Arch/Interior)',
        'total_fee': 814500.00,
        'outstanding': 0.00,
        'remaining': 445800.00,
        'paid_to_date': 368700.00,
        'expiry': '2026-12-31',
        'status': 'DD',
        'client': 'The Siam',
    },
    '24 BK-033': {
        'name': 'Renovation Work for Three of Four Seasons Properties',
        'total_fee': 1500000.00,
        'outstanding': 34375.00,
        'remaining': 1031250.00,
        'paid_to_date': 434375.00,
        'expiry': '2028-04-30',
        'status': 'Monthly',
        'client': 'Four Seasons',
    },
    '24 BK-077': {
        'name': 'Restaurant at the Raffles Hotel, Singapore',
        'total_fee': 195000.00,
        'outstanding': 0.00,
        'remaining': 29250.00,
        'paid_to_date': 165750.00,
        'expiry': '2026-01-31',
        'status': 'CO',
        'client': 'Raffles',
    },
    '24 BK-058': {
        'name': 'Luxury Resort Development at Fenfushi Island, Maldives (Landscape/Arch/Interior)',
        'total_fee': 2990000.00,
        'outstanding': 526000.00,
        'remaining': 448500.00,
        'paid_to_date': 2015500.00,
        'expiry': '2026-11-30',
        'status': 'CD',
        'client': 'Bharath / Chen Huifang',
    },
    '24 BK-074': {
        'name': '43 Dang Thai Mai Project, Hanoi, Vietnam (Landscape/Arch/Interior)',
        'total_fee': 4900000.00,
        'outstanding': 1001725.00,
        'remaining': 808500.00,
        'paid_to_date': 3089775.00,
        'expiry': '2024-12-31',
        'status': 'CD',
        'client': 'Vietnam',
    },
    '25 BK-015': {
        'name': 'Shinta Mani Mustang, Nepal (Two hotels)',
        'total_fee': 300000.00,
        'outstanding': 120000.00,
        'remaining': 135000.00,
        'paid_to_date': 45000.00,
        'expiry': '2027-05-31',
        'status': 'DD',
        'client': 'Shinta Mani',
    },
    '25 BK-017': {
        'name': "TARC's Luxury Branded Residence Project in New Delhi (Landscape/Interior)",
        'total_fee': 3000000.00,
        'outstanding': 131250.00,
        'remaining': 2418750.00,
        'paid_to_date': 450000.00,
        'expiry': '2029-02-28',
        'status': 'CD',
        'client': 'TARC',
    },
    '25 BK-033': {
        'name': 'The Ritz Carlton Reserve, Nusa Dua, Bali (Landscape/Arch/Interior + Branding)',
        'total_fee': 3275000.00,
        'outstanding': 393750.00,
        'remaining': 1983750.00,
        'paid_to_date': 1054750.00,
        'expiry': '2027-07-31',
        'status': 'CD',
        'client': 'Ritz Carlton',
    },
}


def get_current_totals(conn):
    """Get current financial totals from active projects"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) as project_count,
            COALESCE(SUM(total_fee_usd), 0) as total_fees,
            COALESCE(SUM(paid_to_date_usd), 0) as total_paid,
            COALESCE(SUM(outstanding_usd), 0) as total_outstanding,
            COALESCE(SUM(remaining_work_usd), 0) as total_remaining
        FROM proposals
        WHERE is_active_project = 1
    """)
    return cursor.fetchone()


def reset_active_projects(conn):
    """Reset all active project flags"""
    cursor = conn.cursor()
    cursor.execute("UPDATE proposals SET is_active_project = 0")
    conn.commit()
    print(f"Reset is_active_project flag for all proposals")


def update_or_insert_project(conn, project_code, data):
    """Update existing project or insert new one"""
    cursor = conn.cursor()

    # Check if project exists
    cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (project_code,))
    existing = cursor.fetchone()

    if existing:
        # UPDATE existing project
        cursor.execute("""
            UPDATE proposals
            SET
                project_name = ?,
                client_company = ?,
                total_fee_usd = ?,
                outstanding_usd = ?,
                remaining_work_usd = ?,
                paid_to_date_usd = ?,
                contract_expiry_date = ?,
                project_phase = ?,
                is_active_project = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE project_code = ?
        """, (
            data['name'],
            data['client'],
            data['total_fee'],
            data['outstanding'],
            data['remaining'],
            data['paid_to_date'],
            data['expiry'],
            data['status'],
            project_code
        ))
        return 'updated', existing[0]
    else:
        # INSERT new project
        cursor.execute("""
            INSERT INTO proposals (
                project_code,
                project_name,
                client_company,
                total_fee_usd,
                outstanding_usd,
                remaining_work_usd,
                paid_to_date_usd,
                contract_expiry_date,
                project_phase,
                is_active_project,
                status,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            project_code,
            data['name'],
            data['client'],
            data['total_fee'],
            data['outstanding'],
            data['remaining'],
            data['paid_to_date'],
            data['expiry'],
            data['status']
        ))
        return 'inserted', cursor.lastrowid


def main():
    print("=" * 80)
    print("UPDATE ALL PROJECT FINANCIAL DATA")
    print("=" * 80)
    print(f"Database: {DB_PATH}")
    print(f"Total projects to process: {len(CORRECTED_PROJECTS)}")
    print("=" * 80)
    print()

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    try:
        # Get BEFORE totals
        print("BEFORE UPDATE:")
        print("-" * 80)
        before_stats = get_current_totals(conn)
        print(f"Active Projects: {before_stats[0]}")
        print(f"Total Fees:      ${before_stats[1]:,.2f}")
        print(f"Paid to Date:    ${before_stats[2]:,.2f}")
        print(f"Outstanding:     ${before_stats[3]:,.2f}")
        print(f"Remaining:       ${before_stats[4]:,.2f}")
        print()

        # Step 1: Reset all active project flags
        print("Step 1: Resetting all active project flags...")
        reset_active_projects(conn)
        print()

        # Step 2: Update/Insert all projects
        print("Step 2: Updating/Inserting all projects...")
        print("-" * 80)

        updated_count = 0
        inserted_count = 0

        for project_code, data in CORRECTED_PROJECTS.items():
            action, project_id = update_or_insert_project(conn, project_code, data)

            if action == 'updated':
                updated_count += 1
                print(f"UPDATED: {project_code} - {data['name'][:50]}")
            else:
                inserted_count += 1
                print(f"INSERTED: {project_code} - {data['name'][:50]}")

        # Commit all changes
        conn.commit()
        print()
        print(f"Summary: {updated_count} updated, {inserted_count} inserted")
        print()

        # Step 3: Verify and show AFTER totals
        print("AFTER UPDATE:")
        print("-" * 80)
        after_stats = get_current_totals(conn)
        print(f"Active Projects: {after_stats[0]}")
        print(f"Total Fees:      ${after_stats[1]:,.2f}")
        print(f"Paid to Date:    ${after_stats[2]:,.2f}")
        print(f"Outstanding:     ${after_stats[3]:,.2f}")
        print(f"Remaining:       ${after_stats[4]:,.2f}")
        print()

        # Step 4: Verify against expected totals
        print("VERIFICATION:")
        print("-" * 80)
        expected_paid = 25526740.63
        expected_outstanding = 4596578.75
        expected_remaining = 20208950.63

        paid_diff = abs(after_stats[2] - expected_paid)
        outstanding_diff = abs(after_stats[3] - expected_outstanding)
        remaining_diff = abs(after_stats[4] - expected_remaining)

        print(f"Expected Paid:       ${expected_paid:,.2f}")
        print(f"Actual Paid:         ${after_stats[2]:,.2f}")
        print(f"Difference:          ${paid_diff:,.2f}")
        print()
        print(f"Expected Outstanding: ${expected_outstanding:,.2f}")
        print(f"Actual Outstanding:   ${after_stats[3]:,.2f}")
        print(f"Difference:           ${outstanding_diff:,.2f}")
        print()
        print(f"Expected Remaining:   ${expected_remaining:,.2f}")
        print(f"Actual Remaining:     ${after_stats[4]:,.2f}")
        print(f"Difference:           ${remaining_diff:,.2f}")
        print()

        # Check if within acceptable tolerance (1% or $100)
        tolerance = 100.00

        if paid_diff <= tolerance and outstanding_diff <= tolerance and remaining_diff <= tolerance:
            print("SUCCESS: All totals are within acceptable tolerance!")
        else:
            print("WARNING: Some totals differ from expected values")
            if paid_diff > tolerance:
                print(f"  - Paid differs by ${paid_diff:,.2f}")
            if outstanding_diff > tolerance:
                print(f"  - Outstanding differs by ${outstanding_diff:,.2f}")
            if remaining_diff > tolerance:
                print(f"  - Remaining differs by ${remaining_diff:,.2f}")

        print()
        print("=" * 80)
        print("UPDATE COMPLETED SUCCESSFULLY")
        print("=" * 80)

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
