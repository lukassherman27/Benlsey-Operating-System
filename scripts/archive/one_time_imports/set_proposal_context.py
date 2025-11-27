#!/usr/bin/env python3
"""
Set Proposal Context
Manually set expectations and context for intelligent health monitoring
"""
import sqlite3
from pathlib import Path
import sys
from datetime import datetime, timedelta

class ProposalContextSetter:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def list_proposals(self):
        """List all proposals"""
        self.cursor.execute("""
            SELECT project_code, project_name, status, health_score
            FROM proposals
            WHERE is_active_project = 0
            ORDER BY project_code
        """)

        proposals = self.cursor.fetchall()
        print("\n📋 PROPOSALS:")
        print("="*80)
        for prop in proposals:
            health = prop['health_score'] or 50
            health_icon = "🔴" if health < 50 else "🟡" if health < 70 else "🟢"
            print(f"{prop['project_code']}: {prop['project_name'][:50]:50} {health_icon} {health:.0f}%")

    def set_context(self, project_code):
        """Set context for a proposal"""
        # Get proposal
        self.cursor.execute("""
            SELECT * FROM proposals WHERE project_code = ?
        """, (project_code,))

        prop = self.cursor.fetchone()
        if not prop:
            print(f"✗ Proposal {project_code} not found")
            return

        print(f"\n{prop['project_code']}: {prop['project_name']}")
        print("="*80)

        # Show current context
        if prop['expected_delay_days']:
            print(f"Current: Expected delay {prop['expected_delay_days']} days")
            if prop['delay_reason']:
                print(f"Reason: {prop['delay_reason']}")

        print("\n💭 What's the current situation?")
        print("  1. Waiting on client response (expected timeline)")
        print("  2. External dependency (land/permit/financing)")
        print("  3. Client said to check back later (specific date)")
        print("  4. Active negotiation (expect fast responses)")
        print("  5. On hold / paused")
        print("  6. Clear all context (normal tracking)")
        print("  7. Cancel")

        choice = input("\nChoice (1-7): ").strip()

        if choice == '7':
            print("Cancelled")
            return

        if choice == '6':
            # Clear all context
            self.cursor.execute("""
                UPDATE proposals
                SET expected_delay_days = NULL,
                    delay_reason = NULL,
                    delay_until_date = NULL,
                    on_hold = 0,
                    on_hold_reason = NULL,
                    project_phase = 'early_exploration'
                WHERE project_code = ?
            """, (project_code,))
            self.conn.commit()
            print("✓ Context cleared")
            return

        if choice == '1':
            # Expected timeline
            days = input("\nHow many days until expected response? ").strip()
            try:
                days = int(days)
            except:
                print("Invalid number")
                return

            reason = input("Reason (optional): ").strip()

            self.cursor.execute("""
                UPDATE proposals
                SET expected_delay_days = ?,
                    delay_reason = ?,
                    project_phase = 'early_exploration'
                WHERE project_code = ?
            """, (days, reason or None, project_code))

        elif choice == '2':
            # External dependency
            dependency = input("\nWhat's the dependency? (land/permit/financing/other): ").strip()
            months = input("Expected timeline (months): ").strip()

            try:
                days = int(months) * 30
            except:
                days = 90

            reason = f"External dependency: {dependency}"

            self.cursor.execute("""
                UPDATE proposals
                SET expected_delay_days = ?,
                    delay_reason = ?,
                    project_phase = 'early_exploration'
                WHERE project_code = ?
            """, (days, reason, project_code))

        elif choice == '3':
            # Check back later
            date_str = input("\nCheck back date (YYYY-MM-DD): ").strip()
            reason = input("Context/reason: ").strip()

            try:
                check_date = datetime.strptime(date_str, '%Y-%m-%d')
                days = (check_date - datetime.now()).days
            except:
                print("Invalid date format")
                return

            self.cursor.execute("""
                UPDATE proposals
                SET expected_delay_days = ?,
                    delay_reason = ?,
                    delay_until_date = ?,
                    project_phase = 'early_exploration'
                WHERE project_code = ?
            """, (days, reason or None, date_str, project_code))

        elif choice == '4':
            # Active negotiation
            self.cursor.execute("""
                UPDATE proposals
                SET project_phase = 'active_negotiation',
                    expected_delay_days = NULL,
                    delay_reason = NULL
                WHERE project_code = ?
            """, (project_code,))

            print("\n✓ Set to active negotiation (expect responses within 7 days)")

        elif choice == '5':
            # On hold
            reason = input("\nWhy on hold? ").strip()
            resume_date = input("Resume date (YYYY-MM-DD, or leave blank): ").strip()

            self.cursor.execute("""
                UPDATE proposals
                SET on_hold = 1,
                    on_hold_reason = ?,
                    on_hold_until = ?
                WHERE project_code = ?
            """, (reason, resume_date or None, project_code))

            print(f"\n✓ Proposal marked as on hold")

        self.conn.commit()
        print(f"\n✅ Context saved for {project_code}")
        print("   Run proposal_health_monitor.py to see updated health score")

    def run(self):
        """Interactive context setter"""
        print("="*80)
        print("💭 PROPOSAL CONTEXT SETTER")
        print("="*80)

        self.list_proposals()

        print("\n" + "="*80)
        project_code = input("\nEnter project code (or 'q' to quit): ").strip().upper()

        if project_code == 'Q':
            return

        self.set_context(project_code)
        self.conn.close()

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/bensley_master.db"

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        return

    setter = ProposalContextSetter(db_path)
    setter.run()

if __name__ == "__main__":
    main()
