"""
Analytics Router - Dashboard analytics endpoints

Endpoints:
    GET /api/analytics/dashboard - Dashboard analytics overview
"""

from fastapi import APIRouter, HTTPException
import sqlite3
from datetime import datetime, timedelta

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
