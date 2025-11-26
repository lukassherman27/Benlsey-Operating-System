#!/usr/bin/env python3
"""
Quick Proposal Status Marker
Mark proposals as lost, on hold, or cancelled to filter from health monitor
"""
import sqlite3
from pathlib import Path
import sys

def mark_bulk_status(db_path, auto_choice=None):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("="*80)
    print("📝 BULK PROPOSAL STATUS UPDATER")
    print("="*80)

    # Show proposals without emails (likely dead)
    cursor.execute("""
        SELECT p.project_code, p.project_name, p.status
        FROM proposals p
        LEFT JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
        WHERE p.is_active_project = 0
          AND epl.link_id IS NULL
        ORDER BY p.project_code
    """)

    no_email_proposals = cursor.fetchall()

    print(f"\n📊 {len(no_email_proposals)} proposals have NO email activity")
    print("(These are likely dead/on hold/cancelled)\n")

    if not auto_choice:
        print("Options:")
        print("  1. Mark ALL as 'lost' (cancelled/dead)")
        print("  2. Mark ALL as 'on_hold' (may resume)")
        print("  3. Show list and mark individually")
        print("  4. Keep as is")
        choice = input("\nChoice (1-4): ").strip()
    else:
        choice = auto_choice
        print(f"Auto-running option {choice}")

    if choice == '1':
        # Mark all as lost
        if auto_choice:
            confirm = 'yes'
        else:
            confirm = input(f"Mark {len(no_email_proposals)} proposals as 'lost'? (yes/no): ").strip().lower()

        if confirm == 'yes':
            for prop in no_email_proposals:
                cursor.execute("""
                    UPDATE proposals
                    SET status = 'lost',
                        on_hold = 0
                    WHERE project_code = ?
                """, (prop['project_code'],))
            conn.commit()
            print(f"\n✓ Marked {len(no_email_proposals)} proposals as 'lost'")

    elif choice == '2':
        # Mark all as on hold
        if auto_choice:
            confirm = 'yes'
            reason = "No recent activity"
        else:
            confirm = input(f"Mark {len(no_email_proposals)} proposals as 'on_hold'? (yes/no): ").strip().lower()
            reason = input("Reason (optional): ").strip() if confirm == 'yes' else ""

        if confirm == 'yes':
            for prop in no_email_proposals:
                cursor.execute("""
                    UPDATE proposals
                    SET on_hold = 1,
                        on_hold_reason = ?
                    WHERE project_code = ?
                """, (reason or "No recent activity", prop['project_code']))
            conn.commit()
            print(f"\n✓ Marked {len(no_email_proposals)} proposals as 'on_hold'")

    elif choice == '3':
        # Individual marking
        for prop in no_email_proposals:
            print(f"\n{prop['project_code']}: {prop['project_name'][:60]}")
            print("  1. Lost/Cancelled")
            print("  2. On Hold")
            print("  3. Active (keep)")
            print("  s. Skip")

            status = input("  Choice: ").strip()

            if status == '1':
                cursor.execute("""
                    UPDATE proposals
                    SET status = 'lost',
                        on_hold = 0
                    WHERE project_code = ?
                """, (prop['project_code'],))
                print("  ✓ Marked as lost")

            elif status == '2':
                cursor.execute("""
                    UPDATE proposals
                    SET on_hold = 1,
                        on_hold_reason = 'No recent activity'
                    WHERE project_code = ?
                """, (prop['project_code'],))
                print("  ✓ Marked as on hold")

            elif status == '3':
                print("  ✓ Kept as active")

        conn.commit()
        print("\n✓ Updates saved")

    conn.close()
    print("\nRun proposal_health_monitor.py to see updated list!")

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/bensley_master.db"
    auto_choice = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        return

    mark_bulk_status(db_path, auto_choice)

if __name__ == "__main__":
    main()
