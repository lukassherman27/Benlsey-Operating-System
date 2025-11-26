#!/usr/bin/env python3
"""
Fix 3 Proposal Status Inconsistencies

Based on email validator findings:
1. BK-033 (Ritz Carlton Nusa Dua): "won" → "active" (in delivery)
2. BK-008 (TARC New Delhi): empty → "proposal" (active sales)
3. BK-051 (Pawana Lake Mumbai): "lost" → needs review
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("=" * 80)
    print("FIXING PROPOSAL STATUS INCONSISTENCIES")
    print("=" * 80)

    db_path = os.getenv('DATABASE_PATH', 'database/bensley_master.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check current status
    print("\n📊 Current Status of Problem Proposals:\n")

    cursor.execute("""
        SELECT project_code, project_name, status,
               (SELECT COUNT(*) FROM email_proposal_links epl
                WHERE epl.proposal_id = proposals.proposal_id) as email_count
        FROM proposals
        WHERE project_code IN ('BK-033', 'BK-008', 'BK-051')
    """)

    for row in cursor.fetchall():
        status = row['status'] or '(empty)'
        print(f"  {row['project_code']}: {row['project_name'][:50]}")
        print(f"    Status: {status}")
        print(f"    Linked emails: {row['email_count']}")
        print()

    # Ask for confirmation
    print("\n🔧 Proposed Fixes:")
    print("  1. BK-033: 'won' → 'active' (contract won, now in delivery)")
    print("  2. BK-008: empty → 'proposal' (active sales pipeline)")
    print("  3. BK-051: 'lost' → REVIEW (check if emails are mis-linked)")
    print()

    response = input("Apply fixes 1 and 2? (y/N): ").strip().lower()

    if response != 'y':
        print("❌ Cancelled")
        return

    # Fix BK-033
    cursor.execute("""
        UPDATE proposals
        SET status = 'active'
        WHERE project_code = 'BK-033'
    """)
    print("✅ BK-033: Updated 'won' → 'active' (contract in delivery phase)")

    # Fix BK-008
    cursor.execute("""
        UPDATE proposals
        SET status = 'proposal'
        WHERE project_code = 'BK-008'
    """)
    print("✅ BK-008: Updated empty → 'proposal' (active sales)")

    # BK-051 - leave as is, needs manual review
    print("⚠️  BK-051: Left as 'lost' - needs manual review (44 linked emails suggest may be mis-linked)")

    conn.commit()

    # Verify changes
    print("\n📊 Updated Status:\n")
    cursor.execute("""
        SELECT project_code, project_name, status
        FROM proposals
        WHERE project_code IN ('BK-033', 'BK-008', 'BK-051')
    """)

    for row in cursor.fetchall():
        status = row['status'] or '(empty)'
        print(f"  {row['project_code']}: {status}")

    conn.close()
    print("\n✅ Fixes applied!\n")

if __name__ == '__main__':
    main()
