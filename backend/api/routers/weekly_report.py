"""
Weekly Report API - Bill's Monday morning summary (#142)

Endpoints:
- GET /api/weekly-report - Full weekly report
- GET /api/weekly-report/quick - Quick stats for dashboard
- GET /api/weekly-report/email-preview - HTML preview for email
"""

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from typing import Optional
from datetime import datetime, timedelta
import sys

# Add backend path for imports
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from api.dependencies import DB_PATH
from services.weekly_report_service import WeeklyReportService

router = APIRouter(prefix="/api/weekly-report", tags=["weekly-report"])

# Initialize service
report_service = WeeklyReportService(DB_PATH)


@router.get("")
async def get_weekly_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """
    Get full weekly report.

    Defaults to last week (Monday to today) if no dates provided.

    Returns:
    - period: Report date range
    - week_in_review: New, won, lost proposals
    - attention_required: Overdue, stale, at-risk
    - pipeline_outlook: Totals, weighted values, win rate
    - activity_summary: Emails, meetings, actions
    - top_opportunities: Best prospects
    - stalled_proposals: No activity 14+ days
    """
    return report_service.generate_report(start_date, end_date)


@router.get("/quick")
async def get_quick_stats():
    """Get quick stats for dashboard card."""
    return report_service.get_quick_stats()


@router.get("/email-preview", response_class=HTMLResponse)
async def get_email_preview(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    style: str = Query("modern", description="Style: 'modern' (new beautiful) or 'classic' (old)")
):
    """
    Get HTML preview of the weekly email report.

    This is what Bill would receive in his inbox.
    Use ?style=modern for the new beautiful design.
    """
    if style == "modern":
        # Use the new beautiful HTML generator
        html = report_service.generate_html_report(start_date, end_date)
    else:
        # Use the old classic generator
        report = report_service.generate_report(start_date, end_date)
        html = _generate_email_html(report)
    return HTMLResponse(content=html)


def _generate_email_html(report: dict) -> str:
    """Generate HTML email from report data."""
    period = report.get('period', {})
    review = report.get('week_in_review', {})
    attention = report.get('attention_required', {})
    pipeline = report.get('pipeline_outlook', {})
    activity = report.get('activity_summary', {})
    top_opps = report.get('top_opportunities', [])
    stalled = report.get('stalled_proposals', [])

    def format_currency(value):
        if value and value >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        elif value and value >= 1_000:
            return f"${value/1_000:.0f}K"
        elif value:
            return f"${value:,.0f}"
        return "$0"

    # Build HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Proposal Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.5;
            color: #1a1a1a;
            max-width: 640px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        h1 {{
            font-size: 24px;
            margin: 0 0 8px 0;
        }}
        h2 {{
            font-size: 16px;
            color: #666;
            margin: 0 0 16px 0;
            font-weight: 500;
        }}
        h3 {{
            font-size: 14px;
            color: #333;
            margin: 0 0 12px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metrics {{
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }}
        .metric {{
            flex: 1;
            min-width: 100px;
            text-align: center;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: 600;
            color: #1a1a1a;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .alert {{
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
        }}
        .alert-red {{
            background: #fee2e2;
            border-left: 4px solid #ef4444;
        }}
        .alert-amber {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
        }}
        .alert-green {{
            background: #dcfce7;
            border-left: 4px solid #22c55e;
        }}
        .proposal-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .proposal-row:last-child {{
            border-bottom: none;
        }}
        .proposal-name {{
            font-weight: 500;
        }}
        .proposal-value {{
            color: #666;
        }}
        .trend-up {{
            color: #22c55e;
        }}
        .trend-down {{
            color: #ef4444;
        }}
        .footer {{
            text-align: center;
            color: #999;
            font-size: 12px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Weekly Proposal Report</h1>
        <h2>{period.get('start', 'Last Week')} to {period.get('end', 'Today')}</h2>
    </div>

    <!-- Week in Review -->
    <div class="card">
        <h3>Week in Review</h3>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{review.get('new_proposals', {}).get('count', 0)}</div>
                <div class="metric-label">New</div>
                <div style="font-size: 11px; color: #666;">{format_currency(review.get('new_proposals', {}).get('value', 0))}</div>
            </div>
            <div class="metric" style="background: #dcfce7;">
                <div class="metric-value" style="color: #22c55e;">{review.get('won', {}).get('count', 0)}</div>
                <div class="metric-label">Won</div>
                <div style="font-size: 11px; color: #22c55e;">{format_currency(review.get('won', {}).get('value', 0))}</div>
            </div>
            <div class="metric" style="background: #fee2e2;">
                <div class="metric-value" style="color: #ef4444;">{review.get('lost', {}).get('count', 0)}</div>
                <div class="metric-label">Lost</div>
                <div style="font-size: 11px; color: #ef4444;">{format_currency(review.get('lost', {}).get('value', 0))}</div>
            </div>
        </div>
    </div>

    <!-- Attention Required -->
    <div class="card">
        <h3>Attention Required</h3>
        {"".join(f'''
        <div class="alert alert-red">
            <strong>{p.get('project_name', p.get('project_code', 'Unknown'))}</strong><br>
            <span style="font-size: 12px;">Overdue by {int(p.get('days_overdue', 0))} days - {p.get('action_needed', 'Follow up')}</span>
        </div>
        ''' for p in attention.get('overdue', [])[:3]) or '<p style="color: #666;">No overdue items</p>'}

        {"".join(f'''
        <div class="alert alert-amber">
            <strong>{p.get('project_name', p.get('project_code', 'Unknown'))}</strong><br>
            <span style="font-size: 12px;">No activity for {p.get('days_since_contact', 0)} days</span>
        </div>
        ''' for p in stalled[:3]) or ''}
    </div>

    <!-- Pipeline Outlook -->
    <div class="card">
        <h3>Pipeline Outlook</h3>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{format_currency(pipeline.get('total_pipeline', 0))}</div>
                <div class="metric-label">Total Pipeline</div>
            </div>
            <div class="metric">
                <div class="metric-value">{format_currency(pipeline.get('weighted_pipeline', 0))}</div>
                <div class="metric-label">Weighted</div>
            </div>
            <div class="metric">
                <div class="metric-value">{pipeline.get('proposal_count', 0)}</div>
                <div class="metric-label">Active</div>
            </div>
        </div>
        <div style="margin-top: 16px; text-align: center;">
            <span class="{'trend-up' if pipeline.get('win_rate', {}).get('trend') == 'up' else 'trend-down' if pipeline.get('win_rate', {}).get('trend') == 'down' else ''}">
                Win Rate: {pipeline.get('win_rate', {}).get('current', 0)}%
                {'↑' if pipeline.get('win_rate', {}).get('trend') == 'up' else '↓' if pipeline.get('win_rate', {}).get('trend') == 'down' else '→'}
            </span>
        </div>
    </div>

    <!-- Top Opportunities -->
    <div class="card">
        <h3>Top Opportunities</h3>
        {"".join(f'''
        <div class="proposal-row">
            <span class="proposal-name">{p.get('project_name', p.get('project_code', 'Unknown'))}</span>
            <span class="proposal-value">{format_currency(p.get('project_value', 0))} ({p.get('win_probability', 50)}%)</span>
        </div>
        ''' for p in top_opps[:5]) or '<p style="color: #666;">No active opportunities</p>'}
    </div>

    <!-- Activity Summary -->
    <div class="card">
        <h3>Activity This Week</h3>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{activity.get('emails_sent', 0)}</div>
                <div class="metric-label">Sent</div>
            </div>
            <div class="metric">
                <div class="metric-value">{activity.get('emails_received', 0)}</div>
                <div class="metric-label">Received</div>
            </div>
            <div class="metric">
                <div class="metric-value">{activity.get('meetings', 0)}</div>
                <div class="metric-label">Meetings</div>
            </div>
        </div>
    </div>

    <div class="footer">
        Generated by Bensley Intelligence Platform<br>
        {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
</body>
</html>
"""
    return html
