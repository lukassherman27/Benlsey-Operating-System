"""
Analytics Router - Dashboard analytics endpoints

Endpoints:
    GET /api/analytics/dashboard - Dashboard analytics overview
    GET /api/analytics/trends - Pipeline and win rate trends over time
"""

from fastapi import APIRouter, HTTPException
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from api.dependencies import DB_PATH
from api.helpers import item_response

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics/dashboard")
async def get_dashboard_analytics():
    """Get comprehensive dashboard analytics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get proposal stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_proposals,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_proposals,
                SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as won_proposals,
                SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as lost_proposals,
                COALESCE(SUM(project_value), 0) as total_pipeline_value
            FROM proposals
        """)
        proposals = dict(cursor.fetchone() or {})

        # Get project stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_projects,
                SUM(CASE WHEN is_active_project = 1 THEN 1 ELSE 0 END) as active_projects,
                COALESCE(SUM(total_fee_usd), 0) as total_contract_value,
                (SELECT COALESCE(SUM(payment_amount), 0) FROM invoices) as total_collected
            FROM projects
        """)
        projects = dict(cursor.fetchone() or {})

        # Get email stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_emails,
                SUM(CASE WHEN ec.category IS NOT NULL THEN 1 ELSE 0 END) as categorized_emails
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
        """)
        emails = dict(cursor.fetchone() or {})

        # Get invoice stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_invoices,
                COALESCE(SUM(invoice_amount), 0) as total_invoiced,
                COALESCE(SUM(payment_amount), 0) as total_paid
            FROM invoices
        """)
        invoices = dict(cursor.fetchone() or {})

        # Recent activity (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) as recent_emails
            FROM emails
            WHERE date > ?
        """, (week_ago,))
        recent = dict(cursor.fetchone() or {})

        conn.close()

        return {
            "success": True,
            "proposals": proposals,
            "projects": projects,
            "emails": emails,
            "invoices": invoices,
            "recent_activity": {
                "emails_last_7_days": recent.get('recent_emails', 0)
            },
            "health": {
                "email_categorization_rate": round(
                    (emails.get('categorized_emails', 0) / max(emails.get('total_emails', 1), 1)) * 100, 1
                ),
                "collection_rate": round(
                    (invoices.get('total_paid', 0) / max(invoices.get('total_invoiced', 1), 1)) * 100, 1
                ) if invoices.get('total_invoiced') else 0,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/trends")
async def get_analytics_trends(months: int = 12):
    """
    Get time-series analytics for charts.

    Returns:
    - pipeline_by_month: Total active pipeline value per month
    - win_rate_by_month: Win rate percentage per month
    - pipeline_by_status: Current pipeline breakdown by status
    - cycle_times: Average days in each stage
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Generate list of months for the last N months
        today = datetime.now()
        month_list = []
        for i in range(months - 1, -1, -1):
            d = today - timedelta(days=i * 30)
            month_list.append(d.strftime('%Y-%m'))

        # Pipeline value by month (based on first_contact_date)
        # Shows cumulative active pipeline at end of each month
        pipeline_by_month = []
        for month in month_list:
            year, m = month.split('-')
            # Get proposals that were active at end of this month
            # (created before or during month, not lost/signed before month end)
            month_end = f"{month}-{28}"  # Approximate month end
            cursor.execute("""
                SELECT COALESCE(SUM(project_value), 0) as value
                FROM proposals
                WHERE first_contact_date <= ?
                AND (contract_signed_date IS NULL OR contract_signed_date > ?)
                AND (status != 'Lost' OR updated_at > ?)
            """, (month_end, month_end, month_end))
            result = cursor.fetchone()
            pipeline_by_month.append({
                "month": month,
                "value": result['value'] if result else 0
            })

        # Win rate by month
        win_rate_by_month = []
        for month in month_list:
            # Count wins and losses that occurred in this month
            month_start = f"{month}-01"
            year, m = month.split('-')
            next_month = int(m) + 1
            if next_month > 12:
                next_month = 1
                year = str(int(year) + 1)
            month_end = f"{year}-{str(next_month).zfill(2)}-01"

            cursor.execute("""
                SELECT
                    SUM(CASE WHEN contract_signed_date >= ? AND contract_signed_date < ? THEN 1 ELSE 0 END) as won,
                    SUM(CASE WHEN status = 'Lost' AND updated_at >= ? AND updated_at < ? THEN 1 ELSE 0 END) as lost
                FROM proposals
            """, (month_start, month_end, month_start, month_end))
            result = cursor.fetchone()
            won = result['won'] or 0
            lost = result['lost'] or 0
            total = won + lost
            rate = round((won / total * 100), 1) if total > 0 else None

            win_rate_by_month.append({
                "month": month,
                "win_rate": rate,
                "won": won,
                "lost": lost
            })

        # Current pipeline by status (exclude closed + stale statuses)
        cursor.execute("""
            SELECT
                status,
                COUNT(*) as count,
                COALESCE(SUM(project_value), 0) as value
            FROM proposals
            WHERE status NOT IN ('Contract Signed', 'Lost', 'Declined', 'Dormant', 'On Hold')
            GROUP BY status
            ORDER BY
                CASE status
                    WHEN 'First Contact' THEN 1
                    WHEN 'Meeting Scheduled' THEN 2
                    WHEN 'Design Brief Received' THEN 3
                    WHEN 'Proposal Sent' THEN 4
                    WHEN 'Negotiation' THEN 5
                    WHEN 'Verbal Agreement' THEN 6
                    ELSE 7
                END
        """)
        pipeline_by_status = [dict(row) for row in cursor.fetchall()]

        # Average cycle times by stage
        cursor.execute("""
            SELECT
                status,
                AVG(JULIANDAY(COALESCE(contract_signed_date, 'now')) - JULIANDAY(first_contact_date)) as avg_days
            FROM proposals
            WHERE first_contact_date IS NOT NULL
            AND status = 'Contract Signed'
            GROUP BY status
        """)
        won_cycle = cursor.fetchone()
        avg_days_to_win = round(won_cycle['avg_days'], 1) if won_cycle and won_cycle['avg_days'] else None

        # Stage duration (how long proposals spend in current stage)
        cursor.execute("""
            SELECT
                status,
                AVG(JULIANDAY('now') - JULIANDAY(COALESCE(last_status_change, first_contact_date, created_at))) as avg_days_in_stage,
                COUNT(*) as count
            FROM proposals
            WHERE status NOT IN ('Contract Signed', 'Lost', 'Declined', 'Dormant', 'On Hold')
            GROUP BY status
        """)
        stage_durations = [
            {
                "status": row['status'],
                "avg_days": round(row['avg_days_in_stage'], 1) if row['avg_days_in_stage'] else 0,
                "count": row['count']
            }
            for row in cursor.fetchall()
        ]

        # Win rate by value bracket
        cursor.execute("""
            SELECT
                CASE
                    WHEN project_value IS NULL THEN 'Unknown'
                    WHEN project_value < 500000 THEN '<$500K'
                    WHEN project_value < 1000000 THEN '$500K-$1M'
                    WHEN project_value < 5000000 THEN '$1M-$5M'
                    ELSE '$5M+'
                END as bracket,
                SUM(CASE WHEN status = 'Contract Signed' THEN 1 ELSE 0 END) as won,
                SUM(CASE WHEN status = 'Lost' THEN 1 ELSE 0 END) as lost
            FROM proposals
            GROUP BY bracket
            ORDER BY
                CASE bracket
                    WHEN '<$500K' THEN 1
                    WHEN '$500K-$1M' THEN 2
                    WHEN '$1M-$5M' THEN 3
                    WHEN '$5M+' THEN 4
                    ELSE 5
                END
        """)
        win_rate_by_value = []
        for row in cursor.fetchall():
            total = (row['won'] or 0) + (row['lost'] or 0)
            rate = round((row['won'] / total * 100), 1) if total > 0 else None
            win_rate_by_value.append({
                "bracket": row['bracket'],
                "win_rate": rate,
                "won": row['won'] or 0,
                "lost": row['lost'] or 0,
                "total": total
            })

        # Summary metrics (active pipeline only - excludes Dormant/On Hold)
        cursor.execute("""
            SELECT
                COUNT(*) as active_count,
                COALESCE(SUM(project_value), 0) as total_value,
                COALESCE(SUM(project_value * COALESCE(win_probability, 50) / 100), 0) as weighted_value
            FROM proposals
            WHERE status NOT IN ('Contract Signed', 'Lost', 'Declined', 'Dormant', 'On Hold')
        """)
        summary = dict(cursor.fetchone())

        # Stalled pipeline (Dormant + On Hold - shown separately)
        cursor.execute("""
            SELECT
                status,
                COUNT(*) as count,
                COALESCE(SUM(project_value), 0) as value
            FROM proposals
            WHERE status IN ('Dormant', 'On Hold')
            GROUP BY status
        """)
        stalled_pipeline = [dict(row) for row in cursor.fetchall()]

        # Data quality metrics
        cursor.execute("""
            SELECT
                SUM(CASE WHEN project_value IS NULL OR project_value = 0 THEN 1 ELSE 0 END) as missing_values,
                SUM(CASE WHEN win_probability = 0 AND status NOT IN ('Contract Signed', 'Lost', 'Declined') THEN 1 ELSE 0 END) as zero_probability
            FROM proposals
            WHERE status NOT IN ('Contract Signed', 'Lost', 'Declined')
        """)
        data_quality = dict(cursor.fetchone())

        conn.close()

        return {
            "success": True,
            "pipeline_by_month": pipeline_by_month,
            "win_rate_by_month": win_rate_by_month,
            "pipeline_by_status": pipeline_by_status,
            "stage_durations": stage_durations,
            "win_rate_by_value": win_rate_by_value,
            "stalled_pipeline": stalled_pipeline,
            "data_quality": {
                "missing_values": data_quality['missing_values'] or 0,
                "zero_probability": data_quality['zero_probability'] or 0
            },
            "summary": {
                "active_proposals": summary['active_count'],
                "total_pipeline": summary['total_value'],
                "weighted_pipeline": summary['weighted_value'],
                "avg_days_to_win": avg_days_to_win
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
