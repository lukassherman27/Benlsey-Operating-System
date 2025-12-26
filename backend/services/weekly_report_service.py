"""
Weekly Report Service - Visual summary for Bill (#142)

Generates comprehensive weekly reports with:
- Week in Review: new proposals, won/lost, status changes
- Attention Required: overdue, stale, at-risk
- Pipeline Outlook: totals, weighted values, trends
- Activity Summary: emails, meetings, actions
- Financial Connection: expected revenue, cash flow

Used by:
- Web Dashboard at /overview/weekly
- Automated Monday morning email
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .base_service import BaseService

import logging
logger = logging.getLogger(__name__)


class WeeklyReportService(BaseService):
    """Generate weekly proposal reports for Bill."""

    def generate_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete weekly report.

        Args:
            start_date: Start of report period (defaults to last Monday)
            end_date: End of report period (defaults to today)

        Returns:
            Complete report with all sections
        """
        # Default to last week (Monday to Sunday)
        today = datetime.now()
        if not end_date:
            end_date = today.strftime('%Y-%m-%d')
        if not start_date:
            # Last Monday
            days_since_monday = today.weekday()
            if days_since_monday == 0:  # Today is Monday
                days_since_monday = 7  # Go back to last Monday
            last_monday = today - timedelta(days=days_since_monday)
            start_date = last_monday.strftime('%Y-%m-%d')

        with self.get_connection() as conn:
            cursor = conn.cursor()

            report = {
                'period': {
                    'start': start_date,
                    'end': end_date,
                    'generated_at': today.isoformat()
                },
                'week_in_review': self._get_week_in_review(cursor, start_date, end_date),
                'attention_required': self._get_attention_required(cursor),
                'pipeline_outlook': self._get_pipeline_outlook(cursor),
                'activity_summary': self._get_activity_summary(cursor, start_date, end_date),
                'top_opportunities': self._get_top_opportunities(cursor),
                'stalled_proposals': self._get_stalled_proposals(cursor)
            }

            return report

    def _get_week_in_review(
        self,
        cursor,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Get what happened this week."""
        # New proposals
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(project_value), 0)
            FROM proposals
            WHERE first_contact_date >= ? AND first_contact_date <= ?
        """, (start_date, end_date))
        new_count, new_value = cursor.fetchone()

        # Won proposals
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(project_value), 0)
            FROM proposals
            WHERE contract_signed_date >= ? AND contract_signed_date <= ?
        """, (start_date, end_date))
        won_count, won_value = cursor.fetchone()

        # Lost proposals
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(project_value), 0)
            FROM proposals
            WHERE status = 'Lost'
            AND updated_at >= ? AND updated_at <= ?
        """, (start_date, end_date))
        lost_count, lost_value = cursor.fetchone()

        # Status changes (milestones created this week)
        cursor.execute("""
            SELECT
                pm.milestone_type,
                COUNT(*) as cnt,
                p.project_code,
                p.project_name
            FROM proposal_milestones pm
            JOIN proposals p ON pm.proposal_id = p.proposal_id
            WHERE pm.created_at >= ? AND pm.created_at <= ?
            GROUP BY pm.milestone_type
            ORDER BY cnt DESC
        """, (start_date, end_date))
        status_changes = [dict(row) for row in cursor.fetchall()]

        # Key proposals that advanced
        cursor.execute("""
            SELECT DISTINCT
                p.project_code,
                p.project_name,
                p.status,
                p.project_value,
                pm.milestone_type
            FROM proposal_milestones pm
            JOIN proposals p ON pm.proposal_id = p.proposal_id
            WHERE pm.created_at >= ? AND pm.created_at <= ?
            ORDER BY p.project_value DESC
            LIMIT 5
        """, (start_date, end_date))
        advanced_proposals = [dict(row) for row in cursor.fetchall()]

        return {
            'new_proposals': {
                'count': new_count or 0,
                'value': new_value or 0
            },
            'won': {
                'count': won_count or 0,
                'value': won_value or 0
            },
            'lost': {
                'count': lost_count or 0,
                'value': lost_value or 0
            },
            'status_changes': status_changes,
            'advanced_proposals': advanced_proposals
        }

    def _get_attention_required(self, cursor) -> Dict[str, Any]:
        """Get items needing attention."""
        today = datetime.now().strftime('%Y-%m-%d')

        # Overdue follow-ups
        cursor.execute("""
            SELECT
                project_code,
                project_name,
                project_value,
                action_needed,
                action_due,
                action_owner,
                julianday(?) - julianday(action_due) as days_overdue
            FROM proposals
            WHERE action_due < ?
            AND status NOT IN ('Contract Signed', 'Lost', 'Declined', 'On Hold')
            ORDER BY project_value DESC
            LIMIT 10
        """, (today, today))
        overdue = [dict(row) for row in cursor.fetchall()]

        # Stale proposals (14+ days no activity)
        # Use dynamic calculation instead of stored days_since_contact
        cursor.execute("""
            SELECT
                project_code,
                project_name,
                project_value,
                status,
                CAST(JULIANDAY('now') - JULIANDAY(COALESCE(last_contact_date, created_at)) AS INTEGER) as days_since_contact,
                last_contact_date
            FROM proposals
            WHERE CAST(JULIANDAY('now') - JULIANDAY(COALESCE(last_contact_date, created_at)) AS INTEGER) >= 14
            AND status NOT IN ('Contract Signed', 'Lost', 'Declined', 'On Hold')
            ORDER BY days_since_contact DESC
            LIMIT 10
        """)
        stale = [dict(row) for row in cursor.fetchall()]

        # At-risk (health score < 50 or declining sentiment)
        cursor.execute("""
            SELECT
                project_code,
                project_name,
                project_value,
                status,
                health_score,
                last_sentiment,
                ball_in_court
            FROM proposals
            WHERE (health_score < 50 OR last_sentiment = 'concerned')
            AND status NOT IN ('Contract Signed', 'Lost', 'Declined', 'On Hold')
            ORDER BY project_value DESC
            LIMIT 10
        """)
        at_risk = [dict(row) for row in cursor.fetchall()]

        return {
            'overdue': overdue,
            'overdue_count': len(overdue),
            'overdue_value': sum(p.get('project_value', 0) or 0 for p in overdue),
            'stale': stale,
            'stale_count': len(stale),
            'at_risk': at_risk,
            'at_risk_count': len(at_risk),
            'at_risk_value': sum(p.get('project_value', 0) or 0 for p in at_risk)
        }

    def _get_pipeline_outlook(self, cursor) -> Dict[str, Any]:
        """Get pipeline metrics and trends."""
        # Active pipeline
        cursor.execute("""
            SELECT
                COUNT(*) as count,
                COALESCE(SUM(project_value), 0) as total_value,
                COALESCE(SUM(project_value * COALESCE(win_probability, 50) / 100), 0) as weighted_value
            FROM proposals
            WHERE status NOT IN ('Contract Signed', 'Lost', 'Declined')
        """)
        pipeline = dict(cursor.fetchone())

        # By status
        cursor.execute("""
            SELECT
                status,
                COUNT(*) as count,
                COALESCE(SUM(project_value), 0) as value
            FROM proposals
            WHERE status NOT IN ('Contract Signed', 'Lost', 'Declined')
            GROUP BY status
            ORDER BY COUNT(*) DESC
        """)
        by_status = [dict(row) for row in cursor.fetchall()]

        # Win rate (last 3 months)
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM proposals
                 WHERE contract_signed_date >= date('now', '-3 months')) as won,
                (SELECT COUNT(*) FROM proposals
                 WHERE (contract_signed_date >= date('now', '-3 months')
                    OR (status = 'Lost' AND updated_at >= date('now', '-3 months')))) as total
        """)
        win_data = dict(cursor.fetchone())
        win_rate = (win_data['won'] / win_data['total'] * 100) if win_data['total'] > 0 else 0

        # Previous 3 months win rate for comparison
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM proposals
                 WHERE contract_signed_date >= date('now', '-6 months')
                   AND contract_signed_date < date('now', '-3 months')) as won,
                (SELECT COUNT(*) FROM proposals
                 WHERE ((contract_signed_date >= date('now', '-6 months') AND contract_signed_date < date('now', '-3 months'))
                    OR (status = 'Lost' AND updated_at >= date('now', '-6 months') AND updated_at < date('now', '-3 months')))) as total
        """)
        prev_data = dict(cursor.fetchone())
        prev_win_rate = (prev_data['won'] / prev_data['total'] * 100) if prev_data['total'] > 0 else 0

        # Ball in court breakdown
        cursor.execute("""
            SELECT
                ball_in_court,
                COUNT(*) as count,
                COALESCE(SUM(project_value), 0) as value
            FROM proposals
            WHERE status NOT IN ('Contract Signed', 'Lost', 'Declined')
            GROUP BY ball_in_court
        """)
        by_ball = [dict(row) for row in cursor.fetchall()]

        return {
            'total_pipeline': pipeline['total_value'],
            'weighted_pipeline': pipeline['weighted_value'],
            'proposal_count': pipeline['count'],
            'by_status': by_status,
            'by_ball': by_ball,
            'win_rate': {
                'current': round(win_rate, 1),
                'previous': round(prev_win_rate, 1),
                'trend': 'up' if win_rate > prev_win_rate else ('down' if win_rate < prev_win_rate else 'stable')
            }
        }

    def _get_activity_summary(
        self,
        cursor,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Get activity metrics for the period."""
        # Email activity
        cursor.execute("""
            SELECT
                activity_type,
                COUNT(*) as count
            FROM proposal_activities
            WHERE activity_date >= ? AND activity_date <= ?
            GROUP BY activity_type
        """, (start_date, end_date))
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        # Top proposals by activity
        cursor.execute("""
            SELECT
                p.project_code,
                p.project_name,
                COUNT(*) as activity_count
            FROM proposal_activities pa
            JOIN proposals p ON pa.proposal_id = p.proposal_id
            WHERE pa.activity_date >= ? AND pa.activity_date <= ?
            GROUP BY pa.proposal_id
            ORDER BY activity_count DESC
            LIMIT 5
        """, (start_date, end_date))
        most_active = [dict(row) for row in cursor.fetchall()]

        # Action items
        cursor.execute("""
            SELECT COUNT(*) FROM proposal_action_items
            WHERE created_at >= ? AND created_at <= ?
        """, (start_date, end_date))
        items_created = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM proposal_action_items
            WHERE completed_at >= ? AND completed_at <= ?
        """, (start_date, end_date))
        items_completed = cursor.fetchone()[0]

        return {
            'emails_sent': by_type.get('email_sent', 0),
            'emails_received': by_type.get('email_received', 0),
            'meetings': by_type.get('meeting', 0),
            'total_activities': sum(by_type.values()),
            'most_active_proposals': most_active,
            'action_items': {
                'created': items_created,
                'completed': items_completed
            }
        }

    def _get_top_opportunities(self, cursor, limit: int = 5) -> List[Dict]:
        """Get top opportunities by value and probability."""
        cursor.execute("""
            SELECT
                project_code,
                project_name,
                project_value,
                status,
                win_probability,
                health_score,
                ball_in_court,
                action_needed
            FROM proposals
            WHERE status NOT IN ('Contract Signed', 'Lost', 'Declined', 'On Hold')
            AND project_value IS NOT NULL
            ORDER BY project_value * COALESCE(win_probability, 50) / 100 DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def _get_stalled_proposals(self, cursor, days: int = 14, limit: int = 5) -> List[Dict]:
        """Get proposals with no activity for X days."""
        # Use dynamic calculation instead of stored days_since_contact
        cursor.execute("""
            SELECT
                project_code,
                project_name,
                project_value,
                status,
                CAST(JULIANDAY('now') - JULIANDAY(COALESCE(last_contact_date, created_at)) AS INTEGER) as days_since_contact,
                last_contact_date,
                ball_in_court
            FROM proposals
            WHERE CAST(JULIANDAY('now') - JULIANDAY(COALESCE(last_contact_date, created_at)) AS INTEGER) >= ?
            AND status NOT IN ('Contract Signed', 'Lost', 'Declined', 'On Hold')
            ORDER BY project_value DESC
            LIMIT ?
        """, (days, limit))
        return [dict(row) for row in cursor.fetchall()]

    def get_quick_stats(self) -> Dict[str, Any]:
        """Get quick stats for dashboard card."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Active pipeline
            cursor.execute("""
                SELECT
                    COUNT(*) as count,
                    COALESCE(SUM(project_value), 0) as value
                FROM proposals
                WHERE status NOT IN ('Contract Signed', 'Lost', 'Declined')
            """)
            pipeline = dict(cursor.fetchone())

            # Overdue
            cursor.execute("""
                SELECT COUNT(*)
                FROM proposals
                WHERE action_due < date('now')
                AND status NOT IN ('Contract Signed', 'Lost', 'Declined', 'On Hold')
            """)
            overdue = cursor.fetchone()[0]

            # Our move
            cursor.execute("""
                SELECT COUNT(*)
                FROM proposals
                WHERE ball_in_court = 'us'
                AND status NOT IN ('Contract Signed', 'Lost', 'Declined', 'On Hold')
            """)
            our_move = cursor.fetchone()[0]

            return {
                'pipeline_value': pipeline['value'],
                'pipeline_count': pipeline['count'],
                'overdue_count': overdue,
                'our_move_count': our_move
            }

    def generate_html_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Generate beautiful HTML weekly report for Bill.

        Returns:
            Complete HTML document ready to send via email or save as file
        """
        # Get the data
        report = self.generate_report(start_date, end_date)

        # Format currency
        def fmt_money(val):
            if val is None:
                return "$0"
            if val >= 1000000:
                return f"${val/1000000:.1f}M"
            elif val >= 1000:
                return f"${val/1000:.0f}K"
            return f"${val:,.0f}"

        # Format date
        def fmt_date(d):
            if not d:
                return "—"
            try:
                return datetime.strptime(d, '%Y-%m-%d').strftime('%b %d')
            except:
                return d

        # Build sections
        period = report['period']
        week_review = report['week_in_review']
        attention = report['attention_required']
        pipeline = report['pipeline_outlook']
        top_opps = report['top_opportunities']
        stalled = report['stalled_proposals']

        # Calculate some insights
        total_at_risk_value = attention.get('at_risk_value', 0) + attention.get('overdue_value', 0)
        win_rate = pipeline.get('win_rate', {})
        win_trend = win_rate.get('trend', 'stable')
        win_emoji = "📈" if win_trend == 'up' else ("📉" if win_trend == 'down' else "➡️")

        # Build top opportunities HTML
        top_opps_html = ""
        for i, opp in enumerate(top_opps[:5], 1):
            prob = opp.get('win_probability') or 50
            health = opp.get('health_score') or 50
            health_color = "#22c55e" if health >= 70 else ("#f59e0b" if health >= 40 else "#ef4444")
            top_opps_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0;">
                    <strong>{opp.get('project_code', '')}</strong><br>
                    <span style="color: #64748b; font-size: 13px;">{opp.get('project_name', '')[:40]}</span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: right;">
                    <strong style="color: #0f172a;">{fmt_money(opp.get('project_value', 0))}</strong>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: center;">
                    <span style="background: #dbeafe; color: #1e40af; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{prob}%</span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #e2e8f0; text-align: center;">
                    <span style="color: {health_color}; font-weight: 600;">{health}</span>
                </td>
            </tr>
            """

        # Build attention items HTML
        attention_html = ""
        for item in attention.get('overdue', [])[:5]:
            days = int(item.get('days_overdue', 0))
            attention_html += f"""
            <tr style="background: #fef2f2;">
                <td style="padding: 10px; border-bottom: 1px solid #fecaca;">
                    <span style="background: #ef4444; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">OVERDUE {days}d</span>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #fecaca;">
                    <strong>{item.get('project_code', '')}</strong> — {item.get('project_name', '')[:30]}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #fecaca; color: #64748b; font-size: 13px;">
                    {item.get('action_needed', 'Follow up needed')[:40]}
                </td>
            </tr>
            """

        for item in attention.get('stale', [])[:3]:
            days = int(item.get('days_since_contact', 0))
            attention_html += f"""
            <tr style="background: #fffbeb;">
                <td style="padding: 10px; border-bottom: 1px solid #fde68a;">
                    <span style="background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">STALE {days}d</span>
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #fde68a;">
                    <strong>{item.get('project_code', '')}</strong> — {item.get('project_name', '')[:30]}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #fde68a; color: #64748b; font-size: 13px;">
                    Last contact: {fmt_date(item.get('last_contact_date'))}
                </td>
            </tr>
            """

        # Build pipeline by status
        status_html = ""
        for status in pipeline.get('by_status', []):
            status_html += f"""
            <div style="display: inline-block; margin: 8px; padding: 12px 16px; background: #f8fafc; border-radius: 8px; text-align: center; min-width: 100px;">
                <div style="font-size: 24px; font-weight: 700; color: #0f172a;">{status.get('count', 0)}</div>
                <div style="font-size: 12px; color: #64748b;">{status.get('status', 'Unknown')}</div>
                <div style="font-size: 13px; color: #3b82f6; font-weight: 600;">{fmt_money(status.get('value', 0))}</div>
            </div>
            """

        # Build the full HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bensley Weekly Proposal Report</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f1f5f9;">
    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); border-radius: 16px; padding: 32px; margin-bottom: 24px; color: white;">
            <h1 style="margin: 0 0 8px 0; font-size: 28px; font-weight: 700;">Weekly Proposal Report</h1>
            <p style="margin: 0; opacity: 0.9; font-size: 15px;">
                {fmt_date(period['start'])} — {fmt_date(period['end'])} | Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </div>

        <!-- Key Metrics -->
        <div style="display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 150px; background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 32px; font-weight: 700; color: #0f172a;">{fmt_money(pipeline.get('total_pipeline', 0))}</div>
                <div style="font-size: 14px; color: #64748b;">Active Pipeline</div>
                <div style="font-size: 13px; color: #3b82f6; margin-top: 4px;">{pipeline.get('proposal_count', 0)} proposals</div>
            </div>
            <div style="flex: 1; min-width: 150px; background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 32px; font-weight: 700; color: #22c55e;">{fmt_money(pipeline.get('weighted_pipeline', 0))}</div>
                <div style="font-size: 14px; color: #64748b;">Weighted Pipeline</div>
                <div style="font-size: 13px; color: #64748b; margin-top: 4px;">Value × Probability</div>
            </div>
            <div style="flex: 1; min-width: 150px; background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 32px; font-weight: 700; color: #8b5cf6;">{win_rate.get('current', 0):.0f}%</div>
                <div style="font-size: 14px; color: #64748b;">Win Rate (3mo)</div>
                <div style="font-size: 13px; margin-top: 4px;">{win_emoji} {win_rate.get('trend', 'stable')}</div>
            </div>
        </div>

        <!-- This Week -->
        <div style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <h2 style="margin: 0 0 16px 0; font-size: 18px; color: #0f172a;">📅 This Week</h2>
            <div style="display: flex; gap: 24px; flex-wrap: wrap;">
                <div style="text-align: center; padding: 16px 24px; background: #f0fdf4; border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: 700; color: #16a34a;">+{week_review['new_proposals']['count']}</div>
                    <div style="font-size: 13px; color: #64748b;">New Proposals</div>
                    <div style="font-size: 14px; color: #16a34a; font-weight: 600;">{fmt_money(week_review['new_proposals']['value'])}</div>
                </div>
                <div style="text-align: center; padding: 16px 24px; background: #ecfdf5; border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: 700; color: #059669;">🎉 {week_review['won']['count']}</div>
                    <div style="font-size: 13px; color: #64748b;">Won</div>
                    <div style="font-size: 14px; color: #059669; font-weight: 600;">{fmt_money(week_review['won']['value'])}</div>
                </div>
                <div style="text-align: center; padding: 16px 24px; background: #fef2f2; border-radius: 8px;">
                    <div style="font-size: 28px; font-weight: 700; color: #dc2626;">{week_review['lost']['count']}</div>
                    <div style="font-size: 13px; color: #64748b;">Lost</div>
                    <div style="font-size: 14px; color: #dc2626; font-weight: 600;">{fmt_money(week_review['lost']['value'])}</div>
                </div>
            </div>
        </div>

        <!-- Attention Required -->
        {f'''
        <div style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #ef4444;">
            <h2 style="margin: 0 0 16px 0; font-size: 18px; color: #0f172a;">🚨 Attention Required</h2>
            <p style="margin: 0 0 16px 0; color: #64748b; font-size: 14px;">
                {attention.get('overdue_count', 0)} overdue ({fmt_money(attention.get('overdue_value', 0))}) •
                {attention.get('stale_count', 0)} stale •
                {attention.get('at_risk_count', 0)} at risk ({fmt_money(attention.get('at_risk_value', 0))})
            </p>
            <table style="width: 100%; border-collapse: collapse;">
                {attention_html}
            </table>
        </div>
        ''' if attention_html else ''}

        <!-- Top Opportunities -->
        <div style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <h2 style="margin: 0 0 16px 0; font-size: 18px; color: #0f172a;">🎯 Top Opportunities</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8fafc;">
                        <th style="padding: 12px; text-align: left; font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">Project</th>
                        <th style="padding: 12px; text-align: right; font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">Value</th>
                        <th style="padding: 12px; text-align: center; font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">Win %</th>
                        <th style="padding: 12px; text-align: center; font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">Health</th>
                    </tr>
                </thead>
                <tbody>
                    {top_opps_html}
                </tbody>
            </table>
        </div>

        <!-- Pipeline by Status -->
        <div style="background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <h2 style="margin: 0 0 16px 0; font-size: 18px; color: #0f172a;">📊 Pipeline by Status</h2>
            <div style="text-align: center;">
                {status_html}
            </div>
        </div>

        <!-- Footer -->
        <div style="text-align: center; padding: 24px; color: #64748b; font-size: 13px;">
            <p style="margin: 0;">Generated by Bensley Operating System</p>
            <p style="margin: 8px 0 0 0;">
                <a href="http://localhost:3002/overview" style="color: #3b82f6; text-decoration: none;">View Full Dashboard →</a>
            </p>
        </div>

    </div>
</body>
</html>
        """

        return html


def main():
    """CLI entry point for testing."""
    import sys

    service = WeeklyReportService()

    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        result = service.get_quick_stats()
    else:
        result = service.generate_report()

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
