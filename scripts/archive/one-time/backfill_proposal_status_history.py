#!/usr/bin/env python3
"""
Proposal Status History Backfill - Task 1.3
Infer status changes from proposal dates and create historical records
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv('DATABASE_PATH', 'database/bensley_master.db')

class StatusHistoryBackfill:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def get_proposals(self):
        """Get all proposals with their key dates and current status"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                proposal_id, project_code, project_name,
                first_contact_date, proposal_sent_date, contract_signed_date,
                current_status, last_status_change, created_at
            FROM proposals
            ORDER BY project_code
        """)
        return cursor.fetchall()

    def infer_status_changes(self, proposal):
        """Infer historical status changes from dates"""
        changes = []

        # First Contact
        if proposal['first_contact_date']:
            changes.append({
                'date': proposal['first_contact_date'],
                'old_status': None,
                'new_status': 'First Contact',
                'source': 'inferred',
                'notes': 'Inferred from first_contact_date'
            })

        # Proposal Sent
        if proposal['proposal_sent_date']:
            changes.append({
                'date': proposal['proposal_sent_date'],
                'old_status': 'First Contact',
                'new_status': 'Proposal Sent',
                'source': 'inferred',
                'notes': 'Inferred from proposal_sent_date'
            })

        # Contract Signed
        if proposal['contract_signed_date']:
            changes.append({
                'date': proposal['contract_signed_date'],
                'old_status': 'Proposal Sent',
                'new_status': 'Contract Signed',
                'source': 'inferred',
                'notes': 'Inferred from contract_signed_date'
            })

        # Current Status (if different from last inferred)
        current_status = proposal['current_status']
        if current_status:
            last_inferred = changes[-1]['new_status'] if changes else None

            if current_status != last_inferred:
                # Use last_status_change if available, otherwise use created_at
                change_date = proposal['last_status_change'] or proposal['created_at'] or datetime.now().isoformat()

                changes.append({
                    'date': change_date,
                    'old_status': last_inferred,
                    'new_status': current_status,
                    'source': 'current',
                    'notes': 'Current status from proposals table'
                })

        return changes

    def save_history(self, proposal, changes):
        """Save status changes to proposal_status_history"""
        cursor = self.conn.cursor()

        for change in changes:
            try:
                cursor.execute("""
                    INSERT INTO proposal_status_history (
                        proposal_id, project_code, old_status, new_status,
                        status_date, changed_by, notes, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proposal['proposal_id'],
                    proposal['project_code'],
                    change['old_status'],
                    change['new_status'],
                    change['date'],
                    'backfill_script',
                    change['notes'],
                    change['source']
                ))
            except Exception as e:
                print(f"  Error saving change for {proposal['project_code']}: {e}")

        self.conn.commit()

    def get_stats(self):
        """Get status history statistics"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM proposal_status_history")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT proposal_id) FROM proposal_status_history")
        proposals_with_history = cursor.fetchone()[0]

        cursor.execute("""
            SELECT new_status, COUNT(*) as cnt
            FROM proposal_status_history
            GROUP BY new_status
            ORDER BY cnt DESC
        """)
        by_status = cursor.fetchall()

        return {
            'total_records': total,
            'proposals_with_history': proposals_with_history,
            'by_status': [(r['new_status'], r['cnt']) for r in by_status]
        }

    def run(self, clear_existing=True):
        """Backfill all proposal status history"""
        print("=" * 60)
        print("PROPOSAL STATUS HISTORY BACKFILL - Task 1.3")
        print("=" * 60)

        cursor = self.conn.cursor()

        if clear_existing:
            cursor.execute("DELETE FROM proposal_status_history WHERE source IN ('inferred', 'current', 'backfill_script')")
            self.conn.commit()
            print("🗑️  Cleared existing backfill records")

        proposals = self.get_proposals()
        print(f"\n📊 Processing {len(proposals)} proposals...")

        total_changes = 0
        proposals_updated = 0

        for proposal in proposals:
            changes = self.infer_status_changes(proposal)

            if changes:
                self.save_history(proposal, changes)
                total_changes += len(changes)
                proposals_updated += 1

                # Show progress for proposals with multiple changes
                if len(changes) >= 2:
                    print(f"  ✓ {proposal['project_code']}: {len(changes)} status changes")

        # Get final stats
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("✅ STATUS HISTORY BACKFILL COMPLETE")
        print("=" * 60)
        print(f"Total history records: {stats['total_records']}")
        print(f"Proposals with history: {stats['proposals_with_history']}")

        print("\n📊 Records by status:")
        for status, count in stats['by_status']:
            print(f"   {status}: {count}")

        # Show sample timeline
        cursor.execute("""
            SELECT p.project_code, psh.old_status, psh.new_status, psh.status_date
            FROM proposal_status_history psh
            JOIN proposals p ON psh.proposal_id = p.proposal_id
            WHERE psh.source != 'manual'
            ORDER BY psh.proposal_id, psh.status_date
            LIMIT 20
        """)

        print("\n📋 Sample status transitions:")
        current_project = None
        for row in cursor.fetchall():
            if row['project_code'] != current_project:
                current_project = row['project_code']
                print(f"\n  {current_project}:")
            old = row['old_status'] or '(new)'
            print(f"    {old} → {row['new_status']} ({row['status_date'][:10] if row['status_date'] else 'unknown'})")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Backfill proposal status history')
    parser.add_argument('--no-clear', action='store_true', help="Don't clear existing backfill records")
    args = parser.parse_args()

    backfill = StatusHistoryBackfill()
    backfill.run(clear_existing=not args.no_clear)
