#!/usr/bin/env python3
"""
BENSLEY EMAIL INTELLIGENCE SYSTEM
Processes all emails with AI to extract intelligence and link to proposals
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Correct database path
DB_PATH = "/Users/lukassherman/Library/CloudStorage/OneDrive-Personal/Bensley/Benlsey-Operating-System/database/bensley_master.db"


class BensleyEmailIntelligence:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY required")

        self.client = OpenAI(api_key=api_key)

        # Stats
        self.stats = {
            'processed': 0,
            'categorized': 0,
            'linked': 0,
            'summaries': 0,
            'errors': 0
        }

    def get_proposals_context(self) -> List[Dict]:
        """Get all proposals for context matching"""
        self.cursor.execute("""
            SELECT proposal_id, project_code, project_name,
                   client_company, contact_person, project_value, status
            FROM proposals
            ORDER BY project_code
        """)

        proposals = []
        for row in self.cursor.fetchall():
            proposals.append({
                'proposal_id': row['proposal_id'],
                'project_code': row['project_code'],
                'project_name': row['project_name'] or '',
                'client_company': row['client_company'] or '',
                'contact_person': row['contact_person'] or '',
                'project_value': row['project_value'] or 0,
                'status': row['status'] or 'unknown'
            })

        return proposals

    def process_all_emails(self, limit=None):
        """Process all unprocessed emails"""
        print("="*80)
        print("🤖 BENSLEY EMAIL INTELLIGENCE SYSTEM")
        print("="*80)
        print(f"\nDatabase: {DB_PATH}")

        # Get proposals context
        print("\n📊 Loading proposals context...")
        proposals = self.get_proposals_context()
        print(f"   Loaded {len(proposals)} proposals")

        # Get emails to process
        query = """
            SELECT email_id, sender_email, sender_name, subject,
                   snippet, body_full, date, processed
            FROM emails
            WHERE processed = 0 OR category IS NULL
            ORDER BY date DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query)
        emails = self.cursor.fetchall()

        print(f"\n📧 Processing {len(emails)} emails...\n")

        for i, email in enumerate(emails, 1):
            print(f"[{i}/{len(emails)}] {email['subject'][:60]}...")
            try:
                self.process_email(email, proposals)
                self.stats['processed'] += 1
            except Exception as e:
                print(f"   ⚠️  Error: {e}")
                self.stats['errors'] += 1

            # Commit every 10 emails
            if i % 10 == 0:
                self.conn.commit()
                print(f"   💾 Saved progress ({i}/{len(emails)})")

        # Final commit
        self.conn.commit()

        # Print stats
        print("\n" + "="*80)
        print("✅ PROCESSING COMPLETE")
        print("="*80)
        print(f"Processed: {self.stats['processed']}")
        print(f"Categorized: {self.stats['categorized']}")
        print(f"Linked to proposals: {self.stats['linked']}")
        print(f"Summaries created: {self.stats['summaries']}")
        print(f"Errors: {self.stats['errors']}")
        print("="*80)

    def process_email(self, email: sqlite3.Row, proposals: List[Dict]):
        """Process a single email with AI"""

        email_id = email['email_id']

        # Build context for AI
        proposals_summary = self._build_proposals_summary(proposals)

        # Call AI to analyze email
        analysis = self._analyze_email(email, proposals_summary)

        if not analysis:
            return

        # Update email with category
        if analysis.get('category'):
            self.cursor.execute("""
                UPDATE emails
                SET category = ?, ai_confidence = ?, processed = 1
                WHERE email_id = ?
            """, (analysis['category'], analysis.get('confidence', 0.5), email_id))
            self.stats['categorized'] += 1

        # Store AI summary
        if analysis.get('summary'):
            self.cursor.execute("""
                UPDATE emails
                SET ai_summary = ?
                WHERE email_id = ?
            """, (analysis['summary'], email_id))
            self.stats['summaries'] += 1

        # Store extracted data
        if analysis.get('extracted_data'):
            self.cursor.execute("""
                UPDATE emails
                SET ai_extracted_data = ?
                WHERE email_id = ?
            """, (json.dumps(analysis['extracted_data']), email_id))

        # Link to proposals
        if analysis.get('linked_proposals'):
            for proposal in analysis['linked_proposals']:
                self._link_email_to_proposal(
                    email_id,
                    proposal['proposal_id'],
                    proposal['confidence'],
                    'ai_suggested'
                )
            self.stats['linked'] += len(analysis['linked_proposals'])

        print(f"   ✓ {analysis.get('category', 'Unknown')} | Confidence: {analysis.get('confidence', 0):.0%}")

    def _analyze_email(self, email: sqlite3.Row, proposals_summary: str) -> Optional[Dict]:
        """Use AI to analyze email and extract intelligence"""

        body = email['body_full'] or email['snippet'] or ''

        prompt = f"""You are analyzing an email for a design firm's business intelligence system.

EMAIL:
From: {email['sender_email']} ({email['sender_name']})
Subject: {email['subject']}
Date: {email['date']}
Body:
{body[:2000]}

PROPOSALS CONTEXT (all current proposals/projects):
{proposals_summary}

YOUR TASK:
1. Categorize this email (RFI, Proposal, Contract, Financial, Project Update, General, Spam)
2. Extract key information
3. Link to relevant proposals if any
4. Create a brief summary

Respond in JSON:
{{
    "category": "RFI|Proposal|Contract|Financial|Project Update|General|Spam",
    "confidence": 0.85,
    "summary": "Brief 1-2 sentence summary of email content",
    "extracted_data": {{
        "key_points": ["point 1", "point 2"],
        "action_items": ["action 1"],
        "mentioned_amounts": [],
        "mentioned_dates": []
    }},
    "linked_proposals": [
        {{
            "proposal_id": 123,
            "project_code": "BK-070",
            "confidence": 0.9,
            "reasoning": "Email mentions Dubai Resort by name"
        }}
    ]
}}

If email is not related to any proposals, set linked_proposals to empty array.
Be conservative - only link if confidence > 70%.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cheaper, faster model
                messages=[
                    {"role": "system", "content": "You are a business intelligence AI that extracts structured data from emails."},
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

    def _build_proposals_summary(self, proposals: List[Dict]) -> str:
        """Build concise summary of all proposals for AI context"""
        lines = []
        for p in proposals[:50]:  # Limit to 50 most recent to save tokens
            lines.append(
                f"- {p['project_code']}: {p['project_name']} | "
                f"Client: {p['client_company']} | "
                f"Status: {p['status']} | "
                f"Value: ${p['project_value']:,.0f}"
            )
        return "\n".join(lines)

    def _link_email_to_proposal(self, email_id: int, proposal_id: int,
                                 confidence: float, link_type: str):
        """Link email to proposal"""
        try:
            # Use existing schema: confidence_score, match_reasons, auto_linked
            auto_linked = 1 if link_type == 'ai_suggested' else 0
            self.cursor.execute("""
                INSERT OR IGNORE INTO email_proposal_links
                (email_id, proposal_id, confidence_score, match_reasons, auto_linked)
                VALUES (?, ?, ?, ?, ?)
            """, (email_id, proposal_id, confidence, link_type, auto_linked))
        except Exception as e:
            print(f"   ⚠️  Link failed: {e}")

    def close(self):
        self.conn.close()


def main():
    import sys

    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"Processing {limit} emails...")
        except:
            print("Usage: python3 bensley_email_intelligence.py [limit]")
            sys.exit(1)

    processor = BensleyEmailIntelligence()

    try:
        processor.process_all_emails(limit=limit)
    finally:
        processor.close()


if __name__ == "__main__":
    main()
