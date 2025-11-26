#!/usr/bin/env python3
"""
Import 25 BK-018 Ritz Carlton Nanyan Bay Extension Contract
February 21, 2025 - March 2025 to March 2026
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-018
project_code = "25 BK-018"

contract_data = {
    'client_name': "Hainan Golden Tide Tourism Development Co Ltd.",
    'total_fee': 225000,  # New extension fee
    'contract_duration': 12,  # March 2025 - March 2026
    'contract_date': "2025-02-21",
    'payment_terms': 30,  # Standard 30 days for travel reimbursement
    'late_interest': None,  # Not specified in extension (refer to original)
    'stop_work_days': None,  # Not specified in extension (refer to original)
    'restart_fee': None,  # Not specified in extension (refer to original)

    # Extension contracts don't have detailed phase breakdowns
    # They're just continuation fees, so no fee_breakdown needed
    'fee_breakdown': []
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-018 - RITZ CARLTON NANYAN BAY EXTENSION ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: {contract_data['client_name']}")
print(f"   Extension Fee: ${contract_data['total_fee']:,}")
print(f"   Period: March 2025 - March 2026 (12 months)")
print(f"   Contract Date: {contract_data['contract_date']}")
print("\n💰 Payment Schedule:")
print("   1st: $56,250 - On execution")
print("   2nd: $56,250 - July 15, 2025")
print("   3rd: $56,250 - November 15, 2025")
print("   4th: $56,250 - March 15, 2026")
print("\n⚠️  OUTSTANDING FROM PREVIOUS CONTRACT (23 BK-040):")
print("   Invoice #I24-037: $56,250 (June 15, 2024)")
print("\n📌 Notes:")
print("   - This is the 2nd extension to original contract 13 BK-047")
print("   - Amends original agreement from November 4, 2013")
print("   - Client still needs to pay outstanding from first extension")
print("   - After March 2026: $20,000/month until project completion")
print("\n" + "="*80)

confirm = input("\n❓ Proceed with import? (y/n): ").strip().lower()

if confirm == 'y':
    import_contract(project_code, contract_data)
    print("\n✅ Import successful!")
    print("\n📝 Next steps:")
    print("   1. Verify outstanding invoice from 23 BK-040 is in system")
    print("   2. Check if March 2026 has passed → charge $20K/month")
    print("   3. Review all invoices for this project")
else:
    print("\n❌ Import cancelled")
