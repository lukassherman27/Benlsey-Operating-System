#!/usr/bin/env python3
"""
Import 25 BK-017 TARC's Luxury Branded Residence Project in New Delhi
August 21, 2025 - Full Landscape & Interior Design Contract
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-017
project_code = "25 BK-017"

contract_data = {
    'client_name': "TARC GREEN RETREAT LIMITED",
    'total_fee': 3000000,  # USD 3,000,000
    'contract_duration': 36,  # 36 months (can extend to 42 for Construction Observation)
    'contract_date': "2025-08-21",
    'payment_terms': 30,  # 30 days
    'late_interest': 1.5,  # 1.5% per month after 60 days
    'stop_work_days': None,  # Not specified in contract
    'restart_fee': 10.0,  # 10% start-up fee if suspended (Section 7.5)

    # Fee breakdown by discipline and phase
    'fee_breakdown': [
        # INTERIOR DESIGN - $1,950,000
        ('Interior', 'Mobilization Fee/Masterplanning', 292500, 9.75),
        ('Interior', 'Conceptual Design', 487500, 16.25),
        ('Interior', 'Design Development', 585000, 19.5),
        ('Interior', 'Construction Documents', 292500, 9.75),
        ('Interior', 'Construction Observation', 292500, 9.75),

        # LANDSCAPE ARCHITECTURAL - $1,050,000
        ('Landscape', 'Mobilization Fee/Masterplanning', 157500, 5.25),
        ('Landscape', 'Conceptual Design', 262500, 8.75),
        ('Landscape', 'Design Development', 315000, 10.5),
        ('Landscape', 'Construction Documents', 157500, 5.25),
        ('Landscape', 'Construction Observation', 157500, 5.25),
    ]
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-017 - TARC DELHI LUXURY RESIDENCES ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: {contract_data['client_name']}")
print(f"   Total Fee: ${contract_data['total_fee']:,}")
print(f"   Duration: 36 months (up to 42 with Construction Observation)")
print(f"   Contract Date: {contract_data['contract_date']}")
print("\n🏗️ Project Scope:")
print("   Type: Luxury Branded Residences (TARC Green Retreat)")
print("   Location: Adjacent to The Roseate, NH-8, New Delhi")
print("   Size: 7 acres, 80-120 residential units")
print("   Scope: Full landscape + interior design + branding")
print("\n💰 Fee Breakdown:")
print(f"   Interior Design: ${1950000:,}")
print(f"     - Mobilization/Masterplanning: ${292500:,}")
print(f"     - Conceptual Design: ${487500:,}")
print(f"     - Design Development: ${585000:,}")
print(f"     - Construction Documents: ${292500:,}")
print(f"     - Construction Observation: ${292500:,}")
print(f"   Landscape Architectural: ${1050000:,}")
print(f"     - Mobilization/Masterplanning: ${157500:,}")
print(f"     - Conceptual Design: ${262500:,}")
print(f"     - Design Development: ${315000:,}")
print(f"     - Construction Documents: ${157500:,}")
print(f"     - Construction Observation: ${157500:,}")
print(f"   TOTAL: ${contract_data['total_fee']:,}")
print("\n💳 Payment Terms:")
print("   - Payment within 30 days of invoice")
print("   - Late interest: 1.5% per month after 60 days")
print("   - Progress-based payments per phase")
print("   - Fees exclusive of taxes (Client bears VAT)")
print("   - 10% restart fee if work suspended >60 days")
print("\n📌 Notes:")
print("   - This is a MAJOR $3M luxury residence project")
print("   - Includes master planning, branding narrative, storytelling")
print("   - Full interior design for all unit types, shared spaces")
print("   - Complete landscape design for 7-acre site")
print("   - Sports & recreational courts, club amenities")
print("   - 6-8 differentiated interior mock-up units")
print("\n" + "="*80)

confirm = input("\n❓ Proceed with import? (y/n): ").strip().lower()

if confirm == 'y':
    import_contract(project_code, contract_data)
    print("\n✅ Import successful!")
    print("\n📝 Next steps:")
    print("   1. Set up 10 phase milestones for invoicing")
    print("   2. Track separately: Interior ($1.95M) + Landscape ($1.05M)")
    print("   3. Monitor 36-month timeline (Aug 2025 - Aug 2028)")
    print("   4. Note: Non-refundable mobilization fee due on signing")
else:
    print("\n❌ Import cancelled")
