#!/usr/bin/env python3
"""
SMART EMAIL SYSTEM - Two-Layer Architecture

LAYER 1 (Fast, Free): Database lookups for context
- Who sent this? → Check contacts
- What projects are they on? → Get project context
- Cost: $0, Speed: <0.1s

LAYER 2 (Smart, Focused): AI reads email content with context
- AI already knows WHO and WHAT PROJECT
- AI focuses on understanding WHAT THEY'RE SAYING
- AI decides what actions to take
- Cost: ~$0.01-0.02 per email (only analyzing content, not context)

TWO GOALS:
1. Make database more robust - AI suggests schema improvements
2. Learning system - Eventually runs on auto-pilot
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from openai import OpenAI

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


class SmartEmailSystem:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY required")

        self.client = OpenAI(api_key=api_key)

    def process_email(self, email_id: int):
        """Two-layer processing: Fast context lookup → Focused AI analysis"""

        email = self._get_email(email_id)
        if not email:
            return None

        print(f"\n📧 {email['subject'][:60]}...")
        print(f"   From: {email['sender_email']}")

        # ============================================================
        # LAYER 1: FAST CONTEXT LOOKUP (No AI, just database queries)
        # ============================================================
        context = self._get_context_fast(email)

        if context['contact']:
            print(f"   👤 Known contact: {context['contact']['name']}")

        if context['projects']:
            print(f"   📊 Projects: {', '.join([p['project_code'] for p in context['projects']])}")
        else:
            print(f"   ℹ️  No project links - categorizing only")

        # ============================================================
        # LAYER 2: AI ANALYSIS (Focused on content, not context)
        # ============================================================
        ai_analysis = self._analyze_content_with_ai(email, context)

        if not ai_analysis:
            return None

        # Apply or suggest actions
        self._handle_ai_analysis(email_id, ai_analysis, context)

    def _get_email(self, email_id: int) -> Optional[Dict]:
        """Get email from database"""
        self.cursor.execute("SELECT * FROM emails WHERE email_id = ?", (email_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def _get_context_fast(self, email: Dict) -> Dict:
        """
        LAYER 1: Fast context lookup (no AI)

        Check:
        1. Is sender in contacts database?
        2. What projects are they linked to?
        3. Past email history
        4. Any existing RFIs, contracts, etc.

        This is FAST and FREE - just database queries
        """

        sender = email['sender_email']
        context = {
            'contact': None,
            'projects': [],
            'past_emails': [],
            'rfis': [],
            'contracts': []
        }

        # Check if we have this contact
        # Note: contacts table might not exist yet, we'll create it later
        try:
            self.cursor.execute("""
                SELECT * FROM contacts WHERE email = ?
            """, (sender,))
            contact_row = self.cursor.fetchone()
            if contact_row:
                context['contact'] = dict(contact_row)
        except:
            # Contacts table doesn't exist yet
            pass

        # Find projects via multiple methods:
        # 1. Direct email_project_links
        # 2. Sender matches project contact_email
        # 3. Sender domain matches client company domain

        self.cursor.execute("""
            SELECT DISTINCT p.*
            FROM projects p
            LEFT JOIN email_project_links epl ON p.project_code = epl.project_code
            LEFT JOIN emails e ON epl.email_id = e.email_id
            WHERE e.sender_email = ?
               OR p.contact_email = ?
            LIMIT 5
        """, (sender, sender))

        context['projects'] = [dict(row) for row in self.cursor.fetchall()]

        # Get past emails from this sender
        self.cursor.execute("""
            SELECT subject, date, category
            FROM emails
            WHERE sender_email = ?
            ORDER BY date DESC
            LIMIT 5
        """, (sender,))

        context['past_emails'] = [dict(row) for row in self.cursor.fetchall()]

        # If we found projects, get related data
        if context['projects']:
            project_codes = [p['project_code'] for p in context['projects']]

            # Get RFIs for these projects
            try:
                placeholders = ','.join('?' * len(project_codes))
                self.cursor.execute(f"""
                    SELECT * FROM rfis
                    WHERE project_code IN ({placeholders})
                    ORDER BY received_date DESC
                    LIMIT 10
                """, project_codes)
                context['rfis'] = [dict(row) for row in self.cursor.fetchall()]
            except:
                pass  # RFIs table might not exist

        return context

    def _analyze_content_with_ai(self, email: Dict, context: Dict) -> Optional[Dict]:
        """
        LAYER 2: AI analyzes email CONTENT with context

        AI doesn't waste time figuring out WHO or WHAT PROJECT.
        It focuses on understanding WHAT THEY'RE SAYING and WHAT TO DO.
        """

        # Build concise context summary
        context_summary = ""

        if context['projects']:
            context_summary += "RELATED PROJECTS:\n"
            for p in context['projects']:
                context_summary += f"  • {p['project_code']}: {p['project_name'] or 'N/A'}\n"
                context_summary += f"    Status: {p['status']}, Value: ${p.get('project_value', 0):,.0f}\n"

        if context['past_emails']:
            context_summary += "\nRECENT EMAILS FROM SENDER:\n"
            for e in context['past_emails'][:3]:
                context_summary += f"  • {e['date']}: {e['subject']} ({e['category'] or 'Uncategorized'})\n"

        if context['rfis']:
            context_summary += "\nEXISTING RFIs:\n"
            for r in context['rfis'][:3]:
                context_summary += f"  • {r.get('rfi_subject', 'N/A')} (Status: {r.get('status', 'N/A')})\n"

        prompt = f"""You are analyzing an email for a design firm's business operations.

CONTEXT (you already know this, don't analyze it):
{context_summary if context_summary else "No prior context - new sender"}

NEW EMAIL:
Subject: {email['subject']}
Body: {email['body_full'] or email['snippet'] or 'No content'}

YOUR JOB:
Focus on understanding WHAT THIS EMAIL IS SAYING and what needs to happen.

Ask yourself:
1. What is the sender communicating?
2. What database actions are needed?
3. Does current database structure handle this well?

IMPORTANT - What is an RFI:
- RFI = Request for Information during CONSTRUCTION phase
- Only for ACTIVE projects (in construction/build phase)
- Official request from contractor/client about design clarification
- Example: "How should we detail this wall junction?" "What material for this fixture?"
- NOT an RFI: General questions, proposal inquiries, meeting requests, reviews

RESPOND IN JSON:
{{
    "understanding": "Brief summary of email content",
    "email_type": "Construction RFI|Status Update|Proposal Inquiry|Meeting Request|Contract|Payment|General Question|Other",
    "actions": [
        {{
            "action_type": "create_construction_rfi|update_project|categorize|create_contact|log_inquiry|suggest_schema|none",
            "target_table": "rfis|projects|emails|contacts|inquiries|new_table_suggestion",
            "data": {{
                // Data to insert/update
            }},
            "reasoning": "Why this action",
            "confidence": 85
        }}
    ],
    "schema_thoughts": {{
        "fits_well": true/false,
        "suggestion": "If current schema doesn't fit well, suggest improvement",
        "new_table": "If suggesting new table, describe it",
        "reasoning": "Why current structure doesn't work"
    }},
    "category": "RFI|Proposal|Contract|Legal|Financial|General|etc",
    "priority": "high|medium|low"
}}

Be FLEXIBLE. Handle whatever the email is about.
If current database doesn't fit well, suggest improvements.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You analyze email content and decide database actions. You suggest schema improvements when needed."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)
            return analysis

        except Exception as e:
            print(f"   ⚠️  AI analysis failed: {e}")
            return None

    def _handle_ai_analysis(self, email_id: int, analysis: Dict, context: Dict):
        """Handle AI's analysis - apply or create suggestions"""

        print(f"   🤖 {analysis['understanding']}")
        print(f"   📁 Type: {analysis['email_type']}")

        # Check if schema suggestion
        if not analysis['schema_thoughts']['fits_well']:
            print(f"   💡 Schema improvement suggested:")
            print(f"      {analysis['schema_thoughts']['suggestion']}")
            self._create_schema_suggestion(analysis['schema_thoughts'])

        # Handle actions
        for action in analysis.get('actions', []):
            confidence = action.get('confidence', 50)

            if confidence >= 80:
                # Auto-apply high confidence
                print(f"   ✅ Auto-applying: {action['action_type']}")
                self._apply_action(email_id, action, context)
            else:
                # Create suggestion for review
                print(f"   💡 Suggestion: {action['action_type']} ({confidence}% confidence)")
                self._create_action_suggestion(email_id, action, context)

        # Update email category
        self.cursor.execute("""
            UPDATE emails SET category = ? WHERE email_id = ?
        """, (analysis['category'], email_id))

        self.conn.commit()

    def _apply_action(self, email_id: int, action: Dict, context: Dict):
        """Auto-apply high-confidence actions"""

        action_type = action['action_type']
        data = action['data']

        try:
            if action_type == 'create_construction_rfi':
                project_code = data.get('project_code') or (
                    context['projects'][0]['project_code'] if context['projects'] else None
                )

                if project_code:
                    self.cursor.execute("""
                        INSERT INTO rfis (
                            project_code, subject, description,
                            date_sent, status, priority, extracted_from_email_id
                        ) VALUES (?, ?, ?, ?, 'open', 'normal', ?)
                    """, (
                        project_code,
                        data.get('subject', 'Construction RFI from email'),
                        data.get('description', ''),
                        datetime.now().strftime('%Y-%m-%d'),
                        email_id
                    ))

                    # Link email to project
                    self.cursor.execute("""
                        INSERT OR IGNORE INTO email_project_links (email_id, project_code)
                        VALUES (?, ?)
                    """, (email_id, project_code))

            elif action_type == 'update_project':
                project_code = data.get('project_code') or (
                    context['projects'][0]['project_code'] if context['projects'] else None
                )

                if project_code:
                    # Build dynamic UPDATE query
                    updates = []
                    values = []
                    for key, value in data.items():
                        if key != 'project_code':
                            updates.append(f"{key} = ?")
                            values.append(value)

                    if updates:
                        values.append(project_code)
                        self.cursor.execute(
                            f"UPDATE projects SET {', '.join(updates)} WHERE project_code = ?",
                            values
                        )

            self.conn.commit()

        except Exception as e:
            print(f"      ⚠️  Action failed: {e}")

    def _create_schema_suggestion(self, schema_thought: Dict):
        """Create suggestion for database schema improvement"""
        # This goes into a special review queue for schema changes
        import uuid

        suggestion = {
            'id': str(uuid.uuid4()),
            'type': 'schema_improvement',
            'suggestion': schema_thought['suggestion'],
            'new_table': schema_thought.get('new_table'),
            'reasoning': schema_thought['reasoning'],
            'created_at': datetime.now().isoformat()
        }

        # Store in ai_suggestions_queue
        self.cursor.execute("""
            INSERT INTO ai_suggestions_queue (
                id, project_code, suggestion_type, proposed_fix, evidence,
                confidence, impact_type, impact_summary,
                severity, bucket, status, created_at
            ) VALUES (?, 'SYSTEM', 'schema_improvement', ?, ?, 0.8,
                     'database_quality', ?, 'medium', 'needs_attention',
                     'pending', CURRENT_TIMESTAMP)
        """, (
            suggestion['id'],
            json.dumps(suggestion),
            json.dumps({'reasoning': schema_thought['reasoning']}),
            schema_thought['suggestion']
        ))

        self.conn.commit()

    def _create_action_suggestion(self, email_id: int, action: Dict, context: Dict):
        """Create suggestion for human review"""
        import uuid

        project_code = (
            context['projects'][0]['project_code']
            if context['projects']
            else 'SYSTEM'
        )

        self.cursor.execute("""
            INSERT INTO ai_suggestions_queue (
                id, project_code, suggestion_type, proposed_fix, evidence,
                confidence, impact_type, impact_summary,
                severity, bucket, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (
            str(uuid.uuid4()),
            project_code,
            action['action_type'],
            json.dumps(action),
            json.dumps({'email_id': email_id}),
            action['confidence'] / 100.0,
            'data_quality',
            action['reasoning'],
            'medium',
            'needs_attention'
        ))

        self.conn.commit()

    def process_batch(self, limit=20):
        """Process batch of recent emails"""
        print("=" * 80)
        print("🧠 SMART EMAIL SYSTEM")
        print("=" * 80)
        print("\nTwo-layer processing:")
        print("  Layer 1: Fast context lookup (free)")
        print("  Layer 2: Focused AI analysis (cheap)\n")

        self.cursor.execute("""
            SELECT email_id, subject, sender_email
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
        print("✅ DONE")
        print("=" * 80)

    def close(self):
        self.conn.close()


def main():
    print("🧠 SMART EMAIL SYSTEM")
    print("Fast context lookup → Focused AI analysis")
    print("Learns and suggests schema improvements\n")

    system = SmartEmailSystem()

    try:
        system.process_batch(limit=20)
    finally:
        system.close()


if __name__ == "__main__":
    main()
