#!/usr/bin/env python3
"""
Comprehensive Invoice & Project Link Audit
Shows EVERY invoice, proposal, and project link with detailed explanations
"""

import sqlite3
import os
import re
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv('DATABASE_PATH', './database/bensley_master.db')

def extract_code_from_invoice(invoice_number):
    """Extract project code number from invoice (e.g., I24-017 → 017)"""
    match = re.search(r'I?\d{2}-?(\d{3})', invoice_number)
    if match:
        return match.group(1)
    return None

def find_all_matching_projects(cursor, code_num):
    """Find ALL projects that could match this code number"""
    codes_to_try = [
        f'BK-{code_num}',
        f'25 BK-{code_num}',
        f'25BK-{code_num}',
        f'23 BK-{code_num}',
        f'24 BK-{code_num}',
    ]

    matches = []
    for code in codes_to_try:
        cursor.execute("""
            SELECT project_id, project_code, project_title
            FROM projects
            WHERE project_code = ?
        """, (code,))
        result = cursor.fetchone()
        if result:
            matches.append({
                'project_id': result[0],
                'project_code': result[1],
                'project_name': result[2]  # Using project_title from DB
            })

    return matches

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("="*100)
    print("COMPREHENSIVE BENSLEY INVOICE & PROJECT LINK AUDIT")
    print("="*100)

    # PART 1: SHOW ALL INVOICES
    print("\n" + "="*100)
    print("PART 1: ALL INVOICES ANALYSIS (253 invoices)")
    print("="*100)

    cursor.execute("""
        SELECT
            i.invoice_id,
            i.invoice_number,
            i.project_id as current_project_id,
            p.project_code as current_project_code,
            p.project_title as current_project_name,
            i.invoice_amount,
            i.payment_amount,
            i.status
        FROM invoices i
        LEFT JOIN projects p ON i.project_id = p.project_id
        ORDER BY i.invoice_number
    """)

    all_invoices = cursor.fetchall()

    correct_links = []
    wrong_links = []
    unlinked = []
    uncertain = []

    for inv in all_invoices:
        inv_id, inv_num, curr_proj_id, curr_code, curr_name, amount, paid, status = inv

        # Extract expected project code
        code_num = extract_code_from_invoice(inv_num)

        if not code_num:
            uncertain.append({
                'invoice': inv_num,
                'current_project_id': curr_proj_id,
                'current_project_code': curr_code,
                'reason': 'Cannot extract project code from invoice number',
                'amount': amount,
                'paid': paid
            })
            continue

        # Find matching projects
        matches = find_all_matching_projects(cursor, code_num)

        if not matches:
            wrong_links.append({
                'invoice': inv_num,
                'current_project_id': curr_proj_id,
                'current_project_code': curr_code,
                'current_project_name': curr_name,
                'expected_code': f'*-{code_num}',
                'expected_project_id': None,
                'reason': f'No project found with code ending in {code_num}',
                'amount': amount,
                'paid': paid
            })
            continue

        # Check if current link is correct
        expected_proj_id = matches[0]['project_id']
        expected_code = matches[0]['project_code']
        expected_name = matches[0]['project_name']

        if curr_proj_id == expected_proj_id:
            correct_links.append({
                'invoice': inv_num,
                'project_id': curr_proj_id,
                'project_code': curr_code,
                'project_name': curr_name,
                'amount': amount,
                'paid': paid
            })
        else:
            wrong_links.append({
                'invoice': inv_num,
                'current_project_id': curr_proj_id,
                'current_project_code': curr_code,
                'current_project_name': curr_name,
                'expected_project_id': expected_proj_id,
                'expected_code': expected_code,
                'expected_name': expected_name,
                'reason': 'Linked to wrong project',
                'amount': amount,
                'paid': paid
            })

    # Print summary
    print(f"\n✅ CORRECT LINKS: {len(correct_links)}/253")
    print(f"❌ WRONG LINKS: {len(wrong_links)}/253")
    print(f"⚠️  UNLINKED: {len(unlinked)}/253")
    print(f"❓ UNCERTAIN: {len(uncertain)}/253")

    # Show wrong links in detail
    if wrong_links:
        print("\n" + "="*100)
        print(f"DETAILED BREAKDOWN: {len(wrong_links)} WRONG LINKS")
        print("="*100)

        total_wrong_paid = 0
        for i, link in enumerate(wrong_links, 1):
            print(f"\n[{i}/{len(wrong_links)}] Invoice: {link['invoice']}")
            print(f"  💰 Amount: ${link['amount']:,.2f} | Paid: ${link['paid'] or 0:,.2f}")
            print(f"  ❌ CURRENTLY LINKED TO:")
            print(f"      Project ID: {link['current_project_id']}")
            print(f"      Project Code: {link['current_project_code']}")
            print(f"      Project Name: {link['current_project_name']}")

            if link.get('expected_project_id'):
                print(f"  ✅ SHOULD BE LINKED TO:")
                print(f"      Project ID: {link['expected_project_id']}")
                print(f"      Project Code: {link['expected_code']}")
                print(f"      Project Name: {link['expected_name']}")
            else:
                print(f"  ⚠️  PROBLEM: {link['reason']}")

            total_wrong_paid += (link['paid'] or 0)

        print(f"\n💸 Total revenue tracked incorrectly: ${total_wrong_paid:,.2f}")

    # PART 2: PROPOSAL → PROJECT LINKS
    print("\n\n" + "="*100)
    print("PART 2: PROPOSAL → PROJECT LINKING LOGIC")
    print("="*100)

    print("\n📊 Database Overview:")
    cursor.execute("SELECT COUNT(*) FROM proposals")
    total_proposals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM proposals WHERE status = 'won'")
    won_proposals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM proposals WHERE status = 'active'")
    active_proposals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM projects")
    total_projects = cursor.fetchone()[0]

    print(f"  • Total Proposals: {total_proposals}")
    print(f"  • Won Proposals: {won_proposals}")
    print(f"  • Active Proposals: {active_proposals}")
    print(f"  • Total Projects: {total_projects}")

    # Show won/active proposals and their matching
    print("\n" + "="*100)
    print("WON/ACTIVE PROPOSALS → PROJECT MATCHING")
    print("="*100)

    cursor.execute("""
        SELECT proposal_id, project_code, project_name, status, project_value
        FROM proposals
        WHERE status IN ('won', 'active')
        ORDER BY project_code
    """)

    won_active_proposals = cursor.fetchall()

    matched = []
    unmatched = []

    for prop in won_active_proposals:
        prop_id, prop_code, prop_name, status, value = prop

        # Extract code number
        code_match = re.search(r'BK-?(\d{3})', prop_code)
        if not code_match:
            unmatched.append({
                'proposal_id': prop_id,
                'proposal_code': prop_code,
                'proposal_name': prop_name,
                'status': status,
                'reason': 'Cannot extract BK code number'
            })
            continue

        code_num = code_match.group(1)

        # Find matching project
        matches = find_all_matching_projects(cursor, code_num)

        if matches:
            matched.append({
                'proposal_id': prop_id,
                'proposal_code': prop_code,
                'proposal_name': prop_name,
                'status': status,
                'value': value,
                'project_id': matches[0]['project_id'],
                'project_code': matches[0]['project_code'],
                'project_name': matches[0]['project_name']
            })
        else:
            unmatched.append({
                'proposal_id': prop_id,
                'proposal_code': prop_code,
                'proposal_name': prop_name,
                'status': status,
                'value': value,
                'reason': f'No project found with code *-{code_num}'
            })

    print(f"\n✅ CAN AUTO-MATCH: {len(matched)}/{len(won_active_proposals)}")
    print(f"❌ CANNOT MATCH: {len(unmatched)}/{len(won_active_proposals)}")

    if matched:
        print("\n" + "-"*100)
        print(f"MATCHED PROPOSALS (will be linked)")
        print("-"*100)
        for m in matched:
            print(f"\n  Proposal: {m['proposal_code']} (ID: {m['proposal_id']})")
            print(f"    Name: {m['proposal_name']}")
            print(f"    Status: {m['status']}")
            print(f"    Value: ${m['value']:,.2f}" if m['value'] else "    Value: Not specified")
            print(f"  ↓")
            print(f"  Project: {m['project_code']} (ID: {m['project_id']})")
            print(f"    Name: {m['project_name']}")

    if unmatched:
        print("\n" + "-"*100)
        print(f"UNMATCHED PROPOSALS (need manual review)")
        print("-"*100)
        for u in unmatched:
            print(f"\n  Proposal: {u['proposal_code']} (ID: {u['proposal_id']})")
            print(f"    Name: {u['proposal_name']}")
            print(f"    Status: {u['status']}")
            print(f"    Reason: {u['reason']}")

    # PART 3: EXPLAIN THE MATCHING LOGIC
    print("\n\n" + "="*100)
    print("PART 3: HOW THE MATCHING LOGIC WORKS")
    print("="*100)

    print("""
INVOICE MATCHING LOGIC:
━━━━━━━━━━━━━━━━━━━━━

Step 1: Extract project code number from invoice number
  Example: I24-017 → Extract "017"
  Example: I25-088 → Extract "088"

Step 2: Try to find project with matching code in this order:
  1. BK-017
  2. 25 BK-017
  3. 25BK-017
  4. 23 BK-017
  5. 24 BK-017

Step 3: Compare to current link
  • If invoice.project_id matches found project → CORRECT ✅
  • If invoice.project_id doesn't match → WRONG ❌
  • If no project found → MISSING PROJECT ⚠️

Example:
  Invoice: I24-017
  Extract: "017"
  Search: BK-017, 25 BK-017, 25BK-017, 23 BK-017, 24 BK-017
  Found: 25 BK-017 (project_id: 115075) - TARC
  Current Link: project_id 3613 (23 BK-088 - Mandarin Oriental Bali)
  Result: WRONG ❌ - Should be 115075, not 3613


PROPOSAL → PROJECT MATCHING LOGIC:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Get all proposals with status 'won' or 'active'
  These are proposals that should have become projects

Step 2: Extract BK code number from proposal code
  Example: BK-017 → Extract "017"
  Example: 25BK-088 → Extract "088"

Step 3: Use same search logic as invoices to find matching project

Step 4: Create bidirectional link
  proposals.active_project_id → projects.project_id
  projects.proposal_id → proposals.proposal_id


WHY SOME DON'T MATCH:
━━━━━━━━━━━━━━━━━━━━

• Proposal code format doesn't contain BK-XXX pattern
• Project exists but uses completely different code
• Proposal won but project not yet created in database
• Project was renamed/recoded after proposal (like BK-008 → BK-017)
    """)

    # PART 4: SUMMARY
    print("\n" + "="*100)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*100)

    print(f"\n📊 Invoice Status:")
    print(f"  ✅ Correctly linked: {len(correct_links)} invoices")
    print(f"  ❌ Wrongly linked: {len(wrong_links)} invoices")
    print(f"  ❓ Need manual review: {len(uncertain)} invoices")

    print(f"\n📊 Proposal→Project Status:")
    print(f"  ✅ Can auto-link: {len(matched)} proposals")
    print(f"  ❌ Need manual linking: {len(unmatched)} proposals")

    print(f"\n💡 Next Steps:")
    print(f"  1. Review the {len(wrong_links)} wrong invoice links above")
    print(f"  2. Confirm the auto-matching logic makes sense")
    print(f"  3. Manually resolve the {len(unmatched)} unmatched proposals")
    print(f"  4. Run fix_project_lifecycle_links.py --live to apply fixes")

    conn.close()

if __name__ == '__main__':
    main()
