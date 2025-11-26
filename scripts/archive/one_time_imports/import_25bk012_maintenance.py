#!/usr/bin/env python3
"""
Import 25 BK-012 Four Seasons Bangkok Design Maintenance
February 6, 2025 - Annual Landscape Maintenance Services (2025)
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-012
project_code = "25 BK-012"

contract_data = {
    'client_name': "Urban Resort Hotel Co., Ltd. Branch 00001 dba. Four Seasons Hotel Bangkok at Chao Phraya River",
    'total_fee': 27273,  # 900,000 THB ≈ USD 27,273 (at ~33 THB/USD)
    'contract_duration': 12,  # 1 year maintenance contract (2025)
    'contract_date': "2025-02-06",
    'payment_terms': 30,  # 30 days
    'late_interest': 1.0,  # 1% per month after 60 days
    'stop_work_days': None,  # Not specified in maintenance contract
    'restart_fee': None,  # Not specified

    # Maintenance contract - no phase breakdown, service-based
    'fee_breakdown': []
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-012 - FOUR SEASONS BANGKOK MAINTENANCE ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: Four Seasons Hotel Bangkok at Chao Phraya River")
print(f"   Maintenance Fee: 900,000 THB (≈ ${contract_data['total_fee']:,} USD)")
print(f"   Period: 2025 (1 year)")
print(f"   Contract Date: {contract_data['contract_date']}")
print("\n🔧 Scope of Work:")
print("   - Annual landscape architectural maintenance services")
print("   - 3 field visits (300,000 Baht per trip)")
print("   - Conceptual Design")
print("   - Design Development Services")
print("   - Construction Document")
print("   - Construction Administration")
print("   - Plant budget: 600,000 Baht for three trips")
print("\n💰 Payment Terms:")
print("   - Payment within 30 days of invoice")
print("   - Late interest: 1% per month after 60 days")
print("   - BDS invoices monthly for completed/in-progress work")
print("\n📌 Notes:")
print("   - This is a MAINTENANCE contract, not a full design contract")
print("   - Service-based with field visits Feb 15 - Feb 28, 2025")
print("   - No detailed phase breakdown (ongoing maintenance)")
print("   - Fee in Thai Baht, converted to USD for database")
print("\n" + "="*80)

confirm = input("\n❓ Proceed with import? (y/n): ").strip().lower()

if confirm == 'y':
    import_contract(project_code, contract_data)
    print("\n✅ Import successful!")
    print("\n📝 Next steps:")
    print("   1. Create milestones for the 3 field visits")
    print("   2. Track plant budget separately (600,000 Baht)")
    print("   3. Monitor invoice schedule (monthly billing allowed)")
else:
    print("\n❌ Import cancelled")
