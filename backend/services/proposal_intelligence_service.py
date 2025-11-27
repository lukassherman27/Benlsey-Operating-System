"""
Proposal Intelligence Service - AI-Powered Proposal Context and Assistance

Provides:
- Rich proposal context with email history and attachments
- Natural language queries about proposals
- Draft email generation for follow-ups
- Status summaries and recommendations
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from openai import OpenAI

from .base_service import BaseService


class ProposalIntelligenceService(BaseService):
    """Service for AI-powered proposal intelligence and assistance"""

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        api_key = os.environ.get('OPENAI_API_KEY')
        self.ai_enabled = bool(api_key)
        if self.ai_enabled:
            self.client = OpenAI(api_key=api_key)

    def get_proposal_context(self, project_code: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a proposal including:
        - Basic proposal info
        - Email intelligence (count, categories, latest)
        - Attachments
        - Status history
        - AI-generated summary
        """
        # Get data from proposal_intelligence view
        intelligence = self.execute_query("""
            SELECT * FROM proposal_intelligence
            WHERE project_code = ?
        """, [project_code])

        if not intelligence:
            return {'success': False, 'error': 'Proposal not found'}

        proposal = dict(intelligence[0])

        # Get recent emails with AI summaries
        emails = self.execute_query("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.date,
                e.folder,
                ec.ai_summary,
                ec.category,
                ec.urgency_level,
                ec.action_required,
                ec.client_sentiment
            FROM emails e
            JOIN email_content ec ON e.email_id = ec.email_id
            WHERE ec.linked_project_code = ?
            ORDER BY e.date DESC
            LIMIT 20
        """, [project_code])

        # Get attachments
        attachments = self.execute_query("""
            SELECT
                a.filename,
                a.file_type,
                a.category,
                a.file_size,
                e.date as email_date
            FROM attachments a
            JOIN emails e ON a.email_id = e.email_id
            JOIN email_content ec ON e.email_id = ec.email_id
            WHERE ec.linked_project_code = ?
            ORDER BY e.date DESC
            LIMIT 20
        """, [project_code])

        # Get status history
        status_history = self.execute_query("""
            SELECT
                old_status,
                new_status,
                status_date,
                notes
            FROM proposal_status_history
            WHERE project_code = ?
            ORDER BY status_date DESC
            LIMIT 10
        """, [project_code])

        # Generate AI summary if enabled
        ai_summary = None
        if self.ai_enabled and emails:
            ai_summary = self._generate_proposal_summary(proposal, emails)

        return {
            'success': True,
            'proposal': proposal,
            'recent_emails': [dict(e) for e in emails],
            'attachments': [dict(a) for a in attachments],
            'status_history': [dict(s) for s in status_history],
            'ai_summary': ai_summary
        }

    def get_proposals_needing_attention(self) -> List[Dict[str, Any]]:
        """Get proposals that need follow-up or have urgent emails"""
        results = self.execute_query("""
            SELECT
                project_code,
                project_name,
                client_company,
                email_count,
                urgent_emails,
                emails_needing_action,
                attention_status,
                engagement_level,
                days_since_contact,
                latest_email_subject,
                latest_email_summary
            FROM proposal_intelligence
            WHERE attention_status IN ('urgent', 'action_needed', 'follow_up_needed')
            ORDER BY
                CASE attention_status
                    WHEN 'urgent' THEN 1
                    WHEN 'action_needed' THEN 2
                    ELSE 3
                END,
                urgent_emails DESC,
                days_since_contact DESC
            LIMIT 20
        """, [])

        return [dict(r) for r in results]

    def generate_follow_up_email(
        self,
        project_code: str,
        tone: str = 'professional',
        purpose: str = 'follow_up'
    ) -> Dict[str, Any]:
        """
        Generate a draft follow-up email based on proposal context

        Args:
            project_code: The proposal to generate email for
            tone: 'professional', 'friendly', 'urgent'
            purpose: 'follow_up', 'check_status', 'schedule_meeting', 'send_update'
        """
        if not self.ai_enabled:
            return {'success': False, 'error': 'AI not enabled'}

        # Get proposal context
        context = self.get_proposal_context(project_code)
        if not context.get('success'):
            return context

        proposal = context['proposal']
        recent_emails = context['recent_emails'][:5]

        # Build context for AI
        email_context = ""
        for email in recent_emails:
            email_context += f"""
Date: {email['date']}
From: {email['sender_email']}
Subject: {email['subject']}
Summary: {email.get('ai_summary', 'N/A')}
---
"""

        prompt = f"""You are drafting a follow-up email for a design firm (Bensley Design Studios).

PROJECT: {proposal['project_name']} ({project_code})
CLIENT: {proposal.get('client_company', 'Unknown')}
CONTACT: {proposal.get('contact_person', 'Unknown')} ({proposal.get('contact_email', 'N/A')})
STATUS: {proposal.get('current_status', proposal.get('status', 'Unknown'))}
DAYS SINCE CONTACT: {proposal.get('days_since_contact', 'Unknown')}

RECENT EMAIL HISTORY:
{email_context}

INSTRUCTIONS:
- Purpose: {purpose}
- Tone: {tone}
- Write a professional email that references the conversation history
- Keep it concise but warm
- Include specific next steps or questions if appropriate
- Sign off as the Bensley team

Generate the email with:
- Subject line (starting with "Subject: ")
- Email body
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at writing professional business emails for a luxury design studio. You write clear, warm, and action-oriented emails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            email_text = response.choices[0].message.content.strip()

            # Parse subject and body
            lines = email_text.split('\n')
            subject = ""
            body_start = 0

            for i, line in enumerate(lines):
                if line.lower().startswith('subject:'):
                    subject = line[8:].strip()
                    body_start = i + 1
                    break

            body = '\n'.join(lines[body_start:]).strip()

            return {
                'success': True,
                'project_code': project_code,
                'to': proposal.get('contact_email', ''),
                'subject': subject,
                'body': body,
                'tone': tone,
                'purpose': purpose
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def answer_proposal_question(
        self,
        question: str,
        project_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a natural language question about proposals

        Args:
            question: The question to answer
            project_code: Optional - if provided, focuses on that proposal
        """
        if not self.ai_enabled:
            return {'success': False, 'error': 'AI not enabled'}

        # Build context
        if project_code:
            context = self.get_proposal_context(project_code)
            if not context.get('success'):
                return context

            context_text = f"""
PROPOSAL: {context['proposal']['project_name']} ({project_code})
CLIENT: {context['proposal'].get('client_company', 'Unknown')}
STATUS: {context['proposal'].get('current_status', 'Unknown')}
EMAIL COUNT: {context['proposal'].get('email_count', 0)}
URGENT EMAILS: {context['proposal'].get('urgent_emails', 0)}
DAYS SINCE CONTACT: {context['proposal'].get('days_since_contact', 'Unknown')}

RECENT EMAILS:
"""
            for email in context['recent_emails'][:5]:
                context_text += f"- [{email['date'][:10]}] {email['subject']}: {email.get('ai_summary', 'N/A')}\n"

        else:
            # Get overview of all proposals needing attention
            proposals = self.get_proposals_needing_attention()
            context_text = f"""
PROPOSALS NEEDING ATTENTION ({len(proposals)} total):
"""
            for p in proposals[:10]:
                context_text += f"- {p['project_code']}: {p['project_name']} - {p['attention_status']} ({p.get('urgent_emails', 0)} urgent)\n"

        prompt = f"""You are an AI assistant for Bensley Design Studios, helping answer questions about proposals.

CONTEXT:
{context_text}

QUESTION: {question}

Provide a helpful, concise answer based on the context. If you don't have enough information, say so.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for a design firm, answering questions about proposals and client communications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )

            answer = response.choices[0].message.content.strip()

            return {
                'success': True,
                'question': question,
                'answer': answer,
                'project_code': project_code,
                'context_used': bool(project_code)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _generate_proposal_summary(
        self,
        proposal: Dict,
        emails: List[Dict]
    ) -> str:
        """Generate an AI summary of proposal status and recent activity"""

        email_summaries = "\n".join([
            f"- [{e['date'][:10]}] {e.get('ai_summary', e['subject'])}"
            for e in emails[:5]
        ])

        prompt = f"""Summarize the current state of this proposal in 2-3 sentences:

PROJECT: {proposal['project_name']}
CLIENT: {proposal.get('client_company', 'Unknown')}
STATUS: {proposal.get('current_status', proposal.get('status', 'Unknown'))}
DAYS SINCE CONTACT: {proposal.get('days_since_contact', 'Unknown')}
EMAILS: {proposal.get('email_count', 0)} total, {proposal.get('urgent_emails', 0)} urgent

RECENT ACTIVITY:
{email_summaries}

Focus on: current status, any concerns, and recommended next steps.
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You summarize proposal status concisely for busy executives."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )

            return response.choices[0].message.content.strip()

        except Exception:
            return None

    def get_weekly_summary(self) -> Dict[str, Any]:
        """Generate a weekly summary of proposal activity"""

        # Get proposals with activity this week
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()

        active_proposals = self.execute_query("""
            SELECT
                pi.project_code,
                pi.project_name,
                pi.email_count,
                pi.urgent_emails,
                pi.attention_status,
                pi.latest_email_date,
                pi.current_status
            FROM proposal_intelligence pi
            WHERE pi.latest_email_date >= ?
            ORDER BY pi.email_count DESC
            LIMIT 15
        """, [week_ago])

        # Get new emails this week
        email_stats = self.execute_query("""
            SELECT
                COUNT(*) as total_emails,
                SUM(CASE WHEN ec.action_required = 1 THEN 1 ELSE 0 END) as action_needed,
                SUM(CASE WHEN ec.urgency_level IN ('high', 'critical') THEN 1 ELSE 0 END) as urgent,
                COUNT(DISTINCT ec.linked_project_code) as projects_touched
            FROM emails e
            JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.date >= ?
        """, [week_ago])

        return {
            'success': True,
            'week_start': week_ago[:10],
            'active_proposals': [dict(p) for p in active_proposals],
            'email_stats': dict(email_stats[0]) if email_stats else {},
            'generated_at': datetime.now().isoformat()
        }
