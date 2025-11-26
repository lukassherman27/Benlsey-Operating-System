#!/usr/bin/env python3
"""
Import 25 BK-023 Sun Phu Quoc Airways Branding Contract
May 15, 2025 - Logo & Livery Design Service Agreement
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-023
project_code = "25 BK-023"

contract_data = {
    'client_name': "SUN PHU QUOC AIRWAYS LIMITED LIABILITY COMPANY",
    'total_fee': 250000,  # USD 250,000
    'contract_duration': 24,  # 24 months
    'contract_date': "2025-05-15",
    'payment_terms': 15,  # 15 days
    'late_interest': 1.5,  # 1.5% per month after 30 days
    'stop_work_days': 45,  # Can suspend after 45 days delinquency
    'restart_fee': 10.0,  # 10% restart fee

    # Branding contract - no phase breakdown, milestone-based payments
    'fee_breakdown': []
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-023 - SUN PHU QUOC AIRWAYS BRANDING ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: {contract_data['client_name']}")
print(f"   Total Fee: ${contract_data['total_fee']:,}")
print(f"   Duration: 24 months")
print(f"   Contract Date: {contract_data['contract_date']}")
print("\n🎨 Branding Scope (5-Star Airline Logo & Livery):")
print("   - Logo Design & Brand Guidelines")
print("   - Aircraft Livery Design (exterior & interior)")
print("   - Staff Uniform Design")
print("   - Marketing Collateral & Brand Applications")
print("   - F&B Menus, Amenity Kits, Stationery")
print("\n💰 Payment Structure:")
print(f"   Mobilization Fee: ${75000:,} (due on signing)")
print(f"   1st Presentation: ${87500:,}")
print(f"   2nd Presentation: ${87500:,}")
print(f"   TOTAL: ${contract_data['total_fee']:,}")
print("\n💳 Payment Terms:")
print("   - Payment within 15 days of invoice")
print("   - Late interest: 1.5% per month after 30 days")
print("   - Can suspend work after 45 days delinquency")
print("   - 10% restart fee if suspended")
print("   - Fees exclusive of taxes (Client bears VAT)")
print("\n📌 Notes:")
print("   - This is a BRANDING contract for airline logo & livery design")
print("   - 2 design concepts + up to 2 rounds of changes per concept")
print("   - Project for 5-star luxury airline service")
print("   - Comprehensive brand identity & visual guidelines")
print("\n" + "="*80)

confirm = input("\n❓ Proceed with import? (y/n): ").strip().lower()

if confirm == 'y':
    import_contract(project_code, contract_data)
    print("\n✅ Import successful!")
    print("\n📝 Next steps:")
    print("   1. Set up 3 milestone payments (Mobilization, 1st, 2nd Presentation)")
    print("   2. Track branding deliverables as project milestones")
    print("   3. Monitor 24-month timeline (May 2025 - May 2027)")
else:
    print("\n❌ Import cancelled")
