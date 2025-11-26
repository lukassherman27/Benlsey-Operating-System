#!/usr/bin/env python3
"""
Contract Data Import Tool
Imports contract terms and fee breakdowns for Bensley projects
Based on standard contract template analysis
Version 2.0 - With validation, payment milestones, and document registration
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_contract_data(contract_data: Dict) -> Dict:
    """
    Validate contract data before import
    Returns: {"valid": True/False, "errors": [...]}
    """
    errors = []

    # Required fields check
    required_fields = ['contract_signed_date', 'total_fee_usd', 'contract_start_date']
    for field in required_fields:
        if not contract_data.get(field):
            errors.append(f"Missing required field: {field}")

    # Fee validation
    total_fee = contract_data.get('total_fee_usd', 0)
    if total_fee <= 0:
        errors.append(f"Invalid total_fee_usd: {total_fee} (must be > 0)")

    # Date logic validation
    try:
        start_date = datetime.strptime(contract_data.get('contract_start_date', ''), '%Y-%m-%d')
        end_date = datetime.strptime(contract_data.get('contract_end_date', ''), '%Y-%m-%d')
        if end_date <= start_date:
            errors.append(f"contract_end_date must be after contract_start_date")
    except ValueError as e:
        errors.append(f"Invalid date format: {e}")

    # Payment schedule validation (if provided)
    if contract_data.get('payment_schedule'):
        payment_schedule = contract_data['payment_schedule']
        if 'phases' in payment_schedule:
            phase_total = sum(phase.get('amount_usd', 0) for phase in payment_schedule['phases'])
            if abs(phase_total - total_fee) > 0.01:  # 1 cent tolerance
                errors.append(f"Payment schedule phases ({phase_total}) don't match total_fee_usd ({total_fee})")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def contract_exists(project_code: str) -> bool:
    """Check if contract already exists for this project"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM contract_terms WHERE project_code = ?
    """, (project_code,))

    count = cursor.fetchone()[0]
    conn.close()

    return count > 0


def validate_fee_breakdown(project_code: str, total_fee: float, breakdown_percentages: Dict) -> Dict:
    """Validate that fee breakdown percentages sum to 100%"""
    errors = []

    # Check percentages sum to 1.0 (100%)
    total_percentage = sum(breakdown_percentages.values())
    if abs(total_percentage - 1.0) > 0.001:  # 0.1% tolerance
        errors.append(f"Breakdown percentages sum to {total_percentage * 100}%, expected 100%")

    # Check all percentages are positive
    for phase, pct in breakdown_percentages.items():
        if pct < 0:
            errors.append(f"Phase '{phase}' has negative percentage: {pct}")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# ============================================================================
# PAYMENT MILESTONES & DOCUMENTS
# ============================================================================

def create_payment_milestones(contract_id: str, project_code: str, payment_schedule: Dict) -> Dict:
    """
    Create payment milestone records from payment schedule
    Returns: {"success": True/False, "milestone_ids": [...]}
    """
    if not payment_schedule or 'phases' not in payment_schedule:
        return {"success": False, "error": "No payment schedule phases provided"}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    milestone_ids = []

    try:
        for phase_data in payment_schedule['phases']:
            # Calculate due date based on due_on field
            due_date = None
            if phase_data.get('due_on') == 'contract_signing':
                # Get contract signed date
                cursor.execute("SELECT contract_signed_date FROM contract_terms WHERE contract_id = ?", (contract_id,))
                signed_date = cursor.fetchone()
                if signed_date:
                    due_date = signed_date[0]

            cursor.execute("""
                INSERT INTO payment_milestones (
                    contract_id, project_code, phase, amount_usd, percentage,
                    due_date, payment_status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract_id,
                project_code,
                phase_data.get('phase'),
                phase_data.get('amount_usd'),
                phase_data.get('percentage'),
                due_date,
                'pending',
                phase_data.get('notes')
            ))

            milestone_ids.append(cursor.lastrowid)

        conn.commit()
        return {"success": True, "milestone_ids": milestone_ids, "count": len(milestone_ids)}

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}

    finally:
        conn.close()


def register_contract_document(project_code: str, contract_id: str, pdf_path: str, signed_date: str) -> Dict:
    """
    Register contract PDF in documents table
    Returns: {"success": True/False, "document_id": ...}
    """
    if not pdf_path:
        return {"success": False, "error": "No document path provided"}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Generate document_id (integer)
        cursor.execute("SELECT MAX(document_id) FROM documents")
        max_id = cursor.fetchone()[0] or 0
        document_id = max_id + 1

        # Extract filename from path
        import os
        file_name = os.path.basename(pdf_path) if pdf_path else "contract.pdf"

        # Insert into documents table
        cursor.execute("""
            INSERT INTO documents (
                document_id, project_code, document_type, file_path,
                file_name, file_type, document_date, status
            ) VALUES (?, ?, 'contract', ?, ?, 'pdf', ?, 'signed')
        """, (
            document_id,
            project_code,
            pdf_path,
            file_name,
            signed_date
        ))

        conn.commit()
        return {"success": True, "document_id": document_id}

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}

    finally:
        conn.close()


def update_project_fee_rollup(project_code: str, fee_rollup_behavior: str = 'separate') -> Dict:
    """
    Update project's fee_rollup_behavior field
    Values: 'separate' or 'rollup'
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE projects
            SET fee_rollup_behavior = ?,
                updated_at = ?
            WHERE project_code = ?
        """, (fee_rollup_behavior, datetime.now().isoformat(), project_code))

        conn.commit()
        return {"success": True, "fee_rollup_behavior": fee_rollup_behavior}

    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}

    finally:
        conn.close()


# ============================================================================
# CORE IMPORT FUNCTIONS
# ============================================================================

def link_projects(parent_code, child_code, relationship_type, component_type=None):
    """Link child project to parent"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE projects
        SET parent_project_code = ?,
            relationship_type = ?,
            component_type = ?,
            updated_at = ?
        WHERE project_code = ?
    """, (parent_code, relationship_type, component_type,
          datetime.now().isoformat(), child_code))

    conn.commit()
    conn.close()

    return {"success": True, "parent": parent_code, "child": child_code}


def create_contract_terms(project_code, contract_data):
    """Create contract terms record"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Generate contract_id
    cursor.execute("SELECT MAX(CAST(SUBSTR(contract_id, 2) AS INTEGER)) FROM contract_terms WHERE contract_id LIKE 'C%'")
    max_id = cursor.fetchone()[0] or 0
    contract_id = f"C{max_id + 1:04d}"

    # Serialize payment schedule
    payment_schedule_json = None
    if contract_data.get("payment_schedule"):
        payment_schedule_json = json.dumps(contract_data["payment_schedule"])

    cursor.execute("""
        INSERT INTO contract_terms (
            contract_id, project_code, contract_signed_date, contract_start_date,
            total_contract_term_months, contract_end_date, total_fee_usd,
            payment_schedule, contract_type, retainer_amount_usd,
            final_payment_amount_usd, early_termination_terms,
            amendment_count, original_contract_id, contract_document_path,
            confirmed_by_user, confidence, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        contract_id,
        project_code,
        contract_data.get("contract_signed_date"),
        contract_data.get("contract_start_date"),
        contract_data.get("total_contract_term_months"),
        contract_data.get("contract_end_date"),
        contract_data.get("total_fee_usd"),
        payment_schedule_json,
        contract_data.get("contract_type", "fixed_fee"),
        contract_data.get("retainer_amount_usd"),
        contract_data.get("final_payment_amount_usd"),
        contract_data.get("early_termination_terms"),
        contract_data.get("amendment_count", 0),
        contract_data.get("original_contract_id"),
        contract_data.get("contract_document_path"),
        contract_data.get("confirmed_by_user", 0),
        contract_data.get("confidence"),
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return {"success": True, "contract_id": contract_id}


def create_fee_breakdown(project_code, total_fee, breakdown_percentages=None):
    """Create fee breakdown records"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not breakdown_percentages:
        breakdown_percentages = {
            'mobilization': 0.15,
            'concept': 0.25,
            'dd': 0.30,
            'cd': 0.15,
            'ca': 0.15
        }

    created_ids = []

    for phase, percentage in breakdown_percentages.items():
        cursor.execute("SELECT MAX(CAST(SUBSTR(breakdown_id, 2) AS INTEGER)) FROM project_fee_breakdown WHERE breakdown_id LIKE 'B%'")
        max_id = cursor.fetchone()[0] or 0
        breakdown_id = f"B{max_id + 1:05d}"

        phase_fee = total_fee * percentage

        cursor.execute("""
            INSERT INTO project_fee_breakdown (
                breakdown_id, project_code, phase, phase_fee_usd,
                percentage_of_total, payment_status, confirmed_by_user,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'pending', 0, ?, ?)
        """, (
            breakdown_id,
            project_code,
            phase,
            phase_fee,
            percentage,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        created_ids.append(breakdown_id)

    conn.commit()
    conn.close()

    return {"success": True, "breakdown_ids": created_ids}


def import_beach_club_contract():
    """
    Import 25 BK-030 Beach Club at Mandarin Oriental Bali
    Signed June 3, 2025 - Total Fee $550,000
    Additional services for parent project 23 BK-029
    Version 2.0 - With validation, milestones, and document registration
    """
    print("=" * 80)
    print("IMPORTING CONTRACT: 25 BK-030 - Beach Club at Mandarin Oriental Bali (v2.0)")
    print("=" * 80)

    project_code = "25 BK-030"

    # Step 0: Check for duplicate (re-run safety)
    print("\nStep 0: Checking for duplicates...")
    if contract_exists(project_code):
        print(f"  ⚠️  Contract already exists for {project_code}")
        print(f"  Skipping import (re-run safe)")
        return {"success": False, "error": "Contract already exists"}

    # Step 1: Link to parent project (23 BK-029 Mandarin Oriental Bali)
    print("\nStep 1: Linking to parent project...")
    result = link_projects(
        parent_code="23 BK-029",
        child_code=project_code,
        relationship_type="additional_services",
        component_type="beach_club"
    )
    print(f"  ✅ Result: {result}")

    # Set fee rollup behavior (additional_services = separate)
    print("\nStep 1b: Setting fee rollup behavior...")
    result = update_project_fee_rollup(project_code, fee_rollup_behavior='separate')
    print(f"  ✅ Fee rollup: {result}")

    # Step 2: Create contract terms
    print("\nStep 2: Creating contract terms...")

    # Payment schedule (standard Bensley 5-phase)
    payment_schedule = {
        "phases": [
            {
                "phase": "mobilization",
                "percentage": 0.15,
                "amount_usd": 82500,
                "due_on": "contract_signing",
                "refundable": False,
                "notes": "Non-refundable, due on signing"
            },
            {
                "phase": "concept",
                "percentage": 0.25,
                "amount_usd": 137500,
                "due_on": "phase_completion",
                "refundable": True,
                "notes": "Conceptual Design phase"
            },
            {
                "phase": "dd",
                "percentage": 0.30,
                "amount_usd": 165000,
                "due_on": "phase_completion",
                "refundable": True,
                "notes": "Design Development phase"
            },
            {
                "phase": "cd",
                "percentage": 0.15,
                "amount_usd": 82500,
                "due_on": "phase_completion",
                "refundable": True,
                "notes": "Construction Documents phase"
            },
            {
                "phase": "ca",
                "percentage": 0.15,
                "amount_usd": 82500,
                "due_on": "phase_completion",
                "refundable": True,
                "notes": "Construction Observation phase"
            }
        ],
        "payment_terms": {
            "days_to_pay": 15,
            "late_interest_rate": 0.015,  # 1.5% per month
            "currency": "USD",
            "payment_method": "telegraphic_transfer"
        }
    }

    contract_signed = datetime(2025, 6, 3)
    contract_end = contract_signed + timedelta(days=24*30)  # 24 months

    contract_data = {
        "contract_signed_date": contract_signed.strftime("%Y-%m-%d"),
        "contract_start_date": contract_signed.strftime("%Y-%m-%d"),
        "total_contract_term_months": 24,
        "contract_end_date": contract_end.strftime("%Y-%m-%d"),
        "total_fee_usd": 550000,
        "payment_schedule": payment_schedule,
        "contract_type": "fixed_fee",
        "retainer_amount_usd": None,
        "final_payment_amount_usd": 82500,
        "early_termination_terms": "20% demobilization fee of uncommenced work",
        "amendment_count": 0,
        "original_contract_id": None,
        "contract_document_path": "/BDS_KnowledgeBase/attachments/Beach_Club/25-030_Beach_Club_signed.pdf",
        "confirmed_by_user": 1,
        "confidence": 1.0
    }

    # Validate contract data before import
    print("\nStep 2a: Validating contract data...")
    validation = validate_contract_data(contract_data)
    if not validation['valid']:
        print(f"  ❌ Validation failed:")
        for error in validation['errors']:
            print(f"     - {error}")
        return {"success": False, "errors": validation['errors']}
    print(f"  ✅ Validation passed")

    # Create contract terms
    result = create_contract_terms(project_code, contract_data)
    contract_id = result.get('contract_id')
    print(f"  ✅ Contract ID: {contract_id}")
    print(f"  Status: {result}")

    # Step 3: Create fee breakdown
    print("\nStep 3: Creating fee breakdown...")
    result = create_fee_breakdown(
        project_code="25 BK-030",
        total_fee=550000,
        breakdown_percentages={
            'mobilization': 0.15,
            'concept': 0.25,
            'dd': 0.30,
            'cd': 0.15,
            'ca': 0.15
        }
    )
    print(f"  ✅ Created {len(result.get('breakdown_ids', []))} fee breakdown records")
    print(f"  Status: {result}")

    # Step 4: Create payment milestones
    print("\nStep 4: Creating payment milestones...")
    result = create_payment_milestones(
        contract_id=contract_id,
        project_code=project_code,
        payment_schedule=payment_schedule
    )
    if result.get('success'):
        print(f"  ✅ Created {result.get('count')} payment milestones")
        print(f"  Milestone IDs: {result.get('milestone_ids')}")
    else:
        print(f"  ⚠️  Failed to create milestones: {result.get('error')}")

    # Step 5: Register contract document
    print("\nStep 5: Registering contract PDF...")
    result = register_contract_document(
        project_code=project_code,
        contract_id=contract_id,
        pdf_path=contract_data['contract_document_path'],
        signed_date=contract_data['contract_signed_date']
    )
    if result.get('success'):
        print(f"  ✅ Document registered: {result.get('document_id')}")
    else:
        print(f"  ⚠️  Failed to register document: {result.get('error')}")

    # Step 6: Verify all data was created
    print("\nStep 6: Verifying complete import...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check project linkage
    cursor.execute("""
        SELECT project_code, parent_project_code, relationship_type, component_type
        FROM projects WHERE project_code = '25 BK-030'
    """)
    project_data = cursor.fetchone()
    if project_data:
        print(f"  ✅ Project linked: {project_data[0]} → Parent: {project_data[1]} ({project_data[2]})")

    # Check contract terms
    cursor.execute("SELECT contract_id, total_fee_usd FROM contract_terms WHERE project_code = '25 BK-030'")
    contract = cursor.fetchone()
    if contract:
        print(f"  ✅ Contract created: {contract[0]} - ${contract[1]:,.2f}")

    # Check fee breakdown
    cursor.execute("SELECT COUNT(*), SUM(phase_fee_usd) FROM project_fee_breakdown WHERE project_code = '25 BK-030'")
    breakdown = cursor.fetchone()
    if breakdown:
        print(f"  ✅ Fee breakdown: {breakdown[0]} phases totaling ${breakdown[1]:,.2f}")

    # Check payment milestones
    cursor.execute("SELECT COUNT(*), SUM(amount_usd) FROM payment_milestones WHERE project_code = '25 BK-030'")
    milestones = cursor.fetchone()
    if milestones:
        print(f"  ✅ Payment milestones: {milestones[0]} milestones totaling ${milestones[1]:,.2f}")

    # Check document registration
    cursor.execute("SELECT document_id, document_type FROM documents WHERE project_code = '25 BK-030' AND document_type = 'contract'")
    doc = cursor.fetchone()
    if doc:
        print(f"  ✅ Contract document: {doc[0]} (type: {doc[1]})")

    conn.close()

    print("\n" + "=" * 80)
    print("CONTRACT IMPORT COMPLETE ✅")
    print("=" * 80)


def batch_import_contracts(contracts_list):
    """
    Batch import multiple contracts

    Args:
        contracts_list: List of contract dictionaries with:
            - project_code
            - contract_signed_date
            - total_fee_usd
            - contract_term_months
            - parent_project_code (optional)
            - relationship_type (optional)
            - component_type (optional)
    """
    service = ContractService(DB_PATH)

    print("=" * 80)
    print(f"BATCH IMPORTING {len(contracts_list)} CONTRACTS")
    print("=" * 80)

    for i, contract in enumerate(contracts_list, 1):
        print(f"\n[{i}/{len(contracts_list)}] Processing: {contract['project_code']}")

        # Link to parent if specified
        if contract.get('parent_project_code'):
            result = service.link_projects(
                parent_code=contract['parent_project_code'],
                child_code=contract['project_code'],
                relationship_type=contract.get('relationship_type', 'additional_services'),
                component_type=contract.get('component_type')
            )
            print(f"  Linked to parent: {contract['parent_project_code']}")

        # Create contract terms
        contract_signed = datetime.strptime(contract['contract_signed_date'], "%Y-%m-%d")
        term_months = contract.get('contract_term_months', 24)
        contract_end = contract_signed + timedelta(days=term_months*30)

        payment_schedule = {
            "phases": [
                {"phase": "mobilization", "percentage": 0.15, "amount_usd": contract['total_fee_usd'] * 0.15},
                {"phase": "concept", "percentage": 0.25, "amount_usd": contract['total_fee_usd'] * 0.25},
                {"phase": "dd", "percentage": 0.30, "amount_usd": contract['total_fee_usd'] * 0.30},
                {"phase": "cd", "percentage": 0.15, "amount_usd": contract['total_fee_usd'] * 0.15},
                {"phase": "ca", "percentage": 0.15, "amount_usd": contract['total_fee_usd'] * 0.15}
            ]
        }

        contract_data = {
            "contract_signed_date": contract['contract_signed_date'],
            "contract_start_date": contract['contract_signed_date'],
            "total_contract_term_months": term_months,
            "contract_end_date": contract_end.strftime("%Y-%m-%d"),
            "total_fee_usd": contract['total_fee_usd'],
            "payment_schedule": payment_schedule,
            "contract_type": "fixed_fee",
            "confirmed_by_user": contract.get('confirmed_by_user', 0),
            "confidence": contract.get('confidence', 0.8)
        }

        result = service.create_contract_terms(contract['project_code'], contract_data)
        print(f"  Contract terms created: {result.get('contract_id')}")

        # Create fee breakdown
        result = service.create_standard_fee_breakdown(
            project_code=contract['project_code'],
            total_fee=contract['total_fee_usd']
        )
        print(f"  Fee breakdown created: {len(result.get('breakdown_ids', []))} phases")

    print("\n" + "=" * 80)
    print(f"BATCH IMPORT COMPLETE - {len(contracts_list)} CONTRACTS ✅")
    print("=" * 80)


def example_batch_import():
    """Example batch import for top active projects"""
    contracts = [
        {
            "project_code": "25 BK-030",
            "contract_signed_date": "2025-06-03",
            "total_fee_usd": 550000,
            "contract_term_months": 24,
            "parent_project_code": "23 BK-029",
            "relationship_type": "additional_services",
            "component_type": "beach_club",
            "confirmed_by_user": 1,
            "confidence": 1.0
        },
        # Add more contracts here as they're confirmed...
    ]

    batch_import_contracts(contracts)


if __name__ == "__main__":
    # Import the Beach Club contract as example
    import_beach_club_contract()

    # To batch import multiple contracts:
    # example_batch_import()
