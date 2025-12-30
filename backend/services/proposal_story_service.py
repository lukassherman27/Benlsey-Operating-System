"""
Proposal Story Service - AI Story Builder (#141)

Generates a comprehensive "story" narrative for proposals by:
- Compiling all activities chronologically
- Highlighting key milestones and decisions
- Showing pending action items
- Providing sentiment trends over time

Used by the proposal detail page to tell Bill the complete story.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from .base_service import BaseService

import logging
logger = logging.getLogger(__name__)


class ProposalStoryService(BaseService):
    """Generate proposal stories from activity data."""

    def get_proposal_story(self, proposal_id: int) -> Dict[str, Any]:
        """
        Generate complete story for a proposal.

        Returns:
            - proposal: Basic proposal info
            - milestones: Key milestones in journey
            - timeline: Chronological activities with highlights
            - action_items: Pending and recent items
            - sentiment_trend: How sentiment has evolved
            - story_summary: AI-generated narrative summary
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get proposal basics
            cursor.execute("""
                SELECT
                    p.proposal_id,
                    p.project_code,
                    p.project_name,
                    p.client_company,
                    p.status,
                    p.project_value,
                    p.first_contact_date,
                    p.proposal_sent_date,
                    p.contract_signed_date,
                    p.health_score,
                    p.win_probability,
                    p.ball_in_court,
                    p.action_owner,
                    p.action_needed,
                    p.action_due,
                    p.last_sentiment,
                    p.days_since_contact
                FROM proposals p
                WHERE p.proposal_id = ?
            """, (proposal_id,))

            proposal_row = cursor.fetchone()
            if not proposal_row:
                return {'success': False, 'error': 'Proposal not found'}

            proposal = dict(proposal_row)

            # Get milestones
            cursor.execute("""
                SELECT
                    milestone_id,
                    milestone_type,
                    milestone_date,
                    description,
                    proposal_value_at_milestone,
                    created_by
                FROM proposal_milestones
                WHERE proposal_id = ?
                ORDER BY milestone_date ASC
            """, (proposal_id,))
            milestones = [dict(row) for row in cursor.fetchall()]

            # Get recent activities (last 30)
            cursor.execute("""
                SELECT
                    activity_id,
                    activity_type,
                    activity_date,
                    source_type,
                    source_id,
                    actor,
                    actor_email,
                    title,
                    summary,
                    sentiment,
                    extracted_dates,
                    extracted_actions,
                    extracted_decisions,
                    is_significant
                FROM proposal_activities
                WHERE proposal_id = ?
                ORDER BY activity_date DESC
                LIMIT 30
            """, (proposal_id,))
            activities = [dict(row) for row in cursor.fetchall()]

            # Parse JSON fields
            for activity in activities:
                for field in ['extracted_dates', 'extracted_actions', 'extracted_decisions']:
                    if activity.get(field):
                        try:
                            activity[field] = json.loads(activity[field])
                        except:
                            activity[field] = []

            # Get pending action items
            # Get pending action items from tasks table (unified action items)
            cursor.execute("""
                SELECT
                    task_id as action_id,
                    title as action_text,
                    category as action_category,
                    due_date,
                    assignee as assigned_to,
                    priority,
                    status,
                    created_at
                FROM tasks
                WHERE proposal_id = ? AND status = 'pending'
                ORDER BY
                    CASE priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    due_date ASC NULLS LAST
            """, (proposal_id,))
            pending_actions = [dict(row) for row in cursor.fetchall()]

            # Get completed action items from tasks table (last 10)
            cursor.execute("""
                SELECT
                    task_id as action_id,
                    title as action_text,
                    category as action_category,
                    completed_at,
                    description as completion_notes
                FROM tasks
                WHERE proposal_id = ? AND status = 'completed'
                ORDER BY completed_at DESC
                LIMIT 10
            """, (proposal_id,))
            completed_actions = [dict(row) for row in cursor.fetchall()]

            # Calculate sentiment trend
            sentiment_trend = self._calculate_sentiment_trend(activities)

            # Generate key highlights
            highlights = self._generate_highlights(proposal, milestones, activities)

            # Generate story summary
            story_summary = self._generate_story_summary(
                proposal, milestones, activities, pending_actions
            )

            return {
                'success': True,
                'proposal': proposal,
                'milestones': milestones,
                'timeline': activities,
                'action_items': {
                    'pending': pending_actions,
                    'pending_count': len(pending_actions),
                    'completed_recent': completed_actions
                },
                'sentiment_trend': sentiment_trend,
                'highlights': highlights,
                'story_summary': story_summary,
                'stats': {
                    'total_activities': len(activities),
                    'total_milestones': len(milestones),
                    'pending_actions': len(pending_actions)
                }
            }

    def get_proposal_story_by_code(self, project_code: str) -> Dict[str, Any]:
        """Get story by project code instead of ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT proposal_id FROM proposals WHERE project_code = ?",
                (project_code,)
            )
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': f'Proposal {project_code} not found'}
            return self.get_proposal_story(row[0])

    def _calculate_sentiment_trend(self, activities: List[Dict]) -> Dict[str, Any]:
        """Calculate how sentiment has evolved over time."""
        if not activities:
            return {'trend': 'neutral', 'data': []}

        # Group by week
        sentiment_map = {'positive': 1, 'neutral': 0, 'concerned': -1}
        weekly_data = {}

        for activity in activities:
            if activity.get('activity_date') and activity.get('sentiment'):
                try:
                    date = datetime.fromisoformat(activity['activity_date'][:10])
                    week_start = date - timedelta(days=date.weekday())
                    week_key = week_start.strftime('%Y-%m-%d')

                    if week_key not in weekly_data:
                        weekly_data[week_key] = []
                    weekly_data[week_key].append(
                        sentiment_map.get(activity['sentiment'], 0)
                    )
                except:
                    continue

        # Calculate weekly averages
        trend_data = []
        for week, scores in sorted(weekly_data.items()):
            avg = sum(scores) / len(scores)
            trend_data.append({
                'week': week,
                'score': round(avg, 2),
                'count': len(scores)
            })

        # Determine overall trend
        if len(trend_data) >= 2:
            recent = trend_data[-1]['score']
            earlier = trend_data[0]['score']
            if recent > earlier + 0.3:
                trend = 'improving'
            elif recent < earlier - 0.3:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'neutral'

        return {
            'trend': trend,
            'data': trend_data[-8:],  # Last 8 weeks
            'current': activities[0].get('sentiment') if activities else 'neutral'
        }

    def _generate_highlights(
        self,
        proposal: Dict,
        milestones: List[Dict],
        activities: List[Dict]
    ) -> List[Dict]:
        """Generate key highlights for the proposal."""
        highlights = []

        # Add milestone highlights
        for m in milestones:
            highlight_type = 'success' if m['milestone_type'] in (
                'contract_signed', 'proposal_sent', 'terms_agreed'
            ) else 'info'
            if m['milestone_type'] in ('lost', 'declined'):
                highlight_type = 'warning'

            highlights.append({
                'type': highlight_type,
                'date': m['milestone_date'],
                'title': self._format_milestone_title(m['milestone_type']),
                'description': m.get('description'),
                'source': 'milestone'
            })

        # Add significant activity highlights
        for a in activities:
            if a.get('is_significant'):
                highlights.append({
                    'type': 'info',
                    'date': a['activity_date'],
                    'title': a.get('title') or a['activity_type'],
                    'description': a.get('summary'),
                    'source': 'activity'
                })

            # Add decision highlights
            decisions = a.get('extracted_decisions') or []
            for decision in decisions[:2]:  # Max 2 per activity
                highlights.append({
                    'type': 'decision',
                    'date': a['activity_date'],
                    'title': 'Decision Made',
                    'description': decision,
                    'source': 'activity'
                })

        # Sort by date and limit
        highlights.sort(key=lambda x: x.get('date') or '', reverse=True)
        return highlights[:15]

    def _format_milestone_title(self, milestone_type: str) -> str:
        """Format milestone type for display."""
        titles = {
            'first_contact': 'First Contact',
            'meeting_scheduled': 'Meeting Scheduled',
            'meeting_held': 'Meeting Held',
            'proposal_requested': 'Proposal Requested',
            'proposal_sent': 'Proposal Sent',
            'proposal_revised': 'Proposal Revised',
            'negotiation_started': 'Negotiation Started',
            'terms_agreed': 'Terms Agreed',
            'contract_sent': 'Contract Sent',
            'contract_signed': 'Contract Signed - WON!',
            'lost': 'Deal Lost',
            'declined': 'We Declined',
            'on_hold': 'Put on Hold',
            'reactivated': 'Reactivated'
        }
        return titles.get(milestone_type, milestone_type.replace('_', ' ').title())

    def _generate_story_summary(
        self,
        proposal: Dict,
        milestones: List[Dict],
        activities: List[Dict],
        pending_actions: List[Dict]
    ) -> Dict[str, Any]:
        """Generate a narrative summary of the proposal journey."""
        summary = {
            'opening': '',
            'journey': '',
            'current_state': '',
            'next_steps': ''
        }

        project_name = proposal.get('project_name', 'This project')
        client_name = proposal.get('client_company', 'the client')
        status = proposal.get('status', 'In Progress')
        value = proposal.get('project_value')
        value_str = f"${value:,.0f}" if value else "undisclosed value"

        # Opening
        first_contact = proposal.get('first_contact_date')
        if first_contact:
            summary['opening'] = f"{project_name} with {client_name} ({value_str}) started on {first_contact}."
        else:
            summary['opening'] = f"{project_name} with {client_name} ({value_str})."

        # Journey
        milestone_count = len(milestones)
        activity_count = len(activities)
        if milestone_count > 0 or activity_count > 0:
            journey_parts = []
            if milestone_count > 0:
                journey_parts.append(f"{milestone_count} milestones reached")
            if activity_count > 0:
                journey_parts.append(f"{activity_count} recorded interactions")
            summary['journey'] = f"The journey includes {' and '.join(journey_parts)}."

        # Current state
        ball = proposal.get('ball_in_court', 'unknown')
        days_since = proposal.get('days_since_contact', 0)
        sentiment = proposal.get('last_sentiment', 'neutral')

        state_parts = [f"Currently in '{status}' status"]
        if ball == 'us':
            state_parts.append("ball is in our court")
        elif ball == 'them':
            state_parts.append("waiting on the client")

        if days_since and days_since > 0:
            state_parts.append(f"{days_since} days since last contact")

        summary['current_state'] = f"{', '.join(state_parts)}."

        if sentiment == 'concerned':
            summary['current_state'] += " Client sentiment appears concerned."
        elif sentiment == 'positive':
            summary['current_state'] += " Client sentiment is positive."

        # Next steps
        if pending_actions:
            action = pending_actions[0]
            action_text = action.get('action_text', 'Follow up')
            due = action.get('due_date')
            if due:
                summary['next_steps'] = f"Next action: {action_text} (due {due})."
            else:
                summary['next_steps'] = f"Next action: {action_text}."

            if len(pending_actions) > 1:
                summary['next_steps'] += f" Plus {len(pending_actions) - 1} more pending items."
        else:
            action_needed = proposal.get('action_needed')
            if action_needed:
                summary['next_steps'] = f"Next action: {action_needed}."
            else:
                summary['next_steps'] = "No pending action items."

        return summary

    def get_proposal_quick_summary(self, proposal_id: int) -> Dict[str, Any]:
        """
        Get a quick summary for hover cards or lists.
        Lighter weight than full story.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    p.project_code,
                    p.project_name,
                    p.status,
                    p.project_value,
                    p.ball_in_court,
                    p.action_needed,
                    p.last_sentiment,
                    p.days_since_contact,
                    (SELECT COUNT(*) FROM proposal_activities WHERE proposal_id = p.proposal_id) as activity_count,
                    (SELECT COUNT(*) FROM tasks WHERE proposal_id = p.proposal_id AND status = 'pending') as pending_count
                FROM proposals p
                WHERE p.proposal_id = ?
            """, (proposal_id,))

            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': 'Proposal not found'}

            return {
                'success': True,
                'summary': dict(row)
            }


def main():
    """CLI entry point."""
    import sys

    service = ProposalStoryService()

    if len(sys.argv) > 1:
        if sys.argv[1].isdigit():
            result = service.get_proposal_story(int(sys.argv[1]))
        else:
            result = service.get_proposal_story_by_code(sys.argv[1])
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python proposal_story_service.py <proposal_id or project_code>")


if __name__ == "__main__":
    main()
