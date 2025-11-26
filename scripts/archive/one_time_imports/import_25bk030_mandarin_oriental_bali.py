#!/usr/bin/env python3
"""
Import 25 BK-030 Beach Club at Mandarin Oriental Bali
June 3, 2025 - Architectural and Interior Design Service Agreement
"""

import sys
sys.path.append('/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System')

from manual_contract_import import import_contract

# Contract data for 25 BK-030
project_code = "25 BK-030"

contract_data = {
    'client_name': "PT Harmoni Cakrawala Bali",
    'total_fee': 550000,  # USD 550,000
    'contract_duration': 24,  # 24 months
    'contract_date': "2025-06-03",
    'payment_terms': 15,  # 15 days
    'late_interest': 1.5,  # 1.5% per month after 30 days
    'stop_work_days': 45,  # Can suspend after 45 days delinquency
    'restart_fee': 10.0,  # 10% restart fee

    # Fee breakdown by discipline and phase
    'fee_breakdown': [
        # ARCHITECTURAL - $220,000
        ('Architecture', 'Mobilization Fee', 33000, 6.0),
        ('Architecture', 'Conceptual Design', 55000, 10.0),
        ('Architecture', 'Design Development', 66000, 12.0),
        ('Architecture', 'Construction Documents', 33000, 6.0),
        ('Architecture', 'Construction Observation', 33000, 6.0),

        # INTERIOR DESIGN - $330,000
        ('Interior', 'Mobilization Fee', 49500, 9.0),
        ('Interior', 'Conceptual Design', 82500, 15.0),
        ('Interior', 'Design Development', 99000, 18.0),
        ('Interior', 'Construction Documents', 49500, 9.0),
        ('Interior', 'Construction Observation', 49500, 9.0),
    ]
}

print("\n" + "="*80)
print(" IMPORTING 25 BK-030 - BEACH CLUB MANDARIN ORIENTAL BALI ".center(80, "="))
print("="*80)
print("\n📋 Contract Details:")
print(f"   Project: {project_code}")
print(f"   Client: {contract_data['client_name']}")
print(f"   Total Fee: ${contract_data['total_fee']:,}")
print(f"   Duration: 24 months")
print(f"   Contract Date: {contract_data['contract_date']}")
print("\n🏗️ Project Scope:")
print("   Type: Beach Club at Mandarin Oriental Bali")
print("   Location: Bali, Indonesia")
print("   Scope: Full Architectural + Interior Design")
print("   Features:")
print("     - Surf & Water Pavilion with Rip Curl Select Shop")
print("     - Professional surf school with ocean experience")
print("     - 2 Open air Spa Pavilions with cold plunge baths")
print("     - Family area (kid-friendly splash zone, mini surf lessons)")
print("     - Beach BBQ Grill Bar with elevated infinity pool deck")
print("     - Beach activities and cultural crafts")
print("\n💰 Fee Breakdown:")
print(f"   Architectural: ${220000:,}")
print(f"     - Mobilization Fee: ${33000:,}")
print(f"     - Conceptual Design: ${55000:,}")
print(f"     - Design Development: ${66000:,}")
print(f"     - Construction Documents: ${33000:,}")
print(f"     - Construction Observation: ${33000:,}")
print(f"   Interior Design: ${330000:,}")
print(f"     - Mobilization Fee: ${49500:,}")
print(f"     - Conceptual Design: ${82500:,}")
print(f"     - Design Development: ${99000:,}")
print(f"     - Construction Documents: ${49500:,}")
print(f"     - Construction Observation: ${49500:,}")
print(f"   GRAND TOTAL: ${contract_data['total_fee']:,}")
print("\n💳 Payment Terms:")
print("   - Payment within 15 days of invoice")
print("   - Late interest: 1.5% per month after 30 days")
print("   - Can suspend work after 45 days delinquency")
print("   - 10% restart fee if suspended")
print("   - Non-refundable mobilization fee due on signing")
print("   - Fees exclusive of VAT (Client bears taxes)")
print("\n📌 Notes:")
print("   - Comprehensive beach club design for Mandarin Oriental")
print("   - Includes surf pavilion, spa, family area, BBQ grill bar")
print("   - Exclusive Mandarin Oriental collaboration with Rip Curl")
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
    print("   1. Set up 10 phase milestones (5 each for Architecture, Interior)")
    print("   2. Track non-refundable mobilization fees ($82.5K total)")
    print("   3. Monitor 24-month timeline (Jun 2025 - Jun 2027)")
    print("   4. Note: Beach club project for Mandarin Oriental Bali")
else:
    print("\n❌ Import cancelled")
