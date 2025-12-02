#!/usr/bin/env python3
"""
Import 25 BK-013 Tel Aviv High Rise Project Addendum
May 1, 2025 - Addendum to 2022 Agreement
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-013
project_code = "25 BK-013"

contract_data = {
    'client_name': "Nitsba Holding 1995 Ltd.",
    'total_fee': 1155000,  # USD 1,155,000 (addendum fee)
    'contract_duration': 10,  # 10 months (May 2025 - February 2026)
    'contract_date': "2025-05-01",
    'payment_terms': None,  # Not specified in addendum (refers to 2022 agreement)
    'late_interest': None,  # Refers to original 2022 agreement
    'stop_work_days': None,  # Refers to original 2022 agreement
    'restart_fee': None,  # Refers to original 2022 agreement

    # Fee breakdown by discipline and phase
    'fee_breakdown': [
        # LANDSCAPE ARCHITECTURAL - $180,000
        ('Landscape', 'Design Development', 120000, 10.4),
        ('Landscape', 'Construction Documents', 60000, 5.2),

        # INTERIOR DESIGN - $975,000
        ('Interior', 'Design Development (70%)', 585000, 50.6),
        ('Interior', 'Construction Document', 390000, 33.8),
    ]
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-013 - TEL AVIV HIGH RISE ADDENDUM ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: {contract_data['client_name']}")
print(f"   Addendum Fee: ${contract_data['total_fee']:,}")
print(f"   Period: May 2025 - February 2026 (10 months)")
print(f"   Addendum Date: {contract_data['contract_date']}")
print(f"   Parent Contract: 2022 Agreement (April 4, 2022)")
print("\n💰 Fee Breakdown:")
print(f"   Landscape Architectural: ${180000:,}")
print(f"     - Design Development: ${120000:,}")
print(f"     - Construction Documents: ${60000:,}")
print(f"   Interior Design: ${975000:,}")
print(f"     - 70% Design Development: ${585000:,}")
print(f"     - Construction Document: ${390000:,}")
print(f"   TOTAL: ${contract_data['total_fee']:,}")
print("\n💳 Payment Terms:")
print("   - 10 monthly installments of $115,500")
print("   - May 1, 2025 - February 28, 2026")
print("   - Contingent on progress per timeline")
print("   - Fees exclusive of taxes (Client bears VAT)")
print("\n📌 Notes:")
print("   - This is an ADDENDUM to the April 4, 2022 agreement")
print("   - Extends completion from Sep 2025 to Feb 28, 2026")
print("   - Covers Design Development & Construction Documents")
print("   - Construction Observation fees require negotiation")
print("   - Monthly payments cover additional works & client changes")
print("\n" + "="*80)

confirm = input("\n❓ Proceed with import? (y/n): ").strip().lower()

if confirm == 'y':
    import_contract(project_code, contract_data)
    print("\n✅ Import successful!")
    print("\n📝 Next steps:")
    print("   1. Link to original 2022 Agreement if it exists in system")
    print("   2. Set up 10 monthly payment milestones ($115,500 each)")
    print("   3. Review timeline in Appendix 1 for detailed schedule")
    print("   4. Note: Construction Observation fees not yet agreed")
else:
    print("\n❌ Import cancelled")
