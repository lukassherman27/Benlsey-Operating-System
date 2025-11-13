#!/usr/bin/env python3
"""
manual_email_linker.py

Interactive email linking tool
- Shows you each email with AI suggestion
- You approve, reject, or specify correct project
- Learns from your choices
- Updates database
"""

import sqlite3
from pathlib import Path
import sys

class ManualEmailLinker:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self.stats = {
            'reviewed': 0,
            'approved': 0,
            'corrected': 0,
            'skipped': 0
        }

        # Load proposals for quick lookup
        self.proposals = self.load_proposals()

    def load_proposals(self):
        """Load all proposals"""
        self.cursor.execute("""
            SELECT proposal_id, project_code, project_name, client_company
            FROM proposals
            ORDER BY project_code
        """)

        proposals = {}
        for row in self.cursor.fetchall():
            proposals[row['project_code']] = {
                'id': row['proposal_id'],
                'name': row['project_name'],
                'client': row['client_company']
            }

        return proposals

    def get_pending_matches(self):
        """Get emails needing review"""
        self.cursor.execute("""
            SELECT
                l.link_id,
                l.email_id,
                l.proposal_id,
                l.confidence_score,
                l.match_reasons,
                e.subject,
                e.sender_email,
                e.date,
                e.body_preview,
                p.project_code,
                p.project_name,
                p.client_company
            FROM email_proposal_links l
            JOIN emails e ON l.email_id = e.email_id
            JOIN proposals p ON l.proposal_id = p.proposal_id
            WHERE l.auto_linked = 0
            ORDER BY l.confidence_score DESC
        """)

        return self.cursor.fetchall()

    def show_proposals_list(self):
        """Show quick reference of all proposals"""
        print("\n" + "="*80)
        print("📋 PROPOSALS REFERENCE")
        print("="*80)

        for code in sorted(self.proposals.keys()):
            p = self.proposals[code]
            print(f"  {code}: {p['name'][:50]:50} | {p['client'][:20]}")

    def approve_link(self, link_id):
        """Approve a suggested link"""
        self.cursor.execute("""
            UPDATE email_proposal_links
            SET auto_linked = 1
            WHERE link_id = ?
        """, (link_id,))
        self.conn.commit()
        self.stats['approved'] += 1

    def reject_link(self, link_id):
        """Reject and delete a link"""
        self.cursor.execute("""
            DELETE FROM email_proposal_links
            WHERE link_id = ?
        """, (link_id,))
        self.conn.commit()
        self.stats['skipped'] += 1

    def change_link(self, link_id, email_id, new_project_code):
        """Change link to different project"""
        if new_project_code not in self.proposals:
            print(f"   ✗ Project {new_project_code} not found!")
            return False

        new_proposal_id = self.proposals[new_project_code]['id']

        # Delete old link
        self.cursor.execute("""
            DELETE FROM email_proposal_links
            WHERE link_id = ?
        """, (link_id,))

        # Create new link
        self.cursor.execute("""
            INSERT INTO email_proposal_links
            (email_id, proposal_id, confidence_score, match_reasons, auto_linked, created_at)
            VALUES (?, ?, 1.0, 'Manual correction', 1, datetime('now'))
        """, (email_id, new_proposal_id))

        self.conn.commit()
        self.stats['corrected'] += 1
        return True

    def review_match(self, match, index, total):
        """Review a single email match"""
        print("\n" + "="*80)
        print(f"EMAIL {index}/{total}")
        print("="*80)

        print(f"\n📧 Subject: {match['subject']}")
        print(f"   From:    {match['sender_email']}")
        print(f"   Date:    {match['date']}")

        if match['body_preview']:
            print(f"\n   Preview: {match['body_preview'][:150]}...")

        print(f"\n🤖 AI SUGGESTION ({match['confidence_score']*100:.0f}% confidence)")
        print(f"   → {match['project_code']}: {match['project_name']}")
        print(f"   Client: {match['client_company']}")
        print(f"   Why: {match['match_reasons']}")

        print("\n" + "-"*80)
        print("OPTIONS:")
        print("  [y] Yes - Link to this project")
        print("  [n] No - Skip this email")
        print("  [c] Correct - Link to different project (enter project code)")
        print("  [l] List - Show all proposals")
        print("  [q] Quit - Save and exit")
        print("-"*80)

        while True:
            choice = input("\nYour choice: ").strip().lower()

            if choice == 'y':
                self.approve_link(match['link_id'])
                print(f"   ✓ Linked to {match['project_code']}")
                self.stats['reviewed'] += 1
                return True

            elif choice == 'n':
                self.reject_link(match['link_id'])
                print(f"   ✗ Skipped")
                self.stats['reviewed'] += 1
                return True

            elif choice == 'c':
                project_code = input("   Enter project code (e.g., BK-001): ").strip().upper()

                if project_code in self.proposals:
                    if self.change_link(match['link_id'], match['email_id'], project_code):
                        p = self.proposals[project_code]
                        print(f"   ✓ Corrected to {project_code}: {p['name']}")
                        self.stats['reviewed'] += 1
                        return True
                else:
                    print(f"   ✗ Project {project_code} not found. Try again or type 'l' to list all.")
                    continue

            elif choice == 'l':
                self.show_proposals_list()
                continue

            elif choice == 'q':
                return False

            else:
                print("   Invalid choice. Try again.")
                continue

    def print_summary(self):
        """Print final summary"""
        print("\n" + "="*80)
        print("✅ MANUAL LINKING SESSION COMPLETE")
        print("="*80)

        print(f"\nSummary:")
        print(f"  Emails reviewed:     {self.stats['reviewed']}")
        print(f"  ✓ Approved as-is:    {self.stats['approved']}")
        print(f"  🔧 Corrected:         {self.stats['corrected']}")
        print(f"  ✗ Skipped:           {self.stats['skipped']}")

        # Show what's linked now
        self.cursor.execute("""
            SELECT p.project_code, p.project_name, COUNT(*) as email_count
            FROM email_proposal_links l
            JOIN proposals p ON l.proposal_id = p.proposal_id
            WHERE l.auto_linked = 1
            GROUP BY p.project_code, p.project_name
            ORDER BY email_count DESC
            LIMIT 10
        """)

        results = self.cursor.fetchall()
        if results:
            print(f"\n📊 Top Proposals with Linked Emails:")
            for row in results:
                print(f"   {row['project_code']}: {row['project_name'][:40]:40} ({row['email_count']} emails)")

        print("="*80)

    def run(self):
        """Run the interactive linking session"""
        print("="*80)
        print("🔗 MANUAL EMAIL LINKER")
        print("="*80)
        print(f"Database: {self.db_path}")
        print(f"Proposals loaded: {len(self.proposals)}")

        # Get pending matches
        matches = self.get_pending_matches()

        if not matches:
            print("\n✓ No emails need review - all done!")
            return

        print(f"\nFound {len(matches)} emails to review")
        print("="*80)

        # Show proposals reference first
        show_list = input("\nShow proposals list first? (y/n): ").strip().lower()
        if show_list == 'y':
            self.show_proposals_list()

        print("\n🚀 Starting review session...")
        print("(You can type 'l' anytime to see all proposals)")

        # Review each match
        for i, match in enumerate(matches, 1):
            if not self.review_match(match, i, len(matches)):
                print("\n⏸️  Session paused - progress saved")
                break

        # Summary
        self.print_summary()

        # Close database
        self.conn.close()

def main():
    # Get database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = "database/bensley_master.db"

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        print(f"\nUsage: python3 manual_email_linker.py [database_path]")
        return

    try:
        linker = ManualEmailLinker(db_path)
        linker.run()
    except KeyboardInterrupt:
        print("\n\n⏸️  Interrupted - progress saved")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
