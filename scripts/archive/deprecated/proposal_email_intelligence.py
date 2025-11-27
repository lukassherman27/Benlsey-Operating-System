#!/usr/bin/env python3
"""
Proposal Email Intelligence System
Automatically extracts proposal updates, status changes, and context from emails
Uses Claude AI to understand email content and update proposal tracker
"""

import sqlite3
import anthropic
import os
import json
from datetime import datetime, timedelta

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"
API_KEY = os.getenv("ANTHROPIC_API_KEY")

class ProposalEmailIntelligence:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.client = anthropic.Anthropic(api_key=API_KEY)

    def analyze_email_for_proposals(self, email_id=None, days_back=7):
        """
        Analyze emails for proposal-related content and extract intelligence
        """
        if email_id:
            # Analyze specific email
            emails = [self.get_email(email_id)]
        else:
            # Analyze recent emails
            emails = self.get_recent_emails(days_back)

        print(f"Analyzing {len(emails)} emails for proposal intelligence...")

        processed_count = 0
        for email in emails:
            try:
                intelligence = self.extract_proposal_intelligence(email)
                if intelligence:
                    self.save_intelligence(email, intelligence)
                    self.update_proposal_tracker(intelligence)
                    processed_count += 1
            except Exception as e:
                print(f"Error processing email {email['id']}: {e}")
                continue

        self.conn.commit()
        print(f"✓ Processed {processed_count} emails with proposal intelligence")

    def get_email(self, email_id):
        """Get specific email"""
        self.cursor.execute("""
            SELECT id, subject, body, sent_date, sender, recipients
            FROM emails WHERE id = ?
        """, (email_id,))
        return self.cursor.fetchone()

    def get_recent_emails(self, days_back=7):
        """Get recent emails that might contain proposal info"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        self.cursor.execute("""
            SELECT e.id, e.subject, e.body, e.sent_date, e.sender, e.recipients
            FROM emails e
            WHERE e.sent_date >= ?
            AND (
                e.body LIKE '%proposal%'
                OR e.body LIKE '%project%'
                OR e.body LIKE '%25 BK-%'
                OR e.body LIKE '%24 BK-%'
                OR e.body LIKE '%23 BK-%'
                OR e.subject LIKE '%proposal%'
                OR e.subject LIKE '%project%'
            )
            AND e.id NOT IN (SELECT email_id FROM proposal_email_intelligence)
            ORDER BY e.sent_date DESC
            LIMIT 100
        """, (cutoff_date,))

        return self.cursor.fetchall()

    def extract_proposal_intelligence(self, email):
        """
        Use Claude AI to extract proposal-related information from email
        """
        prompt = f"""You are analyzing an email to extract proposal/project information.

EMAIL DETAILS:
Subject: {email['subject']}
Date: {email['sent_date']}
From: {email['sender']}
To: {email['recipients']}

EMAIL BODY:
{email['body'][:3000] if email['body'] else ''}

TASK: Extract the following information and return as JSON:

1. project_codes: List of project codes mentioned (e.g., "25 BK-062", "24 BK-070")
2. status_updates: For each project, what status change occurred? Options:
   - "First Contact" - initial contact made
   - "Drafting" - working on proposal/design
   - "Proposal Sent" - proposal was sent to client
   - "On Hold" - project paused
   - "Contract Signed" - deal won
3. key_information: Important details about the project (scope, timeline, budget, etc.)
4. action_items: What needs to be done next?
5. client_sentiment: Is the client Positive/Neutral/Negative?
6. waiting_on: Who/what are we waiting on?
7. next_steps: What are the next actions?
8. remark: A concise 1-2 sentence summary of the update

Return ONLY valid JSON. If no proposal information found, return empty object {{}}.

Example output:
{{
  "projects": [
    {{
      "project_code": "25 BK-062",
      "status_update": "Proposal Sent",
      "key_information": "Sent final proposal with updated scope and pricing",
      "action_items": ["Follow up next week", "Prepare presentation"],
      "client_sentiment": "Positive",
      "waiting_on": "Client decision",
      "next_steps": "Schedule call to discuss",
      "remark": "Proposal sent to client, positive feedback on initial concept"
    }}
  ]
}}
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse JSON response
            content = response.content[0].text
            # Extract JSON from response
            if "{" in content:
                json_start = content.index("{")
                json_end = content.rindex("}") + 1
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            return {}

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return {}

    def save_intelligence(self, email, intelligence):
        """Save extracted intelligence to database"""
        if not intelligence or 'projects' not in intelligence:
            return

        for project in intelligence['projects']:
            project_code = project.get('project_code')
            if not project_code:
                continue

            self.cursor.execute("""
                INSERT INTO proposal_email_intelligence (
                    email_id, project_code, status_update, key_information,
                    action_items, client_sentiment, email_subject, email_date,
                    email_from, email_to, email_snippet
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                email['id'],
                project_code,
                project.get('status_update'),
                project.get('key_information'),
                json.dumps(project.get('action_items', [])),
                project.get('client_sentiment'),
                email['subject'],
                email['sent_date'],
                email['sender'],
                email['recipients'],
                project.get('remark')
            ))

    def update_proposal_tracker(self, intelligence):
        """Update proposal_tracker table based on extracted intelligence"""
        if not intelligence or 'projects' not in intelligence:
            return

        for project in intelligence['projects']:
            project_code = project.get('project_code')
            if not project_code:
                continue

            # Check if project exists in tracker
            self.cursor.execute("""
                SELECT id, current_status FROM proposal_tracker
                WHERE project_code = ?
            """, (project_code,))

            existing = self.cursor.fetchone()

            if existing:
                # Update existing
                status_update = project.get('status_update')
                remark = project.get('remark')
                waiting_on = project.get('waiting_on')
                next_steps = project.get('next_steps')

                updates = []
                values = []

                if status_update and status_update != existing['current_status']:
                    updates.append("last_week_status = current_status")
                    updates.append("current_status = ?")
                    updates.append("status_changed_date = datetime('now')")
                    values.append(status_update)

                if remark:
                    updates.append("current_remark = ?")
                    values.append(remark)

                if waiting_on:
                    updates.append("waiting_on = ?")
                    values.append(waiting_on)

                if next_steps:
                    updates.append("next_steps = ?")
                    values.append(next_steps)

                updates.append("latest_email_context = ?")
                values.append(project.get('key_information'))

                updates.append("updated_at = datetime('now')")

                if updates:
                    sql = f"UPDATE proposal_tracker SET {', '.join(updates)} WHERE project_code = ?"
                    values.append(project_code)
                    self.cursor.execute(sql, values)

                    print(f"  ✓ Updated {project_code}: {remark}")

    def initialize_from_existing_data(self):
        """
        Initialize proposal_tracker from existing projects data
        """
        print("Initializing proposal tracker from existing data...")

        # Get all active proposal projects
        self.cursor.execute("""
            SELECT
                project_code,
                project_name,
                total_fee_usd,
                country,
                proposal_status,
                created_at
            FROM projects
            WHERE project_category = 'Proposal'
            AND project_code NOT IN (SELECT project_code FROM proposal_tracker)
        """)

        projects = self.cursor.fetchall()

        for proj in projects:
            # Map old status to new status
            status_map = {
                'proposal': 'Proposal Sent',
                'active': 'Drafting',
                'archived': 'Archived',
                'on hold': 'On Hold'
            }

            current_status = status_map.get(
                (proj['proposal_status'] or '').lower(),
                'First Contact'
            )

            self.cursor.execute("""
                INSERT INTO proposal_tracker (
                    project_code, project_name, project_value, country,
                    current_status, first_contact_date, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                proj['project_code'],
                proj['project_name'],
                proj['total_fee_usd'] or 0,
                proj['country'],
                current_status,
                proj['created_at']
            ))

        self.conn.commit()
        print(f"✓ Initialized {len(projects)} proposals in tracker")

    def generate_weekly_report_data(self):
        """
        Generate data for weekly proposal overview report
        Returns list of proposals with all needed fields
        """
        self.cursor.execute("""
            SELECT
                project_code,
                project_name,
                project_value,
                country,
                current_status,
                last_week_status,
                days_in_current_status,
                CASE WHEN proposal_sent = 1 THEN 'Yes' ELSE 'No' END as proposal_sent,
                first_contact_date,
                proposal_sent_date,
                current_remark,
                latest_email_context
            FROM proposal_tracker
            WHERE is_active = 1
            ORDER BY project_code
        """)

        return self.cursor.fetchall()

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    import sys

    intel = ProposalEmailIntelligence()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "init":
            # Initialize from existing data
            intel.initialize_from_existing_data()

        elif command == "analyze":
            # Analyze recent emails
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            intel.analyze_email_for_proposals(days_back=days)

        elif command == "report":
            # Generate weekly report data
            data = intel.generate_weekly_report_data()
            print(f"\n{'='*100}")
            print(f"ACTIVE PROPOSALS: {len(data)}")
            print(f"{'='*100}\n")
            for row in data:
                print(f"{row['project_code']}: {row['project_name']}")
                print(f"  Status: {row['current_status']} ({row['days_in_current_status']} days)")
                if row['current_remark']:
                    print(f"  Remark: {row['current_remark']}")
                print()

    else:
        print("Usage:")
        print("  python3 proposal_email_intelligence.py init     - Initialize from existing data")
        print("  python3 proposal_email_intelligence.py analyze  - Analyze recent emails")
        print("  python3 proposal_email_intelligence.py report   - Show current proposal status")

    intel.close()
