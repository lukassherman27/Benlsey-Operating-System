#!/usr/bin/env python3
"""
Manual Contract Import Tool
Interactive tool for importing contract data while reviewing PDFs
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


def import_contract(project_code, contract_data):
    """
    Import contract data to database

    contract_data = {
        'client_name': str,
        'total_fee': float,
        'contract_duration': int (months),
        'contract_date': str (YYYY-MM-DD),
        'payment_terms': int (days),
        'late_interest': float (% per month),
        'stop_work_days': int,
        'restart_fee': float (%),
        'fee_breakdown': [
            ('Landscape', 'Mobilization', 50000, 20.0),
            ('Landscape', 'Conceptual Design', 62500, 25.0),
            ...
        ]
    }
    """
    conn = get_connection()
    cursor = conn.cursor()

    print(f"\n💾 Importing {project_code}...")

    # 1. Update project metadata
    cursor.execute("""
        UPDATE projects
        SET
            client_company = COALESCE(?, client_company),
            total_fee_usd = COALESCE(?, total_fee_usd),
            contract_duration_months = COALESCE(?, contract_duration_months),
            payment_terms_days = COALESCE(?, payment_terms_days),
            late_payment_interest_rate = COALESCE(?, late_payment_interest_rate),
            stop_work_days_threshold = COALESCE(?, stop_work_days_threshold),
            restart_fee_percentage = COALESCE(?, restart_fee_percentage),
            contract_date = COALESCE(?, contract_date),
            updated_at = ?
        WHERE project_code = ?
    """, (
        contract_data.get('client_name'),
        contract_data.get('total_fee'),
        contract_data.get('contract_duration'),
        contract_data.get('payment_terms'),
        contract_data.get('late_interest'),
        contract_data.get('stop_work_days'),
        contract_data.get('restart_fee'),
        contract_data.get('contract_date'),
        datetime.now().isoformat(),
        project_code
    ))

    print(f"   ✓ Updated project metadata")

    # 2. Import fee breakdown
    if contract_data.get('fee_breakdown'):
        # Clear existing
        cursor.execute("DELETE FROM project_fee_breakdown WHERE project_code = ?", (project_code,))

        # Insert new
        for discipline, phase, fee, percentage in contract_data['fee_breakdown']:
            breakdown_id = f"{project_code}-{discipline[:3].upper()}-{phase[:3].upper()}-{uuid.uuid4().hex[:8]}"
            cursor.execute("""
                INSERT INTO project_fee_breakdown (
                    breakdown_id, project_code, discipline, phase,
                    phase_fee_usd, percentage_of_total,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                breakdown_id, project_code, discipline, phase,
                fee, percentage,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

        print(f"   ✓ Imported {len(contract_data['fee_breakdown'])} fee breakdown entries")

    conn.commit()
    conn.close()
    print(f"   ✅ Import complete!\n")


def show_example():
    """Show example contract data structure"""
    print("""
================================================================================
                           EXAMPLE CONTRACT DATA
================================================================================

project_code = "25 BK-002"

contract_data = {
    'client_name': "Apollo Construction Consultant Limited Liability Company",
    'total_fee': 1000000,
    'contract_duration': 24,  # months
    'contract_date': "2025-01-26",
    'payment_terms': 15,  # days
    'late_interest': 1.5,  # % per month
    'stop_work_days': 45,
    'restart_fee': 10.0,  # %
    'fee_breakdown': [
        # LANDSCAPE - $250,000
        ('Landscape', 'Mobilization', 50000, 20.0),
        ('Landscape', 'Conceptual Design', 62500, 25.0),
        ('Landscape', 'Design Development', 87500, 35.0),
        ('Landscape', 'Construction Documents', 25000, 10.0),
        ('Landscape', 'Construction Observation', 25000, 10.0),

        # ARCHITECTURE - $350,000
        ('Architecture', 'Mobilization', 70000, 20.0),
        ('Architecture', 'Conceptual Design', 87500, 25.0),
        ('Architecture', 'Design Development', 122500, 35.0),
        ('Architecture', 'Construction Documents', 35000, 10.0),
        ('Architecture', 'Construction Observation', 35000, 10.0),

        # INTERIOR - $400,000
        ('Interior', 'Mobilization', 80000, 20.0),
        ('Interior', 'Conceptual Design', 100000, 25.0),
        ('Interior', 'Design Development', 140000, 35.0),
        ('Interior', 'Construction Documents', 40000, 10.0),
        ('Interior', 'Construction Observation', 40000, 10.0),
    ]
}

import_contract(project_code, contract_data)

================================================================================
    """)


if __name__ == "__main__":
    print("\n" + "="*80)
    print(" MANUAL CONTRACT IMPORT TOOL ".center(80, "="))
    print("="*80)
    print("\nThis tool imports contract data into the database.")
    print("Use show_example() to see the expected data format.")
    print("\nTo import a contract, call:")
    print("  import_contract(project_code, contract_data)")
    print("\n" + "="*80 + "\n")

    show_example()
