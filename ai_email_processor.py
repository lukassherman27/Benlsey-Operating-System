#!/usr/bin/env python3
"""
GENERAL AI EMAIL PROCESSOR

Not rigid rules. AI reads email with FULL CONTEXT and decides what to do.

Flow:
1. Email arrives
2. Check: Who sent it? Are they linked to a project?
3. Load FULL project context (all data, past emails, contracts, etc.)
4. AI reads email naturally: "What are they saying? What needs to happen?"
5. AI decides what to update in database
6. Auto-update or create suggestion

AI can handle ANYTHING:
- RFI? → Create RFI entry
- Fee changed? → Update project_value
- New contact? → Add to contacts
- Question about contract? → Reference contract document
- Status update? → Update project status
- Whatever else the email is about
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


class AIEmailProcessor:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY required")

        self.client = OpenAI(api_key=api_key)

    def process_email(self, email_id: int):
        """Process an email with full context and AI understanding"""

        # Get email
        email = self._get_email(email_id)
        if not email:
            return None

        print(f"\n📧 Processing: {email['subject'][:60]}...")
        print(f"   From: {email['sender_email']}")

        # STEP 1: Get context - who is this person? what projects are they on?
        context = self._get_full_context(email)

        if not context['projects']:
            print(f"   ℹ️  Sender not linked to any projects - categorizing only")
            # Just categorize the email
            category = self._categorize_email(email)
            self._update_email_category(email_id, category)
            return

        print(f"   📊 Found {len(context['projects'])} related project(s)")

        # STEP 2: Let AI read the email with FULL CONTEXT and decide what to do
        ai_decision = self._analyze_with_context(email, context)

        if not ai_decision:
            print(f"   ✅ No action needed")
            return

        # STEP 3: Apply AI's decisions
        self._apply_ai_decisions(email_id, ai_decision, context)

    def _get_email(self, email_id: int) -> Optional[Dict]:
        """Get email from database"""
        self.cursor.execute("SELECT * FROM emails WHERE email_id = ?", (email_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def _get_full_context(self, email: Dict) -> Dict:
        """Get FULL context about sender and related projects"""

        sender = email['sender_email']

        # Find projects this sender is associated with
        # Check multiple ways: sender email, client company domain, etc.
        self.cursor.execute("""
            SELECT DISTINCT p.*
            FROM projects p
            LEFT JOIN email_project_links epl ON p.project_code = epl.project_code
            LEFT JOIN emails e ON epl.email_id = e.email_id
            WHERE e.sender_email = ?
               OR p.contact_email = ?
               OR p.client_company LIKE '%' || SUBSTR(?, INSTR(?, '@') + 1) || '%'
            LIMIT 5
        """, (sender, sender, sender, sender))

        projects = [dict(row) for row in self.cursor.fetchall()]

        # Get past email history with this sender
        self.cursor.execute("""
            SELECT subject, date, snippet, category
            FROM emails
            WHERE sender_email = ?
            ORDER BY date DESC
            LIMIT 10
        """, (sender,))

        past_emails = [dict(row) for row in self.cursor.fetchall()]

        # If we found projects, get additional context
        rfis = []
        contracts = []

        if projects:
            project_codes = [p['project_code'] for p in projects]

            # Get any RFIs for these projects
            self.cursor.execute(f"""
                SELECT * FROM rfis
                WHERE project_code IN ({','.join('?' * len(project_codes))})
            """, project_codes)
            rfis = [dict(row) for row in self.cursor.fetchall()]

        return {
            'sender': sender,
            'projects': projects,
            'past_emails': past_emails,
            'rfis': rfis,
            'contracts': contracts
        }

    def _analyze_with_context(self, email: Dict, context: Dict) -> Optional[Dict]:
        """
        Let AI read the email with FULL CONTEXT and decide what needs to happen.

        AI is not looking for specific keywords. It's understanding the email naturally.
        """

        # Build context for AI
        context_text = self._build_context_text(email, context)

        prompt = f"""You are an AI assistant managing a design firm's business operations.

CONTEXT:
{context_text}

NEW EMAIL:
Subject: {email['subject']}
From: {email['sender_email']}
Date: {email['date']}
Body:
{email['body_full'] or email['snippet'] or 'No content'}

YOUR JOB:
Read this email naturally and understand what it means in the context of the business.
Then decide what needs to happen in the database.

THINK ABOUT:
- Is this an RFI (request for information)? → Create RFI entry
- Did anything change? (fee, scope, timeline, status) → Update project
- Are they asking a question? → Reference contracts/documents and answer
- Is this a new inquiry? → Create new project/proposal
- Status update? → Update project status
- New contact person? → Update contacts
- Payment received? → Update financials
- Any other database action needed?

Respond in JSON:
{{
    "understanding": "Brief summary of what this email is about",
    "actions_needed": [
        {{
            "type": "create_rfi|update_project|create_project|update_contact|answer_question|categorize|other",
            "table": "rfis|projects|contacts|emails|etc",
            "data": {{
                // The actual data to insert/update
                // Be flexible - include whatever fields make sense
            }},
            "reasoning": "Why this action is needed",
            "confidence": 85
        }}
    ],
    "category": "RFI|Proposal|Contract|Financial|General|etc",
    "needs_human_review": true/false,
    "priority": "high|medium|low"
}}

If no action needed, return empty actions_needed array.
Be FLEXIBLE - handle whatever the email is about, don't just look for specific patterns.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a business operations AI that understands emails in context and decides what database updates are needed."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            decision = json.loads(response.choices[0].message.content)
            return decision

        except Exception as e:
            print(f"   ⚠️  AI analysis failed: {e}")
            return None

    def _build_context_text(self, email: Dict, context: Dict) -> str:
        """Build context summary for AI"""

        text = ""

        if context['projects']:
            text += "RELATED PROJECTS:\n"
            for p in context['projects']:
                text += f"  • {p['project_code']}: {p['project_name'] or 'N/A'}\n"
                text += f"    Client: {p['client_company'] or 'N/A'}\n"
                text += f"    Status: {p['status'] or 'N/A'}\n"
                text += f"    Value: ${p['project_value'] or 0:,.0f}\n"
                text += f"    Last contact: {p['days_since_contact'] or 'N/A'} days ago\n"

        if context['past_emails']:
            text += "\nPAST EMAIL HISTORY WITH SENDER:\n"
            for e in context['past_emails'][:5]:
                text += f"  • {e['date']}: {e['subject']}\n"
                text += f"    Category: {e['category'] or 'Uncategorized'}\n"

        if context['rfis']:
            text += "\nEXISTING RFIs:\n"
            for r in context['rfis']:
                text += f"  • {r['rfi_subject'] or 'N/A'} (Status: {r['status'] or 'N/A'})\n"

        return text

    def _apply_ai_decisions(self, email_id: int, decision: Dict, context: Dict):
        """Apply AI's decisions to the database"""

        print(f"   🤖 AI Understanding: {decision['understanding']}")

        if not decision.get('actions_needed'):
            # Just update category
            if decision.get('category'):
                self._update_email_category(email_id, decision['category'])
            return

        print(f"   📝 Actions needed: {len(decision['actions_needed'])}")

        for action in decision['actions_needed']:
            print(f"      • {action['type']}: {action['reasoning']}")

            if action['confidence'] < 70 or decision.get('needs_human_review'):
                # Create suggestion for human review
                self._create_suggestion(email_id, action, context)
            else:
                # Auto-apply if high confidence
                self._auto_apply_action(email_id, action, context)

    def _auto_apply_action(self, email_id: int, action: Dict, context: Dict):
        """Auto-apply high-confidence actions"""

        action_type = action['type']
        data = action['data']

        if action_type == 'create_rfi':
            # Create RFI entry
            project_code = data.get('project_code') or (context['projects'][0]['project_code'] if context['projects'] else None)

            if project_code:
                self.cursor.execute("""
                    INSERT INTO rfis (
                        project_code, rfi_subject, rfi_description,
                        received_date, status
                    ) VALUES (?, ?, ?, ?, 'pending')
                """, (
                    project_code,
                    data.get('subject', 'RFI from email'),
                    data.get('description', ''),
                    datetime.now().strftime('%Y-%m-%d')
                ))
                print(f"         ✅ Created RFI for {project_code}")

        elif action_type == 'update_project':
            # Update project data
            project_code = data.get('project_code') or (context['projects'][0]['project_code'] if context['projects'] else None)

            if project_code:
                # Build UPDATE query dynamically based on what fields AI provided
                updates = []
                values = []

                for key, value in data.items():
                    if key != 'project_code':
                        updates.append(f"{key} = ?")
                        values.append(value)

                if updates:
                    values.append(project_code)
                    query = f"UPDATE projects SET {', '.join(updates)} WHERE project_code = ?"
                    self.cursor.execute(query, values)
                    print(f"         ✅ Updated project {project_code}")

        elif action_type == 'categorize':
            self._update_email_category(email_id, data.get('category', 'General'))

        # Add more action types as needed...

        self.conn.commit()

    def _create_suggestion(self, email_id: int, action: Dict, context: Dict):
        """Create suggestion for human review"""
        import uuid

        suggestion_id = str(uuid.uuid4())
        project_code = context['projects'][0]['project_code'] if context['projects'] else 'SYSTEM'

        self.cursor.execute("""
            INSERT INTO ai_suggestions_queue (
                id, project_code, suggestion_type, proposed_fix, evidence,
                confidence, impact_type, impact_summary,
                severity, bucket, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (
            suggestion_id,
            project_code,
            action['type'],
            json.dumps(action),
            json.dumps({'email_id': email_id}),
            action['confidence'] / 100.0,
            'data_quality',
            action['reasoning'],
            'medium',
            'needs_attention'
        ))

        self.conn.commit()
        print(f"         💡 Created suggestion for review")

    def _update_email_category(self, email_id: int, category: str):
        """Update email category"""
        self.cursor.execute("""
            UPDATE emails SET category = ? WHERE email_id = ?
        """, (category, email_id))
        self.conn.commit()

    def _categorize_email(self, email: Dict) -> str:
        """Simple categorization for emails with no project context"""
        # Quick GPT call just to categorize
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cheaper model for simple task
                messages=[
                    {"role": "system", "content": "Categorize this email in one word: RFI, Proposal, Contract, Financial, Legal, General, Spam"},
                    {"role": "user", "content": f"Subject: {email['subject']}\n\nBody: {email['snippet'] or 'No content'}"}
                ],
                temperature=0.1,
                max_tokens=10
            )

            category = response.choices[0].message.content.strip()
            return category
        except:
            return "General"

    def process_recent_emails(self, limit=50):
        """Process recent emails"""
        print("=" * 80)
        print("🤖 AI EMAIL PROCESSOR - GENERAL INTELLIGENCE")
        print("=" * 80)
        print("\nReading emails with full context and deciding what to do...\n")

        # Get recent emails (last 30 days, not yet categorized)
        self.cursor.execute("""
            SELECT email_id, subject, sender_email, date
            FROM emails
            WHERE (category IS NULL OR category = 'general')
            AND date > date('now', '-30 days')
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))

        emails = self.cursor.fetchall()
        print(f"Processing {len(emails)} emails...\n")

        for i, email in enumerate(emails, 1):
            print(f"[{i}/{len(emails)}]", end=" ")
            self.process_email(email['email_id'])

        print("\n" + "=" * 80)
        print("✅ COMPLETE")
        print("=" * 80)

    def close(self):
        self.conn.close()


def main():
    print("🤖 GENERAL AI EMAIL PROCESSOR")
    print("Not rigid rules - AI understands context and decides what to do\n")

    processor = AIEmailProcessor()

    try:
        processor.process_recent_emails(limit=3)  # Test with just 3 first
    finally:
        processor.close()


if __name__ == "__main__":
    main()
