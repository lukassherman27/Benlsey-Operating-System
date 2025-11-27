#!/usr/bin/env python3
"""
Import 25 BK-024 Four Seasons Tented Camp Chiangrai Maintenance
April 17, 2025 - Annual Landscape Maintenance Services (2025)
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-024
project_code = "25 BK-024"

contract_data = {
    'client_name': "Baan Boran Chiang Rai Co., Ltd. Branch 2",
    'total_fee': 9091,  # 300,000 THB ≈ USD 9,091 (at ~33 THB/USD)
    'contract_duration': 13,  # May 2025 - May 2026 (13 months)
    'contract_date': "2025-04-17",
    'payment_terms': 30,  # 30 days
    'late_interest': 1.0,  # 1% per month after 60 days
    'stop_work_days': None,  # Not specified in maintenance contract
    'restart_fee': None,  # Not specified

    # Maintenance contract - no phase breakdown, service-based
    'fee_breakdown': []
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-024 - FOUR SEASONS CHIANGRAI MAINTENANCE ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: {contract_data['client_name']}")
print(f"   Maintenance Fee: 300,000 THB (≈ ${contract_data['total_fee']:,} USD)")
print(f"   Period: May 1, 2025 - May 31, 2026 (13 months)")
print(f"   Contract Date: {contract_data['contract_date']}")
print(f"   Signed Date: April 19, 2025")
print("\n🔧 Scope of Work:")
print("   - Annual landscape architectural maintenance services")
print("   - 1 field visit @ 300,000 Baht per trip")
print("   - Conceptual Design")
print("   - Design Development Services")
print("   - Construction Document")
print("   - Construction Administration")
print("\n💰 Payment Terms:")
print("   - Payment within 30 days of invoice")
print("   - Late interest: 1% per month after 60 days")
print("   - Monthly invoicing allowed for completed/in-progress work")
print("   - Fees in Thai Baht, exclusive of withholding tax and VAT")
print("\n🏨 Special Provisions:")
print("   - Free accommodation for W.R. Bensley & J. Rengthong")
print("   - Includes food, beverage, spa, hotel facilities")
print("   - Travel expenses reimbursed at cost")
print("   - Business class airfare, taxis reimbursed")
print("\n📌 Notes:")
print("   - This is a MAINTENANCE contract, not a full design contract")
print("   - Service-based with 1 year completion period")
print("   - 1 month acceptance period")
print("   - Location: 499 Moo 1, Tumbol Vieng, Chiang Saen, Chiang Rai")
print("\n" + "="*80)

confirm = input("\n❓ Proceed with import? (y/n): ").strip().lower()

if confirm == 'y':
    import_contract(project_code, contract_data)
    print("\n✅ Import successful!")
    print("\n📝 Next steps:")
    print("   1. Track field visit schedule (May 2025 - May 2026)")
    print("   2. Monitor monthly invoice opportunities")
    print("   3. Coordinate with Four Seasons Tented Camp Chiangrai team")
else:
    print("\n❌ Import cancelled")
