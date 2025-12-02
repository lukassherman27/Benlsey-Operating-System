#!/usr/bin/env python3
"""
PROPOSAL AUTOMATION ENGINE

Generates AI suggestions for proposal management:
1. Follow-up reminders (no contact in X days)
2. Contract template suggestions (find similar past proposals)
3. Email draft generation (auto-draft follow-ups)
4. Action recommendations (next steps based on lifecycle)

Populates the ai_suggestions_queue for dashboard display
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid
from openai import OpenAI

DB_PATH = "/Users/lukassherman/Desktop/BDS_SYSTEM/01_DATABASES/bensley_master.db"


class ProposalAutomationEngine:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Initialize OpenAI if available
        api_key = os.environ.get('OPENAI_API_KEY')
        self.ai_enabled = bool(api_key)
        if self.ai_enabled:
            self.client = OpenAI(api_key=api_key)

    def run_all_generators(self):
        """Run all suggestion generators"""
        print("=" * 80)
        print("🤖 PROPOSAL AUTOMATION ENGINE")
        print("=" * 80)
        print()

        suggestions_created = 0

        # 1. Generate follow-up reminders
        print("1️⃣  Generating follow-up reminders...")
        suggestions_created += self.generate_followup_reminders()

        # 2. Generate contract template suggestions
        print("\n2️⃣  Finding contract templates...")
        suggestions_created += self.generate_template_suggestions()

        # 3. Generate action recommendations
        print("\n3️⃣  Analyzing proposal lifecycle stages...")
        suggestions_created += self.generate_lifecycle_actions()

        # 4. Generate financial risk alerts
        print("\n4️⃣  Checking financial risks...")
        suggestions_created += self.generate_financial_alerts()

        print()
        print("=" * 80)
        print(f"✅ Generated {suggestions_created} suggestions")
        print("=" * 80)

        return suggestions_created

    def generate_followup_reminders(self) -> int:
        """Generate suggestions for proposals needing follow-up"""
        # Find proposals with no recent contact
        self.cursor.execute("""
            SELECT
                p.project_code,
                p.project_name,
                p.client_name,
                p.status,
                p.days_since_contact,
                p.estimated_value_usd,
                MAX(e.date) as last_email_date
            FROM projects p
            LEFT JOIN email_project_links epl ON p.project_code = epl.project_code
            LEFT JOIN emails e ON epl.email_id = e.email_id
            WHERE p.is_active_project = 1
            AND p.status IN ('active', 'proposal_sent', 'in_negotiation')
            GROUP BY p.project_code
            HAVING (
                p.days_since_contact > 14
                OR MAX(e.date) < datetime('now', '-14 days')
            )
        """)

        proposals = self.cursor.fetchall()
        count = 0

        for proposal in proposals:
            # Check if suggestion already exists
            if self._suggestion_exists(proposal['project_code'], 'followup_reminder'):
                continue

            days_since = proposal['days_since_contact'] or 14

            # Determine severity
            if days_since > 30:
                severity = 'high'
                bucket = 'urgent'
            elif days_since > 21:
                severity = 'medium'
                bucket = 'urgent'
            else:
                severity = 'low'
                bucket = 'needs_attention'

            # Get recent emails for context
            email_context = self._get_recent_emails(proposal['project_code'], limit=3)

            # Draft follow-up email if AI is enabled
            draft_email = None
            if self.ai_enabled and email_context:
                draft_email = self._draft_followup_email(proposal, email_context)

            # Create suggestion
            proposed_fix = {
                'action': 'send_followup_email',
                'draft_email': draft_email,
                'suggested_subject': f"Following up on {proposal['project_name']}",
                'priority': 'high' if days_since > 30 else 'medium'
            }

            evidence = {
                'days_since_contact': days_since,
                'last_email_date': proposal['last_email_date'],
                'proposal_status': proposal['status'],
                'recent_emails': len(email_context)
            }

            self._create_suggestion(
                project_code=proposal['project_code'],
                suggestion_type='followup_reminder',
                proposed_fix=proposed_fix,
                evidence=evidence,
                confidence=0.9,
                severity=severity,
                bucket=bucket,
                impact_type='client_relationship',
                impact_summary=f"{days_since} days since last contact - risk of losing {proposal['client_name']}",
                impact_value_usd=proposal['estimated_value_usd']
            )

            count += 1
            print(f"   ✅ {proposal['project_code']}: {days_since} days since contact")

        return count

    def generate_template_suggestions(self) -> int:
        """Find similar past proposals to use as templates"""
        # Get active proposals without contracts
        self.cursor.execute("""
            SELECT
                p.project_code,
                p.project_name,
                p.client_name,
                p.project_type,
                p.estimated_value_usd,
                p.location
            FROM projects p
            WHERE p.is_active_project = 1
            AND p.status IN ('proposal_sent', 'in_negotiation')
            AND NOT EXISTS (
                SELECT 1 FROM project_documents pd
                WHERE pd.project_id = p.project_id
                AND pd.document_type = 'bensley_contract'
            )
        """)

        proposals = self.cursor.fetchall()
        count = 0

        for proposal in proposals:
            # Find similar completed projects
            similar = self._find_similar_proposals(proposal)

            if not similar:
                continue

            # Check if suggestion already exists
            if self._suggestion_exists(proposal['project_code'], 'contract_template'):
                continue

            proposed_fix = {
                'action': 'use_contract_template',
                'template_project': similar[0]['project_code'],
                'template_name': similar[0]['project_name'],
                'similarity_score': similar[0]['similarity'],
                'all_matches': [
                    {
                        'code': s['project_code'],
                        'name': s['project_name'],
                        'similarity': s['similarity']
                    } for s in similar[:3]
                ]
            }

            evidence = {
                'matching_criteria': similar[0]['match_reasons'],
                'template_documents': similar[0].get('document_count', 0)
            }

            self._create_suggestion(
                project_code=proposal['project_code'],
                suggestion_type='contract_template',
                proposed_fix=proposed_fix,
                evidence=evidence,
                confidence=similar[0]['similarity'],
                severity='medium',
                bucket='needs_attention',
                impact_type='operational_efficiency',
                impact_summary=f"Use {similar[0]['project_code']} contract as template (similar project)",
                impact_value_usd=None
            )

            count += 1
            print(f"   ✅ {proposal['project_code']}: Template from {similar[0]['project_code']}")

        return count

    def generate_lifecycle_actions(self) -> int:
        """Generate action recommendations based on proposal lifecycle stage"""
        # TODO: Implement lifecycle-based suggestions
        # Examples:
        # - "Proposal sent 30 days ago → Schedule check-in call"
        # - "In negotiation → Prepare final contract"
        # - "Verbal yes → Send formal proposal"
        return 0

    def generate_financial_alerts(self) -> int:
        """Generate financial risk alerts"""
        # Find projects with outstanding payments > 30 days
        self.cursor.execute("""
            SELECT
                p.project_code,
                p.project_name,
                p.outstanding_usd,
                p.client_name
            FROM projects p
            WHERE p.outstanding_usd > 0
            AND p.is_active_project = 1
        """)

        projects = self.cursor.fetchall()
        count = 0

        for project in projects:
            if self._suggestion_exists(project['project_code'], 'financial_risk'):
                continue

            amount = project['outstanding_usd']
            severity = 'high' if amount > 50000 else 'medium' if amount > 10000 else 'low'
            bucket = 'urgent' if amount > 50000 else 'needs_attention'

            proposed_fix = {
                'action': 'send_payment_reminder',
                'amount_usd': amount,
                'suggested_message': f"Gentle reminder about outstanding invoice"
            }

            evidence = {
                'outstanding_amount': amount,
                'client': project['client_name']
            }

            self._create_suggestion(
                project_code=project['project_code'],
                suggestion_type='financial_risk',
                proposed_fix=proposed_fix,
                evidence=evidence,
                confidence=0.95,
                severity=severity,
                bucket=bucket,
                impact_type='financial_risk',
                impact_summary=f"${amount:,.0f} outstanding from {project['client_name']}",
                impact_value_usd=amount
            )

            count += 1

        return count

    def _find_similar_proposals(self, proposal: Dict) -> List[Dict]:
        """Find similar past proposals for template matching"""
        matches = []

        # Search by project type
        if proposal['project_type']:
            self.cursor.execute("""
                SELECT DISTINCT
                    p.project_code,
                    p.project_name,
                    p.project_type,
                    p.location,
                    COUNT(pd.document_id) as document_count
                FROM projects p
                LEFT JOIN project_documents pd ON p.project_id = pd.project_id
                WHERE p.project_type = ?
                AND p.project_code != ?
                AND p.status = 'won'
                AND EXISTS (
                    SELECT 1 FROM project_documents pd2
                    WHERE pd2.project_id = p.project_id
                    AND pd2.document_type IN ('bensley_contract', 'proposal')
                )
                GROUP BY p.project_code
                ORDER BY document_count DESC
                LIMIT 5
            """, (proposal['project_type'], proposal['project_code']))

            for row in self.cursor.fetchall():
                match_reasons = [f"Same type: {proposal['project_type']}"]
                similarity = 0.7

                # Boost if same location
                if proposal['location'] and row['location'] and \
                   proposal['location'].lower() in row['location'].lower():
                    match_reasons.append(f"Same location: {row['location']}")
                    similarity += 0.2

                matches.append({
                    'project_code': row['project_code'],
                    'project_name': row['project_name'],
                    'similarity': min(similarity, 0.95),
                    'match_reasons': match_reasons,
                    'document_count': row['document_count']
                })

        return sorted(matches, key=lambda x: x['similarity'], reverse=True)

    def _get_recent_emails(self, project_code: str, limit: int = 5) -> List[Dict]:
        """Get recent emails for a project"""
        self.cursor.execute("""
            SELECT
                e.subject,
                e.sender_email,
                e.date,
                e.snippet,
                ec.ai_summary
            FROM emails e
            JOIN email_project_links epl ON e.email_id = epl.email_id
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE epl.project_code = ?
            ORDER BY e.date DESC
            LIMIT ?
        """, (project_code, limit))

        return [dict(row) for row in self.cursor.fetchall()]

    def _draft_followup_email(self, proposal: Dict, email_context: List[Dict]) -> str:
        """Use OpenAI to draft a follow-up email"""
        if not self.ai_enabled:
            return None

        # Build context from recent emails
        context = f"Project: {proposal['project_name']}\n"
        context += f"Client: {proposal['client_name']}\n"
        context += f"Status: {proposal['status']}\n"
        context += f"Days since contact: {proposal['days_since_contact']}\n\n"
        context += "Recent email thread:\n"

        for email in reversed(email_context):  # Chronological order
            context += f"- {email['date']}: {email['subject']}\n"
            if email['ai_summary']:
                context += f"  Summary: {email['ai_summary']}\n"

        prompt = f"""Draft a professional, friendly follow-up email for this design project.

Context:
{context}

The email should:
- Be warm but professional
- Reference the project briefly
- Ask about their timeline/decision
- Offer to answer any questions
- Keep it under 100 words
- Don't be pushy

Return only the email body (no subject line)."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional business development assistant for a high-end architecture and design firm."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"   ⚠️  Failed to draft email: {e}")
            return None

    def _suggestion_exists(self, project_code: str, suggestion_type: str) -> bool:
        """Check if an active suggestion already exists"""
        self.cursor.execute("""
            SELECT 1 FROM ai_suggestions_queue
            WHERE project_code = ?
            AND suggestion_type = ?
            AND status = 'pending'
            AND created_at > datetime('now', '-7 days')
        """, (project_code, suggestion_type))

        return self.cursor.fetchone() is not None

    def _create_suggestion(
        self,
        project_code: str,
        suggestion_type: str,
        proposed_fix: Dict,
        evidence: Dict,
        confidence: float,
        severity: str,
        bucket: str,
        impact_type: str,
        impact_summary: str,
        impact_value_usd: Optional[float] = None
    ):
        """Create a new AI suggestion"""
        suggestion_id = str(uuid.uuid4())

        self.cursor.execute("""
            INSERT INTO ai_suggestions_queue (
                id, project_code, suggestion_type, proposed_fix, evidence,
                confidence, impact_type, impact_value_usd, impact_summary,
                severity, bucket, auto_apply_candidate, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (
            suggestion_id,
            project_code,
            suggestion_type,
            json.dumps(proposed_fix),
            json.dumps(evidence),
            confidence,
            impact_type,
            impact_value_usd,
            impact_summary,
            severity,
            bucket,
            0  # Don't auto-apply by default
        ))

        self.conn.commit()

    def close(self):
        self.conn.close()


def main():
    engine = ProposalAutomationEngine()
    try:
        suggestions_created = engine.run_all_generators()
        print(f"\n✅ Automation complete! Created {suggestions_created} suggestions.")
        print("\nView suggestions in the dashboard or run:")
        print("  python3 review_suggestions.py")
    finally:
        engine.close()


if __name__ == "__main__":
    main()
