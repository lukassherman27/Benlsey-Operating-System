#!/usr/bin/env python3
"""
Import Missing Projects: 25 BK-039 and 25 BK-040
Extracted from "Project Status as of 10 Nov 25 (Updated).pdf"
"""

import sqlite3
from datetime import datetime

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"

# Missing projects data extracted from PDF
MISSING_PROJECTS = {
    '25 BK-039': {
        'name': 'Wynn Al Marjan Island Project - Additional Service',
        'total_fee': 250000.00,
        'outstanding': 0.00,
        'remaining': 250000.00,
        'paid_to_date': 0.00,
        'expiry': None,  # No expiry date specified in PDF
        'status': 'Design',  # Additional Service Design Fee
        'client': 'Wynn Al Marjan',
    },
    '25 BK-040': {
        'name': 'The Ritz Carlton Reserve, Nusa Dua, Bali - Branding Consultancy Service',
        'total_fee': 125000.00,
        'outstanding': 0.00,
        'remaining': 93750.00,
        'paid_to_date': 31250.00,
        'expiry': None,  # No expiry date specified in PDF
        'status': 'Branding',  # Branding Consultancy Service
        'client': 'Ritz Carlton',
    },
}

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 80)
    print("IMPORTING MISSING PROJECTS: 25 BK-039 and 25 BK-040")
    print("Source: Project Status as of 10 Nov 25 (Updated).pdf")
    print("=" * 80)
    print()

    updated = 0
    inserted = 0

    for project_code, data in MISSING_PROJECTS.items():
        # Check if project exists
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
            # Insert new project
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

            inserted += 1

    conn.commit()
    conn.close()

    print("=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Updated: {updated} projects")
    print(f"Inserted: {inserted} projects")
    print()
    print("✅ Import complete!")

if __name__ == "__main__":
    main()
