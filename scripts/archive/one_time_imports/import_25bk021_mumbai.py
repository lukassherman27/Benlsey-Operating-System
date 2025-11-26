#!/usr/bin/env python3
"""
Import 25 BK-021 Art Deco Residential Project Mumbai Addendum
March 3, 2025 - Redesign Addendum to Contract 23 BK-093
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-021
project_code = "25 BK-021"

contract_data = {
    'client_name': "25 Downtown Realty Limited (formerly Joyous Housing Limited)",
    'total_fee': 750000,  # USD 750,000 (addendum redesign fee)
    'contract_duration': None,  # Refers to parent contract 23 BK-093
    'contract_date': "2025-03-03",
    'payment_terms': None,  # Refers to parent contract
    'late_interest': None,  # Refers to parent contract
    'stop_work_days': None,  # Refers to parent contract
    'restart_fee': None,  # Refers to parent contract

    # Redesign addendum - milestone-based payments
    'fee_breakdown': [
        # Redesign fee breakdown
        ('Interior', 'Redesign - Sales Center', 300000, 40.0),
        ('Interior', 'Redesign - Main Towers', 450000, 60.0),
    ]
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-021 - MUMBAI ART DECO REDESIGN ADDENDUM ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: {contract_data['client_name']}")
print(f"   Addendum Fee: ${contract_data['total_fee']:,}")
print(f"   Contract Date: {contract_data['contract_date']}")
print(f"   Parent Contract: 23 BK-093 (November 22, 2023)")
print("\n🏗️ Project Scope:")
print("   Type: Art Deco Residential Project (Mumbai, India)")
print("   Redesign Work:")
print("     - Conceptual design redesign (sales center + main towers)")
print("     - Design development drawings redesign")
print("\n💰 Fee Breakdown (Addendum):")
print(f"   Sales Center Redesign: ${300000:,}")
print(f"   Main Towers Redesign: ${450000:,}")
print(f"   ADDENDUM TOTAL: ${contract_data['total_fee']:,}")
print("\n📌 Additional Fees from Parent Contract (23 BK-093):")
print(f"   Inherited Construction Docs & Observation: ${433125:,}")
print(f"     - Sale Center Construction Document: ${50625:,}")
print(f"     - Main Tower Construction Document: ${157500:,}")
print(f"     - Sale Center Construction Observation: ${67500:,}")
print(f"     - Main Tower Construction Observation: ${157500:,}")
print("\n💳 Payment Terms:")
print("   - Refers to parent contract 23 BK-093")
print("   - Redesign fees claimed when drawings completed")
print("   - All fees net of deductions, exclusive of VAT")
print("   - Client bears all taxes")
print("\n📌 Notes:")
print("   - This is an ADDENDUM for redesign work")
print("   - Parent contract 23 BK-093 dated November 22, 2023")
print("   - All other provisions of parent contract remain binding")
print("   - Location: Site Office, Tulsiwadi, Tardeo, Mumbai - 400034")
print("\n" + "="*80)

confirm = input("\n❓ Proceed with import? (y/n): ").strip().lower()

if confirm == 'y':
    import_contract(project_code, contract_data)
    print("\n✅ Import successful!")
    print("\n📝 Next steps:")
    print("   1. Link to parent contract 23 BK-093 if it exists in system")
    print("   2. Track redesign milestones for sales center and main towers")
    print("   3. Monitor inherited fees from parent contract separately")
    print("   4. Note: Payment terms reference original agreement")
else:
    print("\n❌ Import cancelled")
