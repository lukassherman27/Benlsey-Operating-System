#!/usr/bin/env python3
"""
Import 25 BK-006 Fenfushi Island Branding Addendum
February 19, 2025 - Luxury Collection Branding Consultancy
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-006
project_code = "25 BK-006"

contract_data = {
    'client_name': "Grand Leisure Venture Private Limited",
    'total_fee': 125000,  # Flat branding consultancy fee
    'contract_duration': None,  # Not specified - branding scope driven
    'contract_date': "2025-02-19",
    'payment_terms': None,  # Refer to parent contract 24 BK-058
    'late_interest': None,  # Refer to parent contract
    'stop_work_days': None,  # Refer to parent contract
    'restart_fee': None,  # Refer to parent contract

    # Branding addendum - no phase breakdown, scope-based deliverables
    'fee_breakdown': []
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-006 - FENFUSHI ISLAND BRANDING ADDENDUM ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: {contract_data['client_name']}")
print(f"   Branding Fee: ${contract_data['total_fee']:,}")
print(f"   Contract Date: {contract_data['contract_date']}")
print(f"   Parent Contract: 24 BK-058 (October 22, 2024)")
print("\n🎨 Branding Scope (Luxury Collection by Marriott):")
print("   1. Market, Customer & Competitor Analysis")
print("   2. Positioning, Identity & Messaging")
print("   3. Experience Blueprint")
print("   4. Sales, Marketing, Operational Collaterals & Supplies List")
print("   5. Brand Consultancy & Immersions")
print("\n📌 Notes:")
print("   - This is an ADDENDUM to parent contract 24 BK-058")
print("   - Flat fee for branding consultancy services")
print("   - Payment terms refer to original agreement")
print("   - Marriott Luxury Collection branding requirements")
print("\n" + "="*80)

confirm = input("\n❓ Proceed with import? (y/n): ").strip().lower()

if confirm == 'y':
    import_contract(project_code, contract_data)
    print("\n✅ Import successful!")
    print("\n📝 Next steps:")
    print("   1. Link to parent contract 24 BK-058 (update parent_project_code)")
    print("   2. Review branding deliverables as milestones")
    print("   3. Check if any invoices have been issued for this addendum")
else:
    print("\n❌ Import cancelled")
