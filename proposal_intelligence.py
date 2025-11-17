#!/usr/bin/env python3
"""
Proposal Intelligence System
Organizes email content into actionable proposal summaries
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime
import json
import os
from openai import OpenAI

class ProposalIntelligence:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Initialize OpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        self.ai_enabled = bool(api_key)
        if self.ai_enabled:
            self.client = OpenAI(api_key=api_key)

    def get_proposal_emails(self, project_code):
        """Get all emails for a proposal with content"""
        self.cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                ec.ai_summary,
                ec.category,
                ec.importance_score,
                ec.entities,
                ec.clean_body
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            JOIN proposals p ON epl.proposal_id = p.proposal_id
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE p.project_code = ?
            ORDER BY e.date ASC
        """, (project_code,))

        return self.cursor.fetchall()

    def get_proposal_info(self, project_code):
        """Get proposal basic info"""
        self.cursor.execute("""
            SELECT *
            FROM proposals
            WHERE project_code = ?
        """, (project_code,))

        return self.cursor.fetchone()

    def build_activity_timeline(self, emails):
        """Build chronological activity timeline"""
        timeline = []

        for email in emails:
            try:
                date = parsedate_to_datetime(email['date'])
                date_str = date.strftime('%Y-%m-%d')
            except:
                date_str = email['date'][:10] if email['date'] else 'Unknown'

            activity = {
                'date': date_str,
                'subject': email['subject'],
                'from': email['sender_email'],
                'category': email['category'] or 'general',
                'importance': email['importance_score'] or 50,
                'summary': email['ai_summary'] or 'No summary',
                'entities': email['entities']
            }
            timeline.append(activity)

        return timeline

    def extract_key_information(self, timeline):
        """Extract key information from timeline"""
        key_info = {
            'contracts': [],
            'meetings': [],
            'budget_discussions': [],
            'design_reviews': [],
            'decisions': [],
            'next_steps': [],
            'blockers': [],
            'key_people': set()
        }

        for activity in timeline:
            category = activity['category']
            summary = activity['summary'].lower()
            entities = activity['entities']

            # Extract key people from entities
            if entities:
                try:
                    entities_dict = json.loads(entities)
                    for person in entities_dict.get('people', []):
                        key_info['key_people'].add(person)
                except:
                    pass

            # Categorize by type
            if category == 'contract':
                key_info['contracts'].append({
                    'date': activity['date'],
                    'summary': activity['summary']
                })

            elif category == 'meeting':
                key_info['meetings'].append({
                    'date': activity['date'],
                    'summary': activity['summary']
                })

            elif category == 'design':
                key_info['design_reviews'].append({
                    'date': activity['date'],
                    'summary': activity['summary']
                })

            # Look for budget/fee discussions
            if any(word in summary for word in ['fee', 'budget', 'cost', 'price', '$', 'usd']):
                key_info['budget_discussions'].append({
                    'date': activity['date'],
                    'summary': activity['summary']
                })

            # Look for decisions
            if any(word in summary for word in ['approved', 'agreed', 'confirmed', 'decided', 'accepted']):
                key_info['decisions'].append({
                    'date': activity['date'],
                    'summary': activity['summary']
                })

            # Look for blockers
            if any(word in summary for word in ['waiting', 'pending', 'delayed', 'issue', 'problem', 'concern']):
                key_info['blockers'].append({
                    'date': activity['date'],
                    'summary': activity['summary']
                })

        key_info['key_people'] = list(key_info['key_people'])
        return key_info

    def generate_ai_summary(self, proposal, timeline, key_info):
        """Generate intelligent summary using AI"""
        if not self.ai_enabled:
            return "AI disabled - enable OPENAI_API_KEY for summaries"

        # Build context for AI
        timeline_text = "\n".join([
            f"{a['date']}: [{a['category']}] {a['summary']}"
            for a in timeline[-20:]  # Last 20 emails
        ])

        prompt = f"""Analyze this proposal's email history and provide a concise status summary.

PROJECT: {proposal['project_name']} ({proposal['project_code']})
STATUS: {proposal['status'] or 'proposal'}

EMAIL HISTORY (chronological):
{timeline_text}

KEY INFORMATION:
- Contracts: {len(key_info['contracts'])}
- Meetings: {len(key_info['meetings'])}
- Budget discussions: {len(key_info['budget_discussions'])}
- Design reviews: {len(key_info['design_reviews'])}

Provide a 3-4 sentence summary covering:
1. Current status and stage
2. Key developments or decisions
3. Next steps or what we're waiting for
4. Any concerns or blockers

Keep it concise and actionable."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert project analyst summarizing proposal status."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def generate_proposal_report(self, project_code):
        """Generate complete proposal intelligence report"""
        # Get proposal info
        proposal = self.get_proposal_info(project_code)
        if not proposal:
            print(f"✗ Proposal {project_code} not found")
            return

        # Get emails
        emails = self.get_proposal_emails(project_code)
        if not emails:
            print(f"✗ No emails found for {project_code}")
            return

        # Build timeline
        timeline = self.build_activity_timeline(emails)

        # Extract key information
        key_info = self.extract_key_information(timeline)

        # Generate AI summary
        ai_summary = self.generate_ai_summary(proposal, timeline, key_info)

        # Display report
        self.display_report(proposal, timeline, key_info, ai_summary)

    def display_report(self, proposal, timeline, key_info, ai_summary):
        """Display formatted intelligence report"""
        print("\n" + "="*80)
        print(f"📊 PROPOSAL INTELLIGENCE REPORT")
        print("="*80)

        # Header
        print(f"\n{proposal['project_code']}: {proposal['project_name']}")
        print(f"Status: {proposal['status'] or 'proposal'}")
        if proposal['is_active_project']:
            print("🎯 ACTIVE PROJECT (contract signed)")

        # AI Summary
        print("\n" + "="*80)
        print("🧠 INTELLIGENT SUMMARY")
        print("="*80)
        print(ai_summary)

        # Health metrics
        if proposal['days_since_contact']:
            print("\n" + "="*80)
            print("📈 HEALTH METRICS")
            print("="*80)
            print(f"  Last contact: {proposal['days_since_contact']} days ago")
            print(f"  Health score: {proposal['health_score']:.0f}%")
            if proposal['last_sentiment']:
                print(f"  Last sentiment: {proposal['last_sentiment'].title()}")

        # Key Information
        print("\n" + "="*80)
        print("🔑 KEY INFORMATION")
        print("="*80)
        print(f"  Total emails: {len(timeline)}")
        print(f"  Contracts: {len(key_info['contracts'])}")
        print(f"  Meetings: {len(key_info['meetings'])}")
        print(f"  Budget discussions: {len(key_info['budget_discussions'])}")
        print(f"  Design reviews: {len(key_info['design_reviews'])}")
        print(f"  Key decisions: {len(key_info['decisions'])}")
        print(f"  Blockers noted: {len(key_info['blockers'])}")

        if key_info['key_people']:
            print(f"\n  Key people: {', '.join(key_info['key_people'][:5])}")

        # Recent contracts
        if key_info['contracts']:
            print("\n📝 CONTRACTS & AGREEMENTS:")
            for contract in key_info['contracts'][-3:]:
                print(f"  • {contract['date']}: {contract['summary'][:70]}")

        # Recent decisions
        if key_info['decisions']:
            print("\n✅ KEY DECISIONS:")
            for decision in key_info['decisions'][-3:]:
                print(f"  • {decision['date']}: {decision['summary'][:70]}")

        # Blockers
        if key_info['blockers']:
            print("\n⚠️  BLOCKERS/WAITING:")
            for blocker in key_info['blockers'][-3:]:
                print(f"  • {blocker['date']}: {blocker['summary'][:70]}")

        # Activity timeline (recent)
        print("\n" + "="*80)
        print("📅 RECENT ACTIVITY (Last 10 emails)")
        print("="*80)
        for activity in timeline[-10:]:
            importance_icon = "⭐" if activity['importance'] > 80 else ""
            category_icon = {
                'contract': '📄',
                'meeting': '📅',
                'design': '🎨',
                'invoice': '💰',
                'rfi': '❓',
                'schedule': '📆',
                'general': '💬'
            }.get(activity['category'], '💬')

            print(f"\n{activity['date']} {category_icon} [{activity['category'].upper()}] {importance_icon}")
            print(f"  {activity['subject'][:70]}")
            print(f"  → {activity['summary'][:100]}")

        print("\n" + "="*80 + "\n")

    def list_proposals_with_emails(self):
        """List all proposals that have email data"""
        self.cursor.execute("""
            SELECT DISTINCT
                p.project_code,
                p.project_name,
                p.days_since_contact,
                COUNT(e.email_id) as email_count
            FROM proposals p
            JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
            JOIN emails e ON epl.email_id = e.email_id
            WHERE p.status IS NULL OR p.status != 'lost'
            GROUP BY p.project_code, p.project_name, p.days_since_contact
            ORDER BY p.days_since_contact ASC
        """)

        proposals = self.cursor.fetchall()

        print("\n" + "="*80)
        print("📋 PROPOSALS WITH EMAIL DATA")
        print("="*80)

        for prop in proposals:
            days = prop['days_since_contact'] or '???'
            print(f"{prop['project_code']}: {prop['project_name'][:50]:50} | {prop['email_count']:3} emails | {days} days")

        print(f"\nTotal: {len(proposals)} proposals")
        print("="*80)

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "database/bensley_master.db"

    if not Path(db_path).exists():
        print(f"✗ Database not found: {db_path}")
        return

    intel = ProposalIntelligence(db_path)

    if len(sys.argv) > 2:
        # Generate report for specific proposal
        project_code = sys.argv[2].upper()
        intel.generate_proposal_report(project_code)
    else:
        # List all proposals
        intel.list_proposals_with_emails()
        print("\nUsage: python3 proposal_intelligence.py <db_path> <project_code>")
        print("Example: python3 proposal_intelligence.py database/bensley_master.db BK-074")

if __name__ == "__main__":
    main()
