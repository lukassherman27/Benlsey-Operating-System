#!/usr/bin/env python3
"""
Context-Aware Proposal Health Monitor
Intelligent proposal tracking that understands business context
"""
import sqlite3
from pathlib import Path
import sys
from datetime import datetime, timedelta
import json
from email.utils import parsedate_to_datetime

class ProposalHealthMonitor:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def run_migration(self):
        """Apply migration 007 if needed"""
        try:
            migration_path = Path(__file__).parent / "database" / "migrations" / "007_context_aware_health.sql"
            if migration_path.exists():
                with open(migration_path, 'r') as f:
                    migration_sql = f.read()
                    self.conn.executescript(migration_sql)
                    self.conn.commit()
                print("✓ Migration 007 applied")
        except Exception as e:
            pass  # Migration may already be applied

    def calculate_days_since_contact(self, proposal_id):
        """Calculate days since last email for this proposal"""
        self.cursor.execute("""
            SELECT MAX(e.date) as last_email_date
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            WHERE epl.proposal_id = ?
        """, (proposal_id,))

        result = self.cursor.fetchone()
        if result and result['last_email_date']:
            try:
                # Parse email date (RFC 2822 format: "Tue, 4 Nov 2025 11:38:27 +0700")
                last_date_str = result['last_email_date']
                last_date = parsedate_to_datetime(last_date_str)
                days = (datetime.now(last_date.tzinfo) - last_date).days
                return days
            except Exception as e:
                # Fallback: try simple ISO format
                try:
                    last_date = datetime.fromisoformat(last_date_str.split()[0])
                    days = (datetime.now() - last_date).days
                    return days
                except:
                    return None
        return None

    def get_last_email_sentiment(self, proposal_id):
        """Get sentiment of most recent email"""
        self.cursor.execute("""
            SELECT ec.ai_summary, e.subject
            FROM email_content ec
            JOIN emails e ON ec.email_id = e.email_id
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            WHERE epl.proposal_id = ?
            ORDER BY e.date DESC
            LIMIT 1
        """, (proposal_id,))

        result = self.cursor.fetchone()
        if result:
            # Simple sentiment detection from summary
            summary = (result['ai_summary'] or '').lower()
            subject = (result['subject'] or '').lower()
            text = summary + ' ' + subject

            positive_words = ['approved', 'great', 'excellent', 'love', 'perfect', 'yes', 'agreed', 'confirmed']
            negative_words = ['concern', 'issue', 'problem', 'expensive', 'competitor', 'unfortunately']

            if any(word in text for word in positive_words):
                return 'positive'
            elif any(word in text for word in negative_words):
                return 'concerned'

        return 'neutral'

    def calculate_health_score(self, proposal):
        """Calculate context-aware health score"""
        base_score = 100

        # Get days since contact
        days_since = proposal['days_since_contact']
        if days_since is None:
            return 50  # Unknown - middle score

        # Handle expected delays
        expected_delay = proposal['expected_delay_days'] or 0
        if expected_delay > 0:
            if days_since < expected_delay:
                # Still within expected window - minimal penalty
                return 95
            else:
                # Past expected delay - now it's concerning
                days_overdue = days_since - expected_delay
                base_score -= days_overdue * 5

        # Handle on-hold projects
        elif proposal['on_hold']:
            return 90  # On hold but tracked

        # Phase-appropriate expectations
        elif proposal['project_phase'] == 'early_exploration':
            # Slow is normal - penalize after 30 days
            if days_since > 30:
                base_score -= (days_since - 30) * 2

        elif proposal['project_phase'] == 'active_negotiation':
            # Fast expected - penalize after 7 days
            if days_since > 7:
                base_score -= (days_since - 7) * 8

        elif proposal['project_phase'] == 'contract_pending':
            # Very fast expected - penalize after 3 days
            if days_since > 3:
                base_score -= (days_since - 3) * 10

        else:
            # Default: penalize after 10 days
            if days_since > 10:
                base_score -= (days_since - 10) * 5

        # Client pattern adjustment
        if proposal['client_response_pattern'] == 'slow':
            base_score += 15  # Adjust upward
        elif proposal['client_response_pattern'] == 'fast':
            base_score -= 5  # Higher expectations

        # Sentiment adjustment
        if proposal['last_sentiment'] == 'positive':
            base_score += 10
        elif proposal['last_sentiment'] == 'concerned':
            base_score -= 15
        elif proposal['last_sentiment'] == 'negative':
            base_score -= 25

        return max(0, min(100, base_score))

    def update_all_health_scores(self):
        """Update health scores for all proposals"""
        self.cursor.execute("""
            SELECT proposal_id, project_code FROM proposals
            WHERE is_active_project = 0  -- Only proposals, not active projects
              AND (status IS NULL OR status != 'lost')  -- Exclude lost proposals
        """)

        proposals = self.cursor.fetchall()

        for prop in proposals:
            # Calculate days since contact
            days = self.calculate_days_since_contact(prop['proposal_id'])

            # Get sentiment
            sentiment = self.get_last_email_sentiment(prop['proposal_id'])

            # Update proposal
            self.cursor.execute("""
                UPDATE proposals
                SET days_since_contact = ?,
                    last_sentiment = ?
                WHERE proposal_id = ?
            """, (days, sentiment, prop['proposal_id']))

        self.conn.commit()

        # Now recalculate health scores
        self.cursor.execute("""
            SELECT * FROM proposals
            WHERE is_active_project = 0
              AND (status IS NULL OR status != 'lost')  -- Exclude lost proposals
        """)

        all_proposals = self.cursor.fetchall()

        for prop in all_proposals:
            health = self.calculate_health_score(prop)
            self.cursor.execute("""
                UPDATE proposals
                SET health_score = ?
                WHERE proposal_id = ?
            """, (health, prop['proposal_id']))

        self.conn.commit()

    def display_health_report(self):
        """Display comprehensive health report"""
        print("\n" + "="*80)
        print("📊 PROPOSAL HEALTH MONITOR")
        print("="*80)
        print(f"Database: {self.db_path}")
        print(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        # Get all proposals with health scores (exclude lost)
        self.cursor.execute("""
            SELECT *
            FROM proposals
            WHERE is_active_project = 0
              AND (status IS NULL OR status != 'lost')  -- Exclude lost proposals
            ORDER BY
                CASE
                    WHEN on_hold = 1 THEN 4
                    WHEN expected_delay_days IS NOT NULL THEN 3
                    WHEN health_score >= 70 THEN 2
                    WHEN health_score >= 50 THEN 1
                    ELSE 0
                END,
                health_score ASC
        """)

        proposals = self.cursor.fetchall()

        # Group by urgency
        urgent = []
        attention = []
        healthy = []
        expected_delay = []
        on_hold = []
        needs_review = []

        for prop in proposals:
            if prop['on_hold']:
                on_hold.append(prop)
            elif prop['expected_delay_days']:
                expected_delay.append(prop)
            elif prop['days_since_contact'] is None:
                # No contact data - needs manual review
                needs_review.append(prop)
            elif prop['health_score'] and prop['health_score'] < 50:
                urgent.append(prop)
            elif prop['health_score'] and prop['health_score'] < 70:
                attention.append(prop)
            else:
                healthy.append(prop)

        # Display urgent
        if urgent:
            print("🔴 URGENT - ACTION REQUIRED TODAY")
            print("="*80)
            for prop in urgent:
                self.display_proposal(prop, 'urgent')

        # Display needs attention
        if attention:
            print("\n🟡 NEEDS ATTENTION - FOLLOW UP THIS WEEK")
            print("="*80)
            for prop in attention:
                self.display_proposal(prop, 'attention')

        # Display healthy
        if healthy:
            print("\n🟢 HEALTHY - ON TRACK")
            print("="*80)
            for prop in healthy[:10]:  # Show top 10
                self.display_proposal(prop, 'healthy')
            if len(healthy) > 10:
                print(f"\n... and {len(healthy) - 10} more healthy proposals")

        # Display expected delays
        if expected_delay:
            print("\n📅 EXPECTED DELAYS - NO ACTION NEEDED")
            print("="*80)
            for prop in expected_delay:
                self.display_proposal(prop, 'expected_delay')

        # Display on hold
        if on_hold:
            print("\n⏸️  ON HOLD")
            print("="*80)
            for prop in on_hold:
                self.display_proposal(prop, 'on_hold')

        # Display needs manual review
        if needs_review:
            print("\n❓ NEEDS MANUAL REVIEW - NO EMAIL DATA")
            print("="*80)
            print(f"{len(needs_review)} proposals have no email activity.")
            print("These may be:")
            print("  • Recently added proposals")
            print("  • Dead/cancelled proposals (mark as 'lost')")
            print("  • Proposals from Brian's inbox (not yet imported)")
            print("\nRun mark_proposal_status.py to clean up dead proposals")

        # Summary
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"  🔴 Urgent:           {len(urgent)}")
        print(f"  🟡 Needs Attention:  {len(attention)}")
        print(f"  🟢 Healthy:          {len(healthy)}")
        print(f"  📅 Expected Delays:  {len(expected_delay)}")
        print(f"  ⏸️  On Hold:          {len(on_hold)}")
        print(f"  ❓ Needs Review:     {len(needs_review)}")
        print(f"  📊 Total Proposals:  {len(proposals)}")
        print("="*80 + "\n")

    def display_proposal(self, prop, status_type):
        """Display single proposal with context"""
        health = prop['health_score'] or 50
        health_icon = "🔴" if health < 50 else "🟡" if health < 70 else "🟢"

        print(f"\n{prop['project_code']}: {prop['project_name'][:55]}")
        print(f"  Health: {health_icon} {health:.0f}%")

        if prop['days_since_contact'] is not None:
            print(f"  Last contact: {prop['days_since_contact']} days ago")

        if status_type == 'expected_delay':
            print(f"  Expected delay: {prop['expected_delay_days']} days")
            if prop['delay_reason']:
                print(f"  Reason: {prop['delay_reason']}")
            if prop['delay_until_date']:
                print(f"  Check back: {prop['delay_until_date']}")

        elif status_type == 'on_hold':
            if prop['on_hold_reason']:
                print(f"  Reason: {prop['on_hold_reason']}")
            if prop['on_hold_until']:
                print(f"  Resume: {prop['on_hold_until']}")

        else:
            if prop['project_phase']:
                print(f"  Phase: {prop['project_phase'].replace('_', ' ').title()}")

            if prop['last_sentiment']:
                sentiment_emoji = {'positive': '😊', 'neutral': '😐', 'concerned': '😟', 'negative': '😞'}
                print(f"  Sentiment: {sentiment_emoji.get(prop['last_sentiment'], '😐')} {prop['last_sentiment'].title()}")

            # Suggest action
            if status_type == 'urgent':
                print(f"  Action: 🚨 CALL OR EMAIL TODAY")
            elif status_type == 'attention':
                print(f"  Action: ⚠️  Follow up this week")

            if prop['next_action']:
                print(f"  Next: {prop['next_action']}")

    def run(self):
        """Run health monitor"""
        self.run_migration()
        print("\n🔄 Calculating health scores...")
        self.update_all_health_scores()
        print("✓ Health scores updated\n")
        self.display_health_report()
        self.conn.close()

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/bensley_master.db"

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        return

    monitor = ProposalHealthMonitor(db_path)
    monitor.run()

if __name__ == "__main__":
    main()
