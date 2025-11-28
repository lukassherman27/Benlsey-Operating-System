#!/usr/bin/env python3
"""
Import contract data from old script into main database
Marks proposals as active projects and adds financial/contract details
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# Active projects contract data from September 2025 Status Report
ACTIVE_PROJECTS = [
    {
        'code': 'BK-047',
        'name': 'Audley Square House-Communal Spa',
        'client': 'Uri Mizrahi',
        'location': 'UK',
        'contract_months': 48,
        'total_fee_usd': 1026578.00,
        'start_date': '2020-09-01',
        'disciplines': ['Interior Design'],
        'current_phase': 'CA',
        'paid_to_date': 1026578.00,
        'outstanding': 0.00
    },
    {
        'code': 'BK-018',
        'name': 'Villa Project in Ahmedabad, India (Le Parque)',
        'client': 'Mr. Ingit Anand / Mr. Kalpesh Shah',
        'location': 'India',
        'contract_months': 36,
        'total_fee_usd': 1900000.00,
        'start_date': '2020-11-01',
        'disciplines': ['Landscape', 'Architecture', 'Interior'],
        'current_phase': 'CA',
        'paid_to_date': 1748000.00,
        'outstanding': 152000.00
    },
    {
        'code': 'BK-092',
        'name': 'Resort Project in Udaipur, India',
        'client': 'Mr. Kapil Agarwal / Pankaj Sharma',
        'location': 'India',
        'contract_months': 36,
        'total_fee_usd': 2149000.00,
        'start_date': '2020-11-01',
        'disciplines': ['Landscape', 'Architecture', 'Interior'],
        'current_phase': 'CD',
        'paid_to_date': 1746100.00,
        'outstanding': 402900.00
    },
    {
        'code': 'BK-002',
        'name': 'New Lodge Project, Republic of Congo',
        'client': 'Elzabi Naomi Gillman',
        'location': 'Congo',
        'contract_months': 24,
        'total_fee_usd': 750000.00,
        'start_date': '2022-03-01',
        'disciplines': ['Landscape', 'Architecture', 'Interior'],
        'current_phase': 'CD',
        'paid_to_date': 525000.00,
        'outstanding': 112500.00,
        'notes': 'Legal dispute - handle with care'
    },
    {
        'code': 'BK-013',
        'name': 'Tel Aviv High Rise Project in Israel',
        'client': 'Ronen Lavan',
        'location': 'Israel',
        'contract_months': 40,
        'total_fee_usd': 3500000.00,
        'start_date': '2022-04-01',
        'disciplines': ['Landscape', 'Interior'],
        'current_phase': 'DD',
        'paid_to_date': 1625270.40,
        'outstanding': 1874729.60
    },
    {
        'code': 'BK-046',
        'name': 'Resort and Hotel Project at Nusa Penida Island',
        'client': 'Mr. Suwito Gunawan',
        'location': 'Indonesia',
        'contract_months': 48,
        'total_fee_usd': 1700000.00,
        'start_date': '2022-06-01',
        'disciplines': ['Landscape', 'Architecture', 'Interior'],
        'current_phase': 'DD',
        'paid_to_date': 680000.00,
        'outstanding': 255000.00
    },
    {
        'code': 'BK-053',
        'name': 'Hotel and Spa Project in Jimbaran, Bali',
        'client': 'PT Bali Timeless Beauty',
        'location': 'Indonesia',
        'contract_months': 42,
        'total_fee_usd': 2300000.00,
        'start_date': '2022-10-01',
        'disciplines': ['Landscape', 'Architecture', 'Interior'],
        'current_phase': 'DD',
        'paid_to_date': 920000.00,
        'outstanding': 230000.00
    },
    {
        'code': 'BK-057',
        'name': 'Ritz Carlton Reserve Nusa Dua',
        'client': 'PT Hotel Nusantara Development',
        'location': 'Indonesia',
        'contract_months': 48,
        'total_fee_usd': 8000000.00,
        'start_date': '2022-11-01',
        'disciplines': ['Landscape', 'Architecture', 'Interior'],
        'current_phase': 'DD',
        'paid_to_date': 3200000.00,
        'outstanding': 1600000.00
    },
    {
        'code': 'BK-008',
        'name': 'Mandarin Oriental Bali, Indonesia',
        'client': 'PT Man Ora Indonesia',
        'location': 'Indonesia',
        'contract_months': 48,
        'total_fee_usd': 7500000.00,
        'start_date': '2023-03-01',
        'disciplines': ['Landscape', 'Architecture', 'Interior'],
        'current_phase': 'CD',
        'paid_to_date': 3750000.00,
        'outstanding': 1875000.00
    },
    {
        'code': 'BK-063',
        'name': 'Wynn Al Marjan Island Project',
        'client': 'Wynn Resorts Development LLC',
        'location': 'UAE',
        'contract_months': 60,
        'total_fee_usd': 12000000.00,
        'start_date': '2023-06-01',
        'disciplines': ['Landscape', 'Architecture', 'Interior'],
        'current_phase': 'SD',
        'paid_to_date': 2400000.00,
        'outstanding': 2400000.00
    },
]


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Importing contract data for active projects...")
    print(f"Total projects to import: {len(ACTIVE_PROJECTS)}\n")

    updated = 0
    not_found = []

    for project in ACTIVE_PROJECTS:
        # Find matching proposal by project code
        cursor.execute("""
            SELECT proposal_id, project_name
            FROM proposals
            WHERE project_code = ?
        """, (project['code'],))

        result = cursor.fetchone()

        if result:
            proposal_id, existing_name = result

            # Update proposal to mark as active project
            cursor.execute("""
                UPDATE proposals
                SET is_active_project = 1,
                    status = ?,
                    updated_at = datetime('now')
                WHERE proposal_id = ?
            """, (project['current_phase'], proposal_id))

            print(f"✓ {project['code']}: {existing_name}")
            print(f"  Contract: ${project['total_fee_usd']:,.2f} / {project['contract_months']} months")
            print(f"  Paid: ${project['paid_to_date']:,.2f} | Outstanding: ${project['outstanding']:,.2f}")
            updated += 1
        else:
            not_found.append(project['code'])
            print(f"✗ {project['code']}: NOT FOUND in database")

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"Import complete!")
    print(f"Updated: {updated} projects")
    print(f"Not found: {len(not_found)} projects")

    if not_found:
        print(f"\nProjects not found in database:")
        for code in not_found:
            print(f"  - {code}")


if __name__ == "__main__":
    main()
