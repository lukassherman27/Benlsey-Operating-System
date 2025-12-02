"""
Dashboard Router - Dashboard and KPI endpoints

Endpoints:
    GET /api/dashboard/stats - Dashboard statistics
    GET /api/dashboard/kpis - KPI metrics
    GET /api/dashboard/decision-tiles - Decision tiles for dashboard
    GET /api/briefing/daily - Daily briefing
    ... and more
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import sqlite3

from api.services import (
    proposal_service,
    email_service,
    financial_service,
    training_service,
)
from api.dependencies import DB_PATH
from api.helpers import list_response, item_response

router = APIRouter(prefix="/api", tags=["dashboard"])


# ============================================================================
# DASHBOARD STATISTICS
# ============================================================================

@router.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get comprehensive dashboard statistics"""
    try:
        # Get proposal stats
        proposal_stats = proposal_service.get_dashboard_stats()

        # Get email stats
        email_stats = email_service.get_email_stats()

        # Get training progress
        training_progress = training_service.get_verification_stats()

        stats = {
            "total_proposals": proposal_stats.get('total_proposals', 0),
            "active_projects": proposal_stats.get('active_projects', 0),
            "total_emails": email_stats.get('total_emails', 0),
            "categorized_emails": email_stats.get('categorized', 0),
            "needs_review": email_stats.get('needs_review', 0),
            "total_attachments": email_stats.get('attachments', 0),
            "training_progress": training_progress,
            "proposals": proposal_stats.get('by_status', {}),
            "revenue": proposal_stats.get('revenue', {})
        }
        response = item_response(stats)
        response.update(stats)  # Backward compat - flatten at root
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")


def get_period_dates(period: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Calculate date ranges for a given period and its comparison period"""
    today = datetime.now().date()

    if period == "custom" and start_date and end_date:
        current_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        current_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        delta = (current_end - current_start).days
        prev_end = current_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=delta)
    elif period == "this_month":
        current_start = today.replace(day=1)
        current_end = today
        # Previous month
        prev_end = current_start - timedelta(days=1)
        prev_start = prev_end.replace(day=1)
    elif period == "last_3_months":
        current_start = (today - timedelta(days=90)).replace(day=1)
        current_end = today
        # Previous 3 months
        prev_end = current_start - timedelta(days=1)
        prev_start = (prev_end - timedelta(days=90)).replace(day=1)
    elif period == "this_year":
        current_start = today.replace(month=1, day=1)
        current_end = today
        # Same period last year
        prev_start = current_start.replace(year=today.year - 1)
        prev_end = current_end.replace(year=today.year - 1)
    elif period == "last_year":
        current_start = today.replace(year=today.year - 1, month=1, day=1)
        current_end = today.replace(year=today.year - 1, month=12, day=31)
        # Year before that
        prev_start = current_start.replace(year=today.year - 2)
        prev_end = current_end.replace(year=today.year - 2)
    else:  # all_time
        current_start = None
        current_end = None
        prev_start = None
        prev_end = None

    return {
        "current_start": current_start.isoformat() if current_start else None,
        "current_end": current_end.isoformat() if current_end else None,
        "prev_start": prev_start.isoformat() if prev_start else None,
        "prev_end": prev_end.isoformat() if prev_end else None,
    }


def calculate_trend(current: float, previous: float) -> dict:
    """Calculate trend between current and previous values"""
    if previous == 0:
        if current > 0:
            return {"value": 100, "direction": "up", "label": "+100%"}
        return {"value": 0, "direction": "neutral", "label": ""}

    change_pct = ((current - previous) / abs(previous)) * 100

    if abs(change_pct) < 5:
        return {"value": round(change_pct, 1), "direction": "neutral", "label": f"{change_pct:+.1f}%"}
    elif change_pct > 0:
        return {"value": round(change_pct, 1), "direction": "up", "label": f"+{change_pct:.1f}%"}
    else:
        return {"value": round(change_pct, 1), "direction": "down", "label": f"{change_pct:.1f}%"}


@router.get("/dashboard/kpis")
async def get_dashboard_kpis(
    period: str = Query("all_time", description="Time period: this_month, last_3_months, this_year, last_year, all_time, custom"),
    start_date: Optional[str] = Query(None, description="Start date for custom period (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for custom period (YYYY-MM-DD)")
):
    """Get key performance indicators for dashboard with time period filtering

    Supports periods: this_month, last_3_months, this_year, last_year, all_time, custom
    For custom period, provide start_date and end_date parameters.

    Returns KPIs with comparison to previous period.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get date ranges
        dates = get_period_dates(period, start_date, end_date)
        current_start = dates["current_start"]
        current_end = dates["current_end"]
        prev_start = dates["prev_start"]
        prev_end = dates["prev_end"]

        # Period label for frontend
        period_labels = {
            "this_month": "This Month",
            "last_3_months": "Last 3 Months",
            "this_year": str(datetime.now().year),
            "last_year": str(datetime.now().year - 1),
            "all_time": "All Time",
            "custom": "Custom Range"
        }
        period_label = period_labels.get(period, "All Time")

        # ========== REMAINING CONTRACT VALUE (not period-filtered) ==========
        cursor.execute("""
            SELECT COALESCE(SUM(total_fee_usd), 0) as total_contract_value
            FROM projects
            WHERE is_active_project = 1
        """)
        total_contract_value = cursor.fetchone()['total_contract_value'] or 0

        cursor.execute("""
            SELECT COALESCE(SUM(payment_amount), 0) as total_paid
            FROM invoices
        """)
        all_time_paid = cursor.fetchone()['total_paid'] or 0
        remaining_contract_value = total_contract_value - all_time_paid

        # ========== PAID IN PERIOD ==========
        if current_start and current_end:
            cursor.execute(f"""
                SELECT COALESCE(SUM(payment_amount), 0) as paid
                FROM invoices
                WHERE payment_date >= '{current_start}' AND payment_date <= '{current_end}'
            """)
            paid_in_period = cursor.fetchone()['paid'] or 0

            # Previous period for comparison
            if prev_start and prev_end:
                cursor.execute(f"""
                    SELECT COALESCE(SUM(payment_amount), 0) as paid
                    FROM invoices
                    WHERE payment_date >= '{prev_start}' AND payment_date <= '{prev_end}'
                """)
                paid_prev_period = cursor.fetchone()['paid'] or 0
            else:
                paid_prev_period = 0
        else:
            paid_in_period = all_time_paid
            paid_prev_period = 0

        paid_trend = calculate_trend(paid_in_period, paid_prev_period)
        # For "paid", up is good

        # ========== OUTSTANDING INVOICES ==========
        cursor.execute("""
            SELECT COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0) as outstanding
            FROM invoices
            WHERE status != 'paid' OR (invoice_amount - COALESCE(payment_amount, 0)) > 0
        """)
        outstanding_invoices = cursor.fetchone()['outstanding'] or 0

        # Compare to 30 days ago for outstanding trend
        cursor.execute("""
            SELECT COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0) as outstanding
            FROM invoices
            WHERE invoice_date <= date('now', '-30 days')
            AND (status != 'paid' OR (invoice_amount - COALESCE(payment_amount, 0)) > 0)
        """)
        outstanding_prev = cursor.fetchone()['outstanding'] or outstanding_invoices
        outstanding_trend = calculate_trend(outstanding_invoices, outstanding_prev)
        # For outstanding, down is good (invert the direction meaning)
        if outstanding_trend["direction"] == "up":
            outstanding_trend["is_positive"] = False
        elif outstanding_trend["direction"] == "down":
            outstanding_trend["is_positive"] = True
        else:
            outstanding_trend["is_positive"] = True

        # ========== CONTRACTS SIGNED IN PERIOD ==========
        if current_start and current_end:
            cursor.execute(f"""
                SELECT COUNT(*) as count, COALESCE(SUM(total_fee_usd), 0) as value
                FROM projects
                WHERE is_active_project = 1
                AND contract_signed_date >= '{current_start}' AND contract_signed_date <= '{current_end}'
            """)
            row = cursor.fetchone()
            contracts_signed_count = row['count'] or 0
            contracts_signed_value = row['value'] or 0

            if prev_start and prev_end:
                cursor.execute(f"""
                    SELECT COUNT(*) as count
                    FROM projects
                    WHERE is_active_project = 1
                    AND contract_signed_date >= '{prev_start}' AND contract_signed_date <= '{prev_end}'
                """)
                contracts_prev = cursor.fetchone()['count'] or 0
            else:
                contracts_prev = 0
        else:
            # All time - use current year
            current_year = datetime.now().year
            cursor.execute(f"""
                SELECT COUNT(*) as count, COALESCE(SUM(total_fee_usd), 0) as value
                FROM projects
                WHERE is_active_project = 1
                AND contract_signed_date >= '{current_year}-01-01'
            """)
            row = cursor.fetchone()
            contracts_signed_count = row['count'] or 0
            contracts_signed_value = row['value'] or 0
            contracts_prev = 0

        contracts_trend = calculate_trend(contracts_signed_count, contracts_prev)

        # ========== ACTIVE PROJECTS & PROPOSALS ==========
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM projects
            WHERE is_active_project = 1
        """)
        active_projects = cursor.fetchone()['count'] or 0

        # Active proposals = not signed contracts, not completed/cancelled/lost
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM projects
            WHERE is_active_project = 0
            AND status NOT IN ('Completed', 'completed', 'Cancelled', 'cancelled', 'lost', 'declined', 'archived')
        """)
        active_proposals = cursor.fetchone()['count'] or 0

        # ========== ADDITIONAL KPIs ==========

        # Average days to payment (for paid invoices)
        cursor.execute("""
            SELECT AVG(julianday(payment_date) - julianday(invoice_date)) as avg_days
            FROM invoices
            WHERE payment_date IS NOT NULL AND invoice_date IS NOT NULL
            AND payment_date >= invoice_date
        """)
        row = cursor.fetchone()
        avg_days_to_payment = round(row['avg_days'] or 0, 1)

        # Largest outstanding invoice
        cursor.execute("""
            SELECT invoice_number, project_id,
                   (invoice_amount - COALESCE(payment_amount, 0)) as outstanding
            FROM invoices
            WHERE (invoice_amount - COALESCE(payment_amount, 0)) > 0
            ORDER BY outstanding DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        largest_outstanding = {
            "amount": row['outstanding'] if row else 0,
            "invoice_number": row['invoice_number'] if row else None
        }

        # Win rate (won / (won + lost) for projects)
        # Note: "won" = is_active_project=1, "lost" = status in lost/declined/cancelled
        cursor.execute("""
            SELECT
                SUM(CASE WHEN is_active_project = 1 THEN 1 ELSE 0 END) as won,
                SUM(CASE WHEN status IN ('lost', 'declined', 'cancelled', 'Cancelled') THEN 1 ELSE 0 END) as lost
            FROM projects
        """)
        row = cursor.fetchone()
        won = row['won'] or 0
        lost = row['lost'] or 0
        # Only calculate win rate if we have meaningful data (at least some lost deals tracked)
        if lost > 0:
            win_rate = round((won / (won + lost) * 100), 1)
        elif won > 0:
            # No lost deals tracked - win rate is not meaningful, show None
            win_rate = None
        else:
            win_rate = 0

        # Pipeline value (proposals not yet won - is_active_project=0, not completed/lost)
        cursor.execute("""
            SELECT COALESCE(SUM(total_fee_usd), 0) as pipeline
            FROM projects
            WHERE is_active_project = 0
            AND status NOT IN ('Completed', 'completed', 'Cancelled', 'cancelled', 'lost', 'declined', 'archived')
        """)
        pipeline_value = cursor.fetchone()['pipeline'] or 0

        # Overdue invoices count and amount
        cursor.execute("""
            SELECT COUNT(*) as count,
                   COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0) as amount
            FROM invoices
            WHERE due_date < date('now')
            AND (invoice_amount - COALESCE(payment_amount, 0)) > 0
        """)
        row = cursor.fetchone()
        overdue_count = row['count'] or 0
        overdue_amount = row['amount'] or 0

        conn.close()

        return {
            "period": period,
            "period_label": period_label,
            "date_range": {
                "start": current_start,
                "end": current_end
            },
            "remaining_contract_value": {
                "value": remaining_contract_value,
                "trend": {"value": 0, "direction": "neutral", "label": ""}
            },
            "active_projects": {
                "value": active_projects,
                "trend": {"value": 0, "direction": "neutral", "label": ""}
            },
            "active_proposals": {
                "value": active_proposals,
                "trend": {"value": 0, "direction": "neutral", "label": ""}
            },
            "contracts_signed": {
                "value": contracts_signed_count,
                "amount": contracts_signed_value,
                "trend": contracts_trend
            },
            "paid_in_period": {
                "value": paid_in_period,
                "trend": paid_trend,
                "previous_value": paid_prev_period
            },
            "outstanding_invoices": {
                "value": outstanding_invoices,
                "trend": outstanding_trend,
                "overdue_count": overdue_count,
                "overdue_amount": overdue_amount
            },
            # Additional KPIs
            "avg_days_to_payment": avg_days_to_payment,
            "largest_outstanding": largest_outstanding,
            "win_rate": win_rate,
            "pipeline_value": pipeline_value,
            # Legacy fields for compatibility
            "contracts_signed_2025": {
                "value": contracts_signed_count,
                "trend": contracts_trend
            },
            "total_paid_to_date": {
                "value": all_time_paid,
                "trend": {"value": 0, "direction": "neutral", "label": ""}
            },
            "revenue_ytd": {
                "value": paid_in_period if period == "this_year" else all_time_paid,
                "trend": paid_trend
            },
            "trend_period_days": 30
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate KPIs: {str(e)}")


@router.get("/dashboard/decision-tiles")
async def get_decision_tiles():
    """Get actionable decision tiles for dashboard"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        tiles = []

        # Overdue invoices
        cursor.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0) as amount
            FROM invoices
            WHERE status != 'paid'
            AND due_date < date('now')
        """)
        overdue = cursor.fetchone()
        if overdue['count'] > 0:
            tiles.append({
                "type": "overdue_invoices",
                "title": "Overdue Invoices",
                "count": overdue['count'],
                "value": overdue['amount'],
                "priority": "high",
                "action": "Review and follow up"
            })

        # Stale proposals (no contact > 21 days)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM projects
            WHERE is_active_project = 1
            AND days_since_contact > 21
        """)
        stale = cursor.fetchone()['count']
        if stale > 0:
            tiles.append({
                "type": "stale_proposals",
                "title": "Stale Projects",
                "count": stale,
                "priority": "high",
                "action": "Contact client"
            })

        # Pending approvals
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM ai_suggestions
            WHERE status = 'pending' AND confidence >= 0.8
        """)
        pending = cursor.fetchone()['count']
        if pending > 0:
            tiles.append({
                "type": "pending_approvals",
                "title": "High-Confidence Suggestions",
                "count": pending,
                "priority": "medium",
                "action": "Review and approve"
            })

        conn.close()

        return {"tiles": tiles, "count": len(tiles)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BRIEFING ENDPOINTS
# ============================================================================

@router.get("/briefing/daily")
async def get_daily_briefing():
    """Executive daily briefing - actionable intelligence"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get projects needing attention
        cursor.execute("""
            SELECT project_id, project_code, project_title, status,
                   health_score, days_since_contact, last_proposal_activity_date,
                   notes, total_fee_usd
            FROM projects
            WHERE is_active_project = 1
            ORDER BY health_score ASC NULLS LAST
            LIMIT 20
        """)

        projects = []
        for row in cursor.fetchall():
            projects.append({
                "project_id": row[0],
                "project_code": row[1],
                "project_title": row[2],
                "status": row[3],
                "health_score": row[4],
                "days_since_contact": row[5],
                "last_contact_date": row[6],
                "next_action": row[7],
                "total_fee_usd": row[8]
            })

        # Categorize
        urgent = []
        needs_attention = []

        for p in projects:
            days = p["days_since_contact"] or 999

            if days >= 18:
                urgent.append({
                    "type": "no_contact",
                    "priority": "high",
                    "project_code": p["project_code"],
                    "project_title": p["project_title"],
                    "action": f"Call client - {p['next_action'] or 'follow up'}",
                    "context": f"{days} days no contact"
                })
            elif days >= 7:
                needs_attention.append({
                    "type": "follow_up",
                    "project_code": p["project_code"],
                    "project_title": p["project_title"],
                    "action": p["next_action"] or "Schedule follow up",
                    "context": f"{days} days since contact"
                })

        conn.close()

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "urgent": urgent,
            "needs_attention": needs_attention,
            "total_active": len(projects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/meetings")
async def get_dashboard_meetings():
    """Get upcoming meetings for dashboard"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get meetings in next 7 days
        cursor.execute("""
            SELECT * FROM meetings
            WHERE start_time >= datetime('now')
            AND start_time <= datetime('now', '+7 days')
            ORDER BY start_time ASC
            LIMIT 10
        """)

        meetings = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {"meetings": meetings, "count": len(meetings)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
