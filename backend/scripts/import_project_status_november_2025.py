#!/usr/bin/env python3
"""
Import Project Status data from November 2025 accountant report
Updates all active projects with comprehensive financial information
"""

import sqlite3
from datetime import datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# Comprehensive project data from "Project Status as of 10 Nov 25 (Updated).pdf"
# Format: project_code -> {financial data}
ACTIVE_PROJECTS = {
    '20 BK-047': {
        'name': 'Audley Square House-Communal Spa',
        'total_fee': 1026578.00,  # From previous import
        'outstanding': 8000.00,
        'remaining': 108000.00,
        'paid_to_date': 24000.00,
        'expiry': '2026-09-30',
        'status': 'CA',  # Construction Administration
        'client': 'Uri Mizrahi',
    },
    '19 BK-018': {
        'name': 'Villa Project in Ahmedabad, India',
        'total_fee': 1900000.00,
        'outstanding': 152000.00,  # 35625 + 49875 + 66500
        'remaining': 0.00,
        'paid_to_date': 1748000.00,  # 439375 + 615125 + 693500
        'expiry': '2023-11-30',  # Original 36 month
        'status': 'CO',  # Construction Observation
        'client': 'Ingit Anand / Kalpesh Shah',
    },
    '22 BK-013': {
        'name': 'Tel Aviv High Rise Project in Israel',
        'total_fee': 3500000.00,
        'outstanding': 231000.00,
        'remaining': 1827000.00,  # 240000 + 1365000 + 462000 (remaining monthly)
        'paid_to_date': 1622000.00,  # 160000 + 1235000 + 462000 (paid monthly)
        'expiry': '2025-08-31',  # 40 month
        'status': 'DD',  # Design Development + Monthly Fee
        'client': 'Ronen Lavan',
    },
    '22 BK-046': {
        'name': 'Resort and Hotel Project at Nusa Penida Island, Indonesia',
        'total_fee': 1700000.00,
        'outstanding': 255000.00,  # 67500 + 90000 + 97500
        'remaining': 765000.00,  # 202500 + 270000 + 292500
        'paid_to_date': 680000.00,  # 180000 + 240000 + 260000
        'expiry': '2026-06-30',  # 48 month
        'status': 'DD',
        'client': 'Suwito Gunawan',
    },
    '22 BK-095': {
        'name': 'Wynn Al Marjan Island Project',
        'total_fee': 3325000.00,  # Multiple restaurants
        'outstanding': 203478.75,  # 31172.50 + 77306.25 + 47250 + combined
        'remaining': 678148.75,
        'paid_to_date': 3097372.50,
        'expiry': '2026-12-31',  # Latest expiry from multiple parts
        'status': 'CO',
        'client': 'Wynn Al Marjan',
    },
    '23 BK-009': {
        'name': 'Villa Project in Ahmedabad, India (Le Parqe Sector 5 and 7)',
        'total_fee': 730000.00,
        'outstanding': 219000.00,
        'remaining': 0.00,
        'paid_to_date': 511000.00,
        'expiry': '2024-09-30',  # 18 month
        'status': 'CD',  # Construction Documents
        'client': 'Le Parqe',
    },
    '23 BK-028': {
        'name': 'Proscenium Penthouse in Manila, Philippines',
        'total_fee': 1797520.00,  # 1400000 + 397520 mural
        'outstanding': 0.00,
        'remaining': 168000.00,
        'paid_to_date': 1629520.00,
        'expiry': '2024-11-30',  # 18 month
        'status': 'CO',
        'client': 'Proscenium',
    },
    '23 BK-088': {
        'name': 'Mandarin Oriental Bali Hotel and Branded Residential, Indonesia',
        'total_fee': 575000.00,
        'outstanding': 43125.00,
        'remaining': 129375.00,
        'paid_to_date': 402500.00,
        'expiry': '2025-09-30',  # 30 month
        'status': 'CD',
        'client': 'Mandarin Oriental',
    },
    '25 BK-030': {
        'name': 'Beach Club at Mandarin Oriental Bali',
        'total_fee': 550000.00,
        'outstanding': 137500.00,  # 55000 + 82500
        'remaining': 330000.00,  # 132000 + 198000
        'paid_to_date': 82500.00,  # 33000 + 49500
        'expiry': '2027-06-30',  # 24 month
        'status': 'CD',
        'client': 'Mandarin Oriental',
    },
    '25 BK-018': {
        'name': 'The Ritz Carlton Hotel Nanyan Bay, China',
        'total_fee': 225000.00,
        'outstanding': 56250.00,
        'remaining': 56250.00,
        'paid_to_date': 112500.00,
        'expiry': '2026-03-31',  # 12 month extension
        'status': 'Extension',
        'client': 'Ritz Carlton',
    },
    '23 BK-071': {
        'name': 'St. Regis Hotel in Thousand Island Lake, China',
        'total_fee': 1350000.00,
        'outstanding': 101250.00,
        'remaining': 708750.00,
        'paid_to_date': 540000.00,
        'expiry': '2026-02-28',  # 30 month
        'status': 'DD',
        'client': 'St. Regis',
    },
    '23 BK-096': {
        'name': 'St. Regis Hotel in Thousand Island Lake, China (Addendum)',
        'total_fee': 500000.00,
        'outstanding': 75000.00,
        'remaining': 112500.00,
        'paid_to_date': 312500.00,
        'expiry': '2026-02-28',
        'status': 'CD',
        'client': 'St. Regis',
    },
    '23 BK-067': {
        'name': 'Treasure Island Resort, Intercontinental Hotel, Anji, Zhejiang, China',
        'total_fee': 1200000.00,
        'outstanding': 0.00,
        'remaining': 648000.00,
        'paid_to_date': 552000.00,
        'expiry': '2025-11-30',
        'status': 'DD',
        'client': 'Intercontinental',
    },
    '23 BK-080': {
        'name': 'Treasure Island Resort, Intercontinental Hotel, Anji (Landscape)',
        'total_fee': 400000.00,
        'outstanding': 0.00,
        'remaining': 216000.00,
        'paid_to_date': 184000.00,
        'expiry': '2025-11-30',
        'status': 'DD',
        'client': 'Intercontinental',
    },
    '23 BK-093': {
        'name': '25 Downtown Mumbai, India (Art Deco Residential Project)',
        'total_fee': 3250000.00,  # 1000000 + 1500000 + 750000
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
        'total_fee': 4650000.00,  # 4370000 + 280000 additional
        'outstanding': 0.00,
        'remaining': 2561359.38,
        'paid_to_date': 2088640.63,
        'expiry': '2027-05-31',  # 36 month
        'status': 'SD',  # Schematic Design
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
        'name': 'Luang Prabang Heritage Arcade and Hotel, Laos- The Shinta Mani',
        'total_fee': 1450000.00,
        'outstanding': 0.00,
        'remaining': 870000.00,
        'paid_to_date': 580000.00,
        'expiry': '2026-03-31',
        'status': 'CD',
        'client': 'Shinta Mani',
    },
    '24 BK-029': {
        'name': 'Qinhu Resort Project, China',
        'total_fee': 3250000.00,
        'outstanding': 650000.00,
        'remaining': 2356250.00,
        'paid_to_date': 243750.00,
        'expiry': '2026-09-30',
        'status': 'CD',
        'client': 'Qinhu',
    },
    '19 BK-052': {
        'name': 'The Siam Hotel Chiangmai',
        'total_fee': 814500.00,  # THB 28,500,000
        'outstanding': 0.00,
        'remaining': 445800.00,
        'paid_to_date': 368700.00,
        'expiry': '2026-12-31',
        'status': 'DD',
        'client': 'The Siam',
    },
    '24 BK-033': {
        'name': 'Renovation Work for Three of Four Seasons Properties',
        'total_fee': 1500000.00,  # THB 48,000,000
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
        'name': 'Luxury Resort Development at Fenfushi Island, Raa Atoll, Maldives',
        'total_fee': 2990000.00,
        'outstanding': 526000.00,
        'remaining': 448500.00,
        'paid_to_date': 2015500.00,
        'expiry': '2026-11-30',
        'status': 'CD',
        'client': 'Bharath / Chen Huifang',
    },
    '24 BK-074': {
        'name': '43 Dang Thai Mai Project, Hanoi, Vietnam',
        'total_fee': 4900000.00,
        'outstanding': 1001725.00,
        'remaining': 808500.00,
        'paid_to_date': 3089775.00,
        'expiry': '2024-12-31',
        'status': 'CD',
        'client': 'Vietnam',
    },
    '25 BK-015': {
        'name': 'Shinta Mani Mustang, Nepal',
        'total_fee': 300000.00,  # Two hotels
        'outstanding': 120000.00,
        'remaining': 135000.00,
        'paid_to_date': 45000.00,
        'expiry': '2027-05-31',
        'status': 'DD',
        'client': 'Shinta Mani',
    },
    '25 BK-017': {
        'name': "TARC's Luxury Branded Residence Project in New Delhi",
        'total_fee': 3000000.00,
        'outstanding': 131250.00,
        'remaining': 2418750.00,
        'paid_to_date': 450000.00,
        'expiry': '2029-02-28',  # 42 month
        'status': 'CD',
        'client': 'TARC',
    },
    '25 BK-033': {
        'name': 'The Ritz Carlton Reserve, Nusa Dua, Bali, Indonesia',
        'total_fee': 3275000.00,  # 3150000 + 125000 branding
        'outstanding': 393750.00,
        'remaining': 1890000.00,
        'paid_to_date': 1023750.00,
        'expiry': '2027-07-31',
        'status': 'CD',
        'client': 'Ritz Carlton',
    },
}

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("IMPORTING PROJECT STATUS REPORT - NOVEMBER 2025")
    print("Source: accountant@bensley.com (Thippawan Thaviphoke)")
    print("=" * 80)
    print()

    updated = 0
    not_found = []

    for project_code, data in ACTIVE_PROJECTS.items():
        # Check if project exists with EXACT year prefix match
        cursor.execute("""
            SELECT proposal_id, project_code, project_name
            FROM proposals
            WHERE project_code = ?
        """, (project_code,))

        result = cursor.fetchone()

        if result:
            # Update existing project
            proposal_id, db_project_code, existing_name = result

            cursor.execute("""
                UPDATE proposals
                SET
                    is_active_project = 1,
                    status = ?,
                    total_fee_usd = ?,
                    paid_to_date_usd = ?,
                    outstanding_usd = ?,
                    remaining_work_usd = ?,
                    contract_expiry_date = ?,
                    primary_contact = ?,
                    updated_at = datetime('now')
                WHERE proposal_id = ?
            """, (
                data['status'],
                data['total_fee'],
                data['paid_to_date'],
                data['outstanding'],
                data['remaining'],
                data['expiry'],
                data.get('client'),
                proposal_id
            ))

            print(f"✓ UPDATED {project_code}: {existing_name}")
            print(f"  Total Fee: ${data['total_fee']:,.2f}")
            print(f"  Paid: ${data['paid_to_date']:,.2f}")
            print(f"  Outstanding: ${data['outstanding']:,.2f}")
            print(f"  Remaining: ${data['remaining']:,.2f}")
            print(f"  Status: {data['status']}")
            print()

            updated += 1
        else:
            # Insert new project - doesn't exist with this year prefix
            cursor.execute("""
                INSERT INTO proposals (
                    project_code, project_name, is_active_project,
                    status, total_fee_usd, paid_to_date_usd,
                    outstanding_usd, remaining_work_usd,
                    contract_expiry_date, primary_contact,
                    created_at, updated_at
                ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                project_code,
                data['name'],
                data['status'],
                data['total_fee'],
                data['paid_to_date'],
                data['outstanding'],
                data['remaining'],
                data['expiry'],
                data.get('client')
            ))

            print(f"✓ INSERTED {project_code}: {data['name']}")
            print(f"  Total Fee: ${data['total_fee']:,.2f}")
            print(f"  Paid: ${data['paid_to_date']:,.2f}")
            print(f"  Outstanding: ${data['outstanding']:,.2f}")
            print(f"  Remaining: ${data['remaining']:,.2f}")
            print(f"  Status: {data['status']}")
            print()

            updated += 1

    conn.commit()
    conn.close()

    print("=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Updated: {updated} projects")

    if not_found:
        print(f"\nNot found: {len(not_found)} projects")
        for code in not_found:
            print(f"  - {code}: {ACTIVE_PROJECTS[code]['name']}")

    print()
    print("✅ Import complete!")

if __name__ == "__main__":
    main()
