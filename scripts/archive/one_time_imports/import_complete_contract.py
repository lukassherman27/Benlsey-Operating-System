#!/usr/bin/env python3
"""
Import complete contract data including fees, payment terms, and metadata
"""

import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def import_tonkin_palace_contract():
    """Import complete Tonkin Palace contract data"""

    conn = get_connection()
    cursor = conn.cursor()

    project_code = "25 BK-002"

    print("\n" + "="*80)
    print(" IMPORTING TONKIN PALACE CONTRACT ".center(80, "="))
    print("="*80)

    # 1. Update project with contract metadata
    print("\n1️⃣  Updating project metadata...")

    cursor.execute("""
        UPDATE projects
        SET
            client_company = ?,
            total_fee_usd = ?,
            contract_duration_months = ?,
            payment_terms_days = ?,
            late_payment_interest_rate = ?,
            stop_work_days_threshold = ?,
            restart_fee_percentage = ?,
            contract_date = ?,
            updated_at = ?
        WHERE project_code = ?
    """, (
        "Apollo Construction Consultant Limited Liability Company",
        1000000,  # Total fee
        24,  # Contract duration
        15,  # Payment terms (days)
        1.5,  # Late payment interest (1.5% per month)
        45,  # Stop work threshold (days)
        10.0,  # Restart fee (10%)
        "2025-01-26",  # Contract date
        datetime.now().isoformat(),
        project_code
    ))

    if cursor.rowcount == 0:
        print(f"⚠️  Project {project_code} not found in database!")
        print("   Creating new project entry...")

        cursor.execute("""
            INSERT INTO projects (
                project_code,
                project_name,
                client_company,
                total_fee_usd,
                contract_duration_months,
                payment_terms_days,
                late_payment_interest_rate,
                stop_work_days_threshold,
                restart_fee_percentage,
                contract_date,
                is_active_project,
                status,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_code,
            "Tonkin Palace Hanoi, Vietnam",
            "Apollo Construction Consultant Limited Liability Company",
            1000000,
            24,
            15,
            1.5,
            45,
            10.0,
            "2025-01-26",
            1,  # Active project
            "active",
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        print(f"✅ Created project {project_code}")
    else:
        print(f"✅ Updated project {project_code}")

    # 2. Clear existing fee breakdowns for this project
    print("\n2️⃣  Clearing existing fee breakdowns...")
    cursor.execute("DELETE FROM project_fee_breakdown WHERE project_code = ?", (project_code,))
    print(f"   Deleted {cursor.rowcount} old entries")

    # 3. Import fee breakdown
    print("\n3️⃣  Importing fee breakdown...")

    fee_breakdown = [
        # LANDSCAPE - $250,000 (25%)
        ("Landscape", "Mobilization", 50000, 20.0),
        ("Landscape", "Conceptual Design", 62500, 25.0),
        ("Landscape", "Design Development", 87500, 35.0),
        ("Landscape", "Construction Documents", 25000, 10.0),
        ("Landscape", "Construction Observation", 25000, 10.0),

        # ARCHITECTURE - $350,000 (35%)
        ("Architecture", "Mobilization", 70000, 20.0),
        ("Architecture", "Conceptual Design", 87500, 25.0),
        ("Architecture", "Design Development", 122500, 35.0),
        ("Architecture", "Construction Documents", 35000, 10.0),
        ("Architecture", "Construction Observation", 35000, 10.0),

        # INTERIOR - $400,000 (40%)
        ("Interior", "Mobilization", 80000, 20.0),
        ("Interior", "Conceptual Design", 100000, 25.0),
        ("Interior", "Design Development", 140000, 35.0),
        ("Interior", "Construction Documents", 40000, 10.0),
        ("Interior", "Construction Observation", 40000, 10.0),
    ]

    inserted = 0
    for discipline, phase, fee, percentage in fee_breakdown:
        breakdown_id = f"{project_code}-{discipline[:3].upper()}-{phase[:3].upper()}-{uuid.uuid4().hex[:8]}"

        cursor.execute("""
            INSERT INTO project_fee_breakdown (
                breakdown_id,
                project_code,
                discipline,
                phase,
                phase_fee_usd,
                percentage_of_total,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            breakdown_id,
            project_code,
            discipline,
            phase,
            fee,
            percentage,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        print(f"   ✓ {discipline:15s} | {phase:25s} | ${fee:>10,} ({percentage:>4.1f}%)")
        inserted += 1

    conn.commit()
    conn.close()

    # 4. Summary
    print("\n" + "="*80)
    print(" IMPORT COMPLETE ".center(80, "="))
    print("="*80)
    print(f"\n✅ Project: {project_code}")
    print(f"✅ Client: Apollo Construction Consultant Limited Liability Company")
    print(f"✅ Total Contract Value: $1,000,000")
    print(f"✅ Contract Duration: 24 months")
    print(f"✅ Fee Breakdown Entries: {inserted}")
    print("\nContract Terms:")
    print(f"  • Payment Due: 15 days after invoice")
    print(f"  • Late Interest: 1.5% per month (after 30 days)")
    print(f"  • Stop Work: After 45 days delinquent")
    print(f"  • Restart Fee: 10% of outstanding amount")
    print("\nDiscipline Breakdown:")
    print(f"  • Landscape: $250,000 (25%)")
    print(f"  • Architecture: $350,000 (35%)")
    print(f"  • Interior: $400,000 (40%)")
    print("="*80 + "\n")


if __name__ == "__main__":
    import_tonkin_palace_contract()
