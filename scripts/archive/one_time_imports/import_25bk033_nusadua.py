#!/usr/bin/env python3
"""
Import 25 BK-033 Ritz Carlton Reserve Nusa Dua
June 30, 2025 - Full Landscape, Architectural & Interior Design
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-033
project_code = "25 BK-033"

contract_data = {
    'client_name': "PT. Bali Destinasi Lestari",
    'total_fee': 3150000,  # USD 3,150,000
    'contract_duration': 24,  # 24 months
    'contract_date': "2025-06-30",
    'payment_terms': 30,  # 30 days
    'late_interest': 1.5,  # 1.5% per month after 45 days
    'stop_work_days': 45,  # Can suspend after 45 days delinquency
    'restart_fee': 10.0,  # 10% restart fee

    # Fee breakdown by discipline and phase
    'fee_breakdown': [
        # LANDSCAPE ARCHITECTURAL - $810,000
        ('Landscape', 'Mobilization Fee', 162000, 5.14),
        ('Landscape', 'Conceptual Design', 202500, 6.43),
        ('Landscape', 'Design Development', 243000, 7.71),
        ('Landscape', 'Construction Documents', 121500, 3.86),
        ('Landscape', 'Construction Observation', 81000, 2.57),

        # ARCHITECTURAL - $1,080,000
        ('Architecture', 'Mobilization Fee', 216000, 6.86),
        ('Architecture', 'Conceptual Design', 270000, 8.57),
        ('Architecture', 'Design Development', 324000, 10.29),
        ('Architecture', 'Construction Documents', 162000, 5.14),
        ('Architecture', 'Construction Observation', 108000, 3.43),

        # INTERIOR DESIGN - $1,260,000
        ('Interior', 'Mobilization Fee', 252000, 8.0),
        ('Interior', 'Conceptual Design', 315000, 10.0),
        ('Interior', 'Design Development', 378000, 12.0),
        ('Interior', 'Construction Documents', 189000, 6.0),
        ('Interior', 'Construction Observation', 126000, 4.0),
    ]
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-033 - RITZ CARLTON RESERVE NUSA DUA ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: {contract_data['client_name']}")
print(f"   Total Fee: ${contract_data['total_fee']:,}")
print(f"   Duration: 24 months")
print(f"   Contract Date: {contract_data['contract_date']}")
print("\n🏗️ Project Scope:")
print("   Type: Ritz Carlton Reserve Luxury Resort")
print("   Location: Kawasan Nusa Dua Lot S-5, Bali, Indonesia")
print("   Special: Converting Princess Diana's former villa into wellness center")
print("   Full Landscape + Architecture + Interior Design")
print("\n💰 Fee Breakdown:")
print(f"   Landscape Architectural: ${810000:,}")
print(f"     - Mobilization Fee: ${162000:,}")
print(f"     - Conceptual Design: ${202500:,}")
print(f"     - Design Development: ${243000:,}")
print(f"     - Construction Documents: ${121500:,}")
print(f"     - Construction Observation: ${81000:,}")
print(f"   Architectural: ${1080000:,}")
print(f"     - Mobilization Fee: ${216000:,}")
print(f"     - Conceptual Design: ${270000:,}")
print(f"     - Design Development: ${324000:,}")
print(f"     - Construction Documents: ${162000:,}")
print(f"     - Construction Observation: ${108000:,}")
print(f"   Interior Design: ${1260000:,}")
print(f"     - Mobilization Fee: ${252000:,}")
print(f"     - Conceptual Design: ${315000:,}")
print(f"     - Design Development: ${378000:,}")
print(f"     - Construction Documents: ${189000:,}")
print(f"     - Construction Observation: ${126000:,}")
print(f"   GRAND TOTAL: ${contract_data['total_fee']:,}")
print("\n💳 Payment Terms:")
print("   - Payment within 30 days of invoice")
print("   - Late interest: 1.5% per month on bills past 45 days")
print("   - Non-refundable mobilization fee due on signing")
print("   - Progress-based payments per stage")
print("   - Fees exclusive of VAT (Client bears taxes)")
print("   - 10% restart fee if suspended after 45 days")
print("\n📌 Notes:")
print("   - Comprehensive landscape, architecture & interior design")
print("   - Converting existing villa into dedicated wellness center")
print("   - Princess Diana historically visited this villa")
print("   - Bensley liability limited to 50% of fees paid")
print("   - Governed by Indonesian law")
print("   - 1 month acceptance period")
print("   - Feng Shui additional fee: 12.5% if requested post-brief")
print("\n" + "="*80)

confirm = input("\n❓ Proceed with import? (y/n): ").strip().lower()

if confirm == 'y':
    import_contract(project_code, contract_data)
    print("\n✅ Import successful!")
    print("\n📝 Next steps:")
    print("   1. Set up 15 phase milestones (5 each for Landscape, Architecture, Interior)")
    print("   2. Track non-refundable mobilization fees ($630K total)")
    print("   3. Monitor 24-month timeline (Jun 2025 - Jun 2027)")
    print("   4. Note: This is a MAJOR $3.15M comprehensive design project")
else:
    print("\n❌ Import cancelled")
