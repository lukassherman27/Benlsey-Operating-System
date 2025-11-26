#!/usr/bin/env python3
"""
Import 25 BK-040 Ritz Carlton Reserve Nusa Dua - Branding Consultancy
September 3, 2025 - Addendum to Contract 25 BK-033
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-040
project_code = "25 BK-040"

contract_data = {
    'client_name': "PT. Bali Destinasi Lestari",
    'total_fee': 125000,  # USD 125,000
    'contract_duration': None,  # Refers to parent contract 25 BK-033
    'contract_date': "2025-09-03",
    'payment_terms': 30,  # Inherits from parent contract
    'late_interest': 1.5,  # 1.5% per month after 45 days (from parent)
    'stop_work_days': 45,  # From parent contract
    'restart_fee': 10.0,  # 10% restart fee (from parent)

    # Branding addendum - no phase breakdown, scope-based deliverables
    'fee_breakdown': []
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-040 - RITZ CARLTON NUSA DUA BRANDING ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: {contract_data['client_name']}")
print(f"   Addendum Fee: ${contract_data['total_fee']:,}")
print(f"   Contract Date: {contract_data['contract_date']}")
print(f"   Parent Contract: 25 BK-033 (June 30, 2025)")
print("\n🎨 Branding Scope (5 Steps):")
print("   Step 1: Market, Customer & Competitor Analysis")
print("   Step 2: Positioning, Identity & Messaging")
print("   Step 3: Experience Blueprint")
print("   Step 4: Sales, Marketing, Operational Collaterals & Supplies List")
print("   Step 5: Brand Consultancy & Immersions")
print("\n💰 Fee Structure:")
print(f"   Branding Consultancy Fee: ${contract_data['total_fee']:,}")
print("\n💳 Payment Terms (from Parent Contract 25 BK-033):")
print("   - Payment within 30 days of invoice")
print("   - Late interest: 1.5% per month after 45 days")
print("   - Can suspend work after 45 days delinquency")
print("   - 10% restart fee if suspended")
print("   - Fees exclusive of taxes (Client bears VAT)")
print("\n📌 Notes:")
print("   - This is an ADDENDUM to Contract 25 BK-033")
print("   - Adds branding consultancy services to main design contract")
print("   - All other provisions of parent contract remain binding")
print("   - Branding deliverables per Ritz Reserve requirements")
print("   - Includes brand positioning, experience blueprint, collaterals")
print("\n" + "="*80)

confirm = input("\n❓ Proceed with import? (y/n): ").strip().lower()

if confirm == 'y':
    import_contract(project_code, contract_data)
    print("\n✅ Import successful!")
    print("\n📝 Next steps:")
    print("   1. Link to parent contract 25 BK-033 if needed")
    print("   2. Track branding deliverables across 5 steps")
    print("   3. Note: Payment terms inherit from parent contract")
    print("   4. This addendum adds $125K to the $3.15M main contract")
else:
    print("\n❌ Import cancelled")
