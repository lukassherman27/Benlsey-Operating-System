"""
Follow-Up Agent Service

Intelligent agent that:
1. Identifies proposals needing follow-up based on communication patterns
2. Analyzes email sentiment and context to determine appropriate follow-up
3. Drafts personalized follow-up emails
4. Queues actions for approval
5. Learns from successful follow-up patterns

This is the first "agent" in the system - a specialized AI that takes autonomous action.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from openai import OpenAI

from .base_service import BaseService
from .ai_learning_service import AILearningService


class FollowUpAgent(BaseService):
    """Intelligent agent for proposal follow-up management"""

    def __init__(self, db_path: str = None):
        super().__init__(db_path)
        api_key = os.environ.get('OPENAI_API_KEY')
        self.ai_enabled = bool(api_key)
        if self.ai_enabled:
            self.client = OpenAI(api_key=api_key)
        self.learning_service = AILearningService(db_path)

    # =========================================================================
    # ANALYSIS
    # =========================================================================

    def get_proposals_needing_followup(
        self,
        days_threshold: int = 14,
        include_analysis: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all proposals that need follow-up with intelligent analysis.

        Enhanced version that includes:
        - Communication history analysis
        - Client sentiment from recent emails
        - Recommended follow-up approach
        - Priority scoring based on value and probability
        """
        proposals = self.execute_query("""
            SELECT
                p.proposal_id,
                p.project_code,
                p.project_name,
                p.client_company,
                p.contact_person,
                p.contact_email,
                p.status,
                p.last_contact_date,
                p.days_since_contact,
                p.next_action,
                p.next_action_date,
                p.project_value,
                p.win_probability,
                p.health_score,
                p.internal_notes
            FROM proposals p
            WHERE p.status IN ('proposal', 'negotiating', 'pending', 'submitted')
            AND (
                p.days_since_contact IS NULL
                OR p.days_since_contact >= ?
                OR (p.next_action_date IS NOT NULL AND date(p.next_action_date) <= date('now'))
            )
            ORDER BY
                CASE WHEN p.next_action_date IS NOT NULL AND date(p.next_action_date) <= date('now') THEN 0 ELSE 1 END,
                p.days_since_contact DESC NULLS LAST
            LIMIT ?
        """, [days_threshold, limit])

        proposals = [dict(p) for p in proposals]

        if include_analysis:
            for proposal in proposals:
                # Get communication history
                proposal['communication_history'] = self._get_communication_history(proposal['proposal_id'])

                # Calculate priority score
                proposal['priority_score'] = self._calculate_priority_score(proposal)

                # Get urgency category
                proposal['urgency'] = self._categorize_urgency(
                    proposal['days_since_contact'],
                    proposal['next_action_date']
                )

                # Get last email sentiment (if AI enabled)
                if self.ai_enabled and proposal['communication_history']:
                    proposal['last_email_sentiment'] = self._analyze_sentiment(proposal['communication_history'][-1])

        # Sort by priority score
        proposals.sort(key=lambda x: x.get('priority_score', 0), reverse=True)

        return proposals

    def _get_communication_history(self, proposal_id: int, limit: int = 10) -> List[Dict]:
        """Get recent email communication for a proposal"""
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
                ec.action_required
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE epl.proposal_id = ?
            ORDER BY e.date DESC
            LIMIT ?
        """, [proposal_id, limit])

        return [dict(e) for e in emails]

    def _calculate_priority_score(self, proposal: Dict) -> float:
        """
        Calculate priority score for a proposal (0-100).

        Factors:
        - Project value (higher = higher priority)
        - Win probability (higher = higher priority)
        - Days since contact (longer = higher priority)
        - Overdue action (yes = higher priority)
        - Health score (lower = higher priority)
        """
        score = 0

        # Value factor (up to 30 points)
        value = proposal.get('project_value') or 0
        if value >= 1000000:
            score += 30
        elif value >= 500000:
            score += 25
        elif value >= 200000:
            score += 20
        elif value >= 100000:
            score += 15
        elif value >= 50000:
            score += 10
        else:
            score += 5

        # Win probability factor (up to 20 points)
        prob = proposal.get('win_probability') or 50
        if prob >= 80:
            score += 20
        elif prob >= 60:
            score += 15
        elif prob >= 40:
            score += 10
        else:
            score += 5

        # Days since contact factor (up to 25 points)
        days = proposal.get('days_since_contact')
        if days is None:
            score += 25  # No contact recorded = high priority
        elif days >= 90:
            score += 25
        elif days >= 60:
            score += 20
        elif days >= 30:
            score += 15
        elif days >= 14:
            score += 10
        else:
            score += 5

        # Overdue action factor (up to 15 points)
        next_action_date = proposal.get('next_action_date')
        if next_action_date:
            try:
                action_date = datetime.fromisoformat(next_action_date).date()
                if action_date <= datetime.now().date():
                    score += 15
            except:
                pass

        # Health score factor (up to 10 points)
        health = proposal.get('health_score') or 50
        if health < 30:
            score += 10
        elif health < 50:
            score += 7
        elif health < 70:
            score += 5
        else:
            score += 2

        return min(100, score)

    def _categorize_urgency(self, days_since_contact: int, next_action_date: str) -> str:
        """Categorize follow-up urgency"""
        today = datetime.now().date()

        if next_action_date:
            try:
                action_date = datetime.fromisoformat(next_action_date).date()
                if action_date <= today:
                    return "overdue_action"
            except:
                pass

        if days_since_contact is None:
            return "no_contact"
        elif days_since_contact >= 90:
            return "critical"
        elif days_since_contact >= 60:
            return "urgent"
        elif days_since_contact >= 30:
            return "high"
        elif days_since_contact >= 14:
            return "medium"
        else:
            return "low"

    def _analyze_sentiment(self, email: Dict) -> str:
        """Analyze sentiment of last email"""
        # Simple heuristic analysis (can be enhanced with AI)
        summary = (email.get('ai_summary') or '').lower()
        urgency = email.get('urgency_level')

        if urgency == 'critical':
            return 'urgent'
        if any(word in summary for word in ['problem', 'issue', 'delay', 'concern', 'waiting']):
            return 'concerned'
        if any(word in summary for word in ['thank', 'great', 'excited', 'pleased', 'looking forward']):
            return 'positive'
        if email.get('action_required'):
            return 'awaiting_response'

        return 'neutral'

    # =========================================================================
    # FOLLOW-UP DRAFTING
    # =========================================================================

    def draft_follow_up_email(
        self,
        proposal_id: int,
        tone: str = 'professional',
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Draft a personalized follow-up email using AI.

        Args:
            proposal_id: The proposal to follow up on
            tone: 'professional', 'casual', 'formal'
            include_context: Whether to include email history in draft

        Returns:
            Draft email with subject and body
        """
        if not self.ai_enabled:
            return {'error': 'AI not enabled - cannot draft emails'}

        # Get proposal details
        proposal = self.execute_query("""
            SELECT
                p.*,
                COUNT(DISTINCT e.email_id) as email_count
            FROM proposals p
            LEFT JOIN email_proposal_links epl ON p.proposal_id = epl.proposal_id
            LEFT JOIN emails e ON epl.email_id = e.email_id
            WHERE p.proposal_id = ?
            GROUP BY p.proposal_id
        """, [proposal_id])

        if not proposal:
            return {'error': 'Proposal not found'}

        proposal = dict(proposal[0])

        # Get communication history
        history = self._get_communication_history(proposal_id, limit=5)

        # Get learned patterns for this client
        patterns = self._get_client_patterns(proposal.get('client_company'))

        # Build context for AI
        context = self._build_email_context(proposal, history, patterns)

        # Generate draft with AI
        draft = self._generate_email_draft(context, tone)

        # Queue as action for approval
        if draft and 'error' not in draft:
            self._queue_follow_up_action(proposal_id, draft)

        return draft

    def _get_client_patterns(self, client_company: str) -> List[Dict]:
        """Get learned communication patterns for a client"""
        if not client_company:
            return []

        patterns = self.learning_service.get_learned_patterns(
            pattern_type='communication_style',
            active_only=True
        )

        # Filter for this client
        client_patterns = []
        for p in patterns:
            condition = p.get('condition', {})
            if condition.get('client_company') == client_company or not condition.get('client_company'):
                client_patterns.append(p)

        return client_patterns

    def _build_email_context(
        self,
        proposal: Dict,
        history: List[Dict],
        patterns: List[Dict]
    ) -> str:
        """Build context string for AI email generation"""
        context_parts = []

        # Proposal info
        context_parts.append(f"Proposal: {proposal.get('project_code')} - {proposal.get('project_name')}")
        context_parts.append(f"Client: {proposal.get('client_company')}")
        context_parts.append(f"Contact: {proposal.get('contact_person')} ({proposal.get('contact_email')})")
        context_parts.append(f"Value: ${proposal.get('project_value', 0):,.0f}")
        context_parts.append(f"Status: {proposal.get('status')}")

        if proposal.get('days_since_contact'):
            context_parts.append(f"Days since last contact: {proposal['days_since_contact']}")

        if proposal.get('next_action'):
            context_parts.append(f"Pending action: {proposal['next_action']}")

        # Recent email history
        if history:
            context_parts.append("\nRecent communication:")
            for email in history[:3]:
                direction = "Sent" if email.get('folder') in ('Sent', 'SENT') else "Received"
                context_parts.append(f"- {direction}: {email.get('subject')} ({email.get('date', '')[:10]})")
                if email.get('ai_summary'):
                    context_parts.append(f"  Summary: {email['ai_summary'][:100]}")

        # Learned patterns
        if patterns:
            context_parts.append("\nCommunication preferences:")
            for p in patterns[:2]:
                action = p.get('action', {})
                if action.get('tone'):
                    context_parts.append(f"- Preferred tone: {action['tone']}")
                if action.get('sign_off'):
                    context_parts.append(f"- Sign off: {action['sign_off']}")

        return "\n".join(context_parts)

    def _generate_email_draft(self, context: str, tone: str) -> Dict[str, str]:
        """Use AI to generate email draft"""
        try:
            system_prompt = f"""You are drafting a follow-up email for a landscape architecture proposal.

Tone: {tone}
Keep the email:
- Concise (3-5 sentences max)
- Professional but warm
- Focused on moving the project forward
- Not pushy or desperate

Return JSON with:
{{"subject": "subject line", "body": "email body"}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Draft a follow-up email based on this context:\n\n{context}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            result = json.loads(response.choices[0].message.content)
            result['context_used'] = context
            result['generated_at'] = datetime.now().isoformat()

            return result

        except Exception as e:
            return {'error': str(e)}

    def _queue_follow_up_action(self, proposal_id: int, draft: Dict):
        """Queue the follow-up email for approval"""
        proposal = self.execute_query("""
            SELECT project_code FROM proposals WHERE proposal_id = ?
        """, [proposal_id])

        project_code = proposal[0]['project_code'] if proposal else None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_action_queue (
                    action_type, action_data, requires_approval,
                    triggered_by, project_code, status, created_at
                ) VALUES (
                    'send_email', ?, 1,
                    ?, ?, 'pending', datetime('now')
                )
            """, (
                json.dumps(draft),
                f"follow_up_agent:proposal_{proposal_id}",
                project_code
            ))
            conn.commit()

    # =========================================================================
    # BATCH PROCESSING
    # =========================================================================

    def run_daily_analysis(self) -> Dict[str, Any]:
        """
        Run daily follow-up analysis for all proposals.

        This should be run once per day to:
        1. Identify new proposals needing follow-up
        2. Generate suggestions for the learning system
        3. Draft follow-up emails for critical cases
        """
        results = {
            'proposals_analyzed': 0,
            'follow_ups_needed': 0,
            'critical_proposals': 0,
            'emails_drafted': 0,
            'suggestions_created': 0
        }

        # Get all proposals needing follow-up
        proposals = self.get_proposals_needing_followup(
            days_threshold=7,  # More aggressive for daily analysis
            include_analysis=True
        )

        results['proposals_analyzed'] = len(proposals)

        for proposal in proposals:
            urgency = proposal.get('urgency')

            if urgency in ('critical', 'urgent', 'overdue_action'):
                results['critical_proposals'] += 1

                # Create suggestion in learning system
                self._create_follow_up_suggestion(proposal)
                results['suggestions_created'] += 1

                # Draft email for critical cases
                if self.ai_enabled:
                    draft = self.draft_follow_up_email(proposal['proposal_id'])
                    if 'error' not in draft:
                        results['emails_drafted'] += 1

            elif urgency in ('high', 'medium'):
                results['follow_ups_needed'] += 1

                # Create suggestion
                self._create_follow_up_suggestion(proposal)
                results['suggestions_created'] += 1

        return results

    def _create_follow_up_suggestion(self, proposal: Dict):
        """Create a follow-up suggestion in the learning system"""
        urgency = proposal.get('urgency', 'medium')
        priority_map = {
            'critical': 'critical',
            'urgent': 'high',
            'overdue_action': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        }

        priority = priority_map.get(urgency, 'medium')

        # Calculate confidence based on data quality
        confidence = 0.7
        if proposal.get('email_count', 0) > 5:
            confidence += 0.1
        if proposal.get('last_contact_date'):
            confidence += 0.1

        suggestion_data = {
            'proposal_id': proposal['proposal_id'],
            'project_code': proposal['project_code'],
            'days_since_contact': proposal.get('days_since_contact'),
            'urgency': urgency,
            'priority_score': proposal.get('priority_score', 50),
            'suggested_approach': self._get_suggested_approach(urgency)
        }

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO ai_suggestions (
                    suggestion_type, priority, confidence_score,
                    source_type, source_id, source_reference,
                    title, description, suggested_action,
                    suggested_data, target_table, project_code,
                    proposal_id, status, created_at
                ) VALUES (
                    'follow_up_needed', ?, ?,
                    'pattern', ?, ?,
                    ?, ?, 'Send follow-up email',
                    ?, 'proposals', ?, ?, 'pending', datetime('now')
                )
            """, (
                priority,
                confidence,
                proposal['proposal_id'],
                f"Proposal {proposal['project_code']} - {proposal['days_since_contact'] or 'N/A'} days silent",
                f"Follow up on {proposal['project_code']}",
                self._get_follow_up_description(proposal),
                json.dumps(suggestion_data),
                proposal['project_code'],
                proposal['proposal_id']
            ))
            conn.commit()

    def _get_suggested_approach(self, urgency: str) -> str:
        """Get suggested follow-up approach based on urgency"""
        approaches = {
            'critical': 'Call client directly to check status',
            'urgent': 'Send direct follow-up email and consider calling',
            'overdue_action': 'Complete scheduled action immediately',
            'high': 'Send friendly follow-up email',
            'medium': 'Send check-in email',
            'low': 'Monitor for now'
        }
        return approaches.get(urgency, 'Send follow-up email')

    def _get_follow_up_description(self, proposal: Dict) -> str:
        """Generate description for follow-up suggestion"""
        days = proposal.get('days_since_contact')
        value = proposal.get('project_value', 0)
        urgency = proposal.get('urgency', 'medium')

        parts = []

        if days:
            parts.append(f"No contact for {days} days")
        else:
            parts.append("No contact recorded")

        if value:
            parts.append(f"Value: ${value:,.0f}")

        if proposal.get('next_action'):
            parts.append(f"Pending: {proposal['next_action']}")

        return ". ".join(parts)

    # =========================================================================
    # FOLLOW-UP SUMMARY
    # =========================================================================

    def get_follow_up_summary(self) -> Dict[str, Any]:
        """Get summary of follow-up status across all proposals"""
        summary = {
            'total_active_proposals': 0,
            'needing_follow_up': 0,
            'by_urgency': {},
            'value_at_risk': 0,
            'top_priority': [],
            'overdue_actions': []
        }

        # Get total active proposals
        total = self.execute_query("""
            SELECT COUNT(*) as count FROM proposals
            WHERE status IN ('proposal', 'negotiating', 'pending', 'submitted')
        """, [])
        summary['total_active_proposals'] = total[0]['count'] if total else 0

        # Get proposals needing follow-up
        proposals = self.get_proposals_needing_followup(
            days_threshold=14,
            include_analysis=True,
            limit=100
        )

        summary['needing_follow_up'] = len(proposals)

        # Group by urgency
        for p in proposals:
            urgency = p.get('urgency', 'medium')
            if urgency not in summary['by_urgency']:
                summary['by_urgency'][urgency] = {'count': 0, 'value': 0}
            summary['by_urgency'][urgency]['count'] += 1
            project_value = p.get('project_value') or 0
            summary['by_urgency'][urgency]['value'] += project_value

            # Track value at risk
            summary['value_at_risk'] += project_value

            # Track overdue actions
            if urgency == 'overdue_action':
                summary['overdue_actions'].append({
                    'project_code': p['project_code'],
                    'action': p.get('next_action'),
                    'due_date': p.get('next_action_date')
                })

        # Get top priority
        summary['top_priority'] = [
            {
                'project_code': p['project_code'],
                'project_name': p['project_name'],
                'client': p['client_company'],
                'value': p.get('project_value', 0),
                'urgency': p.get('urgency'),
                'priority_score': p.get('priority_score', 0)
            }
            for p in proposals[:5]
        ]

        return summary
