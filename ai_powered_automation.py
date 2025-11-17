#!/usr/bin/env python3
"""
AI-POWERED PROPOSAL AUTOMATION (with Human-in-the-Loop Learning)

Uses GPT-4 to:
1. Understand email nuance (not just keywords)
2. Suggest actions (follow-ups, categories, migrations)
3. Learn from your feedback (yes/no/modify)
4. Build training data for local model distillation

Your feedback creates training examples:
- "This email is actually a legal document" → Creates 'legal' category
- "Don't follow up on this, client is on vacation" → Learns context
- "This needs a new field: contract_expiry_date" → Suggests migration
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import uuid
from openai import OpenAI

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


class AIPoweredAutomation:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Initialize OpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY required for AI-powered mode")

        self.client = OpenAI(api_key=api_key)

    def analyze_uncategorized_emails(self, limit=50):
        """Use AI to suggest categories for uncategorized emails"""
        print("=" * 80)
        print("🤖 AI EMAIL ANALYSIS")
        print("=" * 80)

        # Get uncategorized or low-confidence emails
        self.cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                e.snippet,
                e.body_full,
                e.category,
                ec.ai_summary
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.category IS NULL OR e.category = 'general'
            ORDER BY e.date DESC
            LIMIT ?
        """, (limit,))

        emails = self.cursor.fetchall()
        print(f"\nFound {len(emails)} emails needing categorization\n")

        # Get existing categories from database
        existing_categories = self._get_existing_categories()

        suggestions_created = 0

        for i, email in enumerate(emails, 1):
            print(f"[{i}/{len(emails)}] Analyzing: {email['subject'][:60]}...")

            # Use AI to understand the email
            ai_analysis = self._analyze_email_with_ai(email, existing_categories)

            if not ai_analysis:
                continue

            # Create suggestion for user review
            self._create_categorization_suggestion(email, ai_analysis)
            suggestions_created += 1

        print(f"\n✅ Created {suggestions_created} categorization suggestions")
        print("Review them with: python3 review_suggestions.py")

        return suggestions_created

    def analyze_proposal_actions(self, limit=20):
        """Use AI to suggest actions for active proposals"""
        print("\n" + "=" * 80)
        print("🎯 AI PROPOSAL ACTION ANALYSIS")
        print("=" * 80)

        # Get active proposals with their email history
        self.cursor.execute("""
            SELECT
                p.project_code,
                p.project_name,
                p.client_company as client_name,
                p.status,
                p.days_since_contact,
                p.project_value as estimated_value_usd
            FROM projects p
            WHERE p.is_active_project = 1
            AND p.status IN ('active', 'proposal_sent', 'in_negotiation')
            ORDER BY p.days_since_contact DESC
            LIMIT ?
        """, (limit,))

        proposals = self.cursor.fetchall()
        print(f"\nAnalyzing {len(proposals)} active proposals\n")

        suggestions_created = 0

        for i, proposal in enumerate(proposals, 1):
            print(f"[{i}/{len(proposals)}] {proposal['project_code']}: {proposal['project_name'][:40]}...")

            # Get email context for this proposal
            email_context = self._get_proposal_email_context(proposal['project_code'])

            # Use AI to suggest next action
            ai_suggestion = self._get_ai_action_suggestion(proposal, email_context)

            if ai_suggestion:
                self._create_action_suggestion(proposal, ai_suggestion)
                suggestions_created += 1

        print(f"\n✅ Created {suggestions_created} action suggestions")
        return suggestions_created

    def suggest_database_improvements(self):
        """Use AI to analyze data and suggest schema improvements"""
        print("\n" + "=" * 80)
        print("🔧 AI DATABASE ANALYSIS")
        print("=" * 80)

        # Analyze patterns in data that might need new fields/tables
        analyses = []

        # 1. Check for unstructured data in text fields
        print("\n1️⃣  Analyzing unstructured data patterns...")
        unstructured = self._find_unstructured_patterns()
        if unstructured:
            analyses.append({
                'type': 'schema_improvement',
                'findings': unstructured,
                'suggestions': self._get_ai_schema_suggestions(unstructured)
            })

        # 2. Check for missing relationships
        print("2️⃣  Checking for missing relationships...")
        # TODO: Implement

        # 3. Check for performance issues
        print("3️⃣  Analyzing query patterns for indexes...")
        # TODO: Implement

        return analyses

    def _analyze_email_with_ai(self, email: Dict, existing_categories: List[str]) -> Optional[Dict]:
        """Use GPT-4 to understand email and suggest category"""

        email_text = f"""
Subject: {email['subject']}
From: {email['sender_email']}
Date: {email['date']}

Body:
{email['snippet'] or email['body_full'][:1000]}
"""

        prompt = f"""You are an AI assistant helping categorize business emails for a design firm.

Existing categories: {', '.join(existing_categories)}

Analyze this email and determine:
1. Best category (from existing or suggest NEW if none fit)
2. Key entities mentioned (clients, projects, amounts, dates)
3. Importance/urgency (1-10)
4. Suggested action (if any)
5. Confidence in categorization (0-100%)

Email:
{email_text}

Respond in JSON format:
{{
    "category": "...",
    "is_new_category": false,
    "new_category_reason": "...",
    "entities": {{
        "project_codes": [],
        "clients": [],
        "amounts": [],
        "dates": []
    }},
    "importance": 7,
    "urgency": "medium",
    "suggested_action": "...",
    "reasoning": "...",
    "confidence": 85
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # gpt-4o supports JSON mode and is faster/cheaper
                messages=[
                    {"role": "system", "content": "You are a business intelligence assistant analyzing emails for categorization and action suggestions."},
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

    def _get_ai_action_suggestion(self, proposal: Dict, email_context: List[Dict]) -> Optional[Dict]:
        """Use AI to suggest next action for a proposal"""

        context_text = f"""
Proposal: {proposal['project_code']} - {proposal['project_name'] or 'N/A'}
Client: {proposal['client_name'] or 'N/A'}
Status: {proposal['status'] or 'N/A'}
Days Since Contact: {proposal['days_since_contact'] or 'N/A'}
Estimated Value: ${proposal['estimated_value_usd']:,.0f if proposal['estimated_value_usd'] else 0}

Recent Email Thread:
"""

        for email in email_context[-5:]:  # Last 5 emails
            context_text += f"""
- {email['date']}: {email['subject']}
  From: {email['sender_email']}
  Summary: {email.get('ai_summary', 'N/A')}
"""

        prompt = f"""You are a business development AI assistant. Based on this proposal's context, suggest the BEST next action.

{context_text}

Consider:
- How long since last contact?
- What was discussed in recent emails?
- What's the proposal status?
- What's the business value at stake?

Suggest ONE specific action. Options:
1. Send follow-up email (draft it)
2. Schedule a call
3. Send additional information
4. Update proposal/pricing
5. Wait (if appropriate)
6. Close/archive (if deal is dead)
7. Other (specify)

Respond in JSON:
{{
    "action": "send_followup_email",
    "reasoning": "...",
    "urgency": "high|medium|low",
    "draft_email": "..." (if action is email),
    "suggested_subject": "...",
    "confidence": 85,
    "alternative_actions": ["action2", "action3"]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # gpt-4o supports JSON mode and is faster/cheaper
                messages=[
                    {"role": "system", "content": "You are a business development strategist helping manage proposal pipeline."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            suggestion = json.loads(response.choices[0].message.content)
            return suggestion

        except Exception as e:
            print(f"   ⚠️  AI suggestion failed: {e}")
            return None

    def _find_unstructured_patterns(self) -> List[Dict]:
        """Find patterns in text fields that could be structured"""
        patterns = []

        # Check email bodies for recurring patterns
        self.cursor.execute("""
            SELECT body_full
            FROM emails
            WHERE body_full IS NOT NULL
            LIMIT 100
        """)

        # Look for things like:
        # - Dollar amounts → Should be extracted to 'mentioned_amount' field
        # - Dates → Should be extracted to 'mentioned_dates' field
        # - Project codes → Should be linked in relationships table
        # etc.

        # TODO: Implement pattern detection

        return patterns

    def _get_ai_schema_suggestions(self, patterns: List[Dict]) -> str:
        """Use AI to suggest schema improvements"""
        # TODO: Implement
        return ""

    def _get_existing_categories(self) -> List[str]:
        """Get list of existing email categories"""
        self.cursor.execute("""
            SELECT DISTINCT category
            FROM emails
            WHERE category IS NOT NULL
            AND category != 'general'
        """)

        return [row['category'] for row in self.cursor.fetchall()]

    def _get_proposal_email_context(self, project_code: str) -> List[Dict]:
        """Get email thread for a proposal"""
        self.cursor.execute("""
            SELECT
                e.subject,
                e.sender_email,
                e.date,
                e.snippet,
                ec.ai_summary
            FROM emails e
            LEFT JOIN email_project_links epl ON e.email_id = epl.email_id
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE epl.project_code = ?
            ORDER BY e.date ASC
        """, (project_code,))

        return [dict(row) for row in self.cursor.fetchall()]

    def _create_categorization_suggestion(self, email: Dict, ai_analysis: Dict):
        """Create a suggestion for user to approve/reject category"""
        suggestion_id = str(uuid.uuid4())

        proposed_fix = {
            'action': 'categorize_email',
            'email_id': email['email_id'],
            'suggested_category': ai_analysis['category'],
            'is_new_category': ai_analysis.get('is_new_category', False),
            'new_category_reason': ai_analysis.get('new_category_reason'),
            'entities': ai_analysis.get('entities', {}),
            'importance': ai_analysis.get('importance', 5),
            'ai_reasoning': ai_analysis.get('reasoning', '')
        }

        evidence = {
            'email_subject': email['subject'],
            'from': email['sender_email'],
            'confidence': ai_analysis.get('confidence', 50)
        }

        # Determine severity based on confidence and importance
        confidence = ai_analysis.get('confidence', 50)
        importance = ai_analysis.get('importance', 5)

        if confidence > 80 and importance > 7:
            severity = 'high'
            bucket = 'urgent'
        elif confidence > 60:
            severity = 'medium'
            bucket = 'needs_attention'
        else:
            severity = 'low'
            bucket = 'fyi'

        self.cursor.execute("""
            INSERT INTO ai_suggestions_queue (
                id, project_code, suggestion_type, proposed_fix, evidence,
                confidence, impact_type, impact_summary,
                severity, bucket, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (
            suggestion_id,
            'SYSTEM',  # Not project-specific
            'email_categorization',
            json.dumps(proposed_fix),
            json.dumps(evidence),
            confidence / 100.0,
            'data_quality',
            f"AI suggests category: {ai_analysis['category']}",
            severity,
            bucket
        ))

        self.conn.commit()

    def _create_action_suggestion(self, proposal: Dict, ai_suggestion: Dict):
        """Create action suggestion for proposal"""
        suggestion_id = str(uuid.uuid4())

        proposed_fix = {
            'action': ai_suggestion['action'],
            'reasoning': ai_suggestion.get('reasoning', ''),
            'draft_email': ai_suggestion.get('draft_email'),
            'suggested_subject': ai_suggestion.get('suggested_subject'),
            'alternative_actions': ai_suggestion.get('alternative_actions', [])
        }

        evidence = {
            'days_since_contact': proposal['days_since_contact'],
            'proposal_status': proposal['status'],
            'confidence': ai_suggestion.get('confidence', 50)
        }

        urgency = ai_suggestion.get('urgency', 'medium')
        severity = 'high' if urgency == 'high' else 'medium' if urgency == 'medium' else 'low'
        bucket = 'urgent' if urgency == 'high' else 'needs_attention'

        self.cursor.execute("""
            INSERT INTO ai_suggestions_queue (
                id, project_code, suggestion_type, proposed_fix, evidence,
                confidence, impact_type, impact_value_usd, impact_summary,
                severity, bucket, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (
            suggestion_id,
            proposal['project_code'],
            'proposal_action',
            json.dumps(proposed_fix),
            json.dumps(evidence),
            ai_suggestion.get('confidence', 50) / 100.0,
            'client_relationship',
            proposal['estimated_value_usd'],
            f"AI suggests: {ai_suggestion['action']}",
            severity,
            bucket
        ))

        self.conn.commit()

    def close(self):
        self.conn.close()


def main():
    print("🤖 AI-POWERED PROPOSAL AUTOMATION")
    print("Using GPT-4 to understand nuance and suggest actions\n")

    engine = AIPoweredAutomation()

    try:
        # 1. Analyze uncategorized emails
        email_suggestions = engine.analyze_uncategorized_emails(limit=20)

        # 2. Analyze active proposals (DISABLED - fixing bugs)
        action_suggestions = 0  # engine.analyze_proposal_actions(limit=10)

        print("\n" + "=" * 80)
        print(f"✅ COMPLETE! Generated {email_suggestions + action_suggestions} AI suggestions")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Review suggestions: python3 review_suggestions.py")
        print("2. Approve/reject to build training data")
        print("3. After 100+ examples, fine-tune local model")

    finally:
        engine.close()


if __name__ == "__main__":
    main()
