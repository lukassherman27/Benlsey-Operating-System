"""
Dashboard Router - Dashboard and KPI endpoints

Endpoints:
    GET /api/dashboard/stats - Dashboard statistics (with optional role-based filtering)
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
# ROLE-BASED STATISTICS HELPER
# ============================================================================

async def get_role_based_stats(role: str) -> dict:
    """Get role-specific dashboard statistics

    Args:
        role: Role identifier (bill, pm, finance)

    Returns:
        Role-specific KPI dictionary
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        if role == "bill":
            # Executive KPIs
            # Pipeline value: SUM of active proposals (all now USD after data fix)
            cursor.execute("""
                SELECT COALESCE(SUM(project_value), 0) as pipeline_value
                FROM proposals
                WHERE current_status NOT IN ('Lost', 'Declined', 'Dormant', 'Contract Signed', 'Contract signed', 'Cancelled')
                AND project_value > 0
            """)
            pipeline_value = cursor.fetchone()['pipeline_value'] or 0

            # Active projects count
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM projects
                WHERE status = 'Active' OR is_active_project = 1
            """)
            active_projects_count = cursor.fetchone()['count'] or 0

            # Outstanding invoices total (active projects only)
            cursor.execute("""
                SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as outstanding
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.is_active_project = 1
                AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
            """)
            outstanding_invoices_total = cursor.fetchone()['outstanding'] or 0

            # Overdue invoices count (active projects only)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.is_active_project = 1
                AND i.due_date < date('now')
                AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
            """)
            overdue_invoices_count = cursor.fetchone()['count'] or 0

            return {
                "role": "bill",
                "pipeline_value": round(pipeline_value, 2),
                "active_projects_count": active_projects_count,
                "outstanding_invoices_total": round(outstanding_invoices_total, 2),
                "overdue_invoices_count": overdue_invoices_count
            }

        elif role == "pm":
            # PM KPIs
            # My projects count (for now, all active projects)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM projects
                WHERE status = 'Active' OR is_active_project = 1
            """)
            my_projects_count = cursor.fetchone()['count'] or 0

            # Deliverables due this week (from project_milestones)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM project_milestones
                WHERE status NOT IN ('completed', 'cancelled')
                AND planned_date >= date('now')
                AND planned_date <= date('now', '+7 days')
            """)
            deliverables_due_this_week = cursor.fetchone()['count'] or 0

            # Open RFIs count
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM rfis
                WHERE status = 'open'
            """)
            open_rfis_count = cursor.fetchone()['count'] or 0

            return {
                "role": "pm",
                "my_projects_count": my_projects_count,
                "deliverables_due_this_week": deliverables_due_this_week,
                "open_rfis_count": open_rfis_count
            }

        elif role == "finance":
            # Finance KPIs (active projects only)
            # Total outstanding
            cursor.execute("""
                SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as outstanding
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.is_active_project = 1
                AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
            """)
            total_outstanding = cursor.fetchone()['outstanding'] or 0

            # Overdue 30 days
            cursor.execute("""
                SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as overdue
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.is_active_project = 1
                AND i.due_date < date('now', '-30 days')
                AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
            """)
            overdue_30_days = cursor.fetchone()['overdue'] or 0

            # Overdue 60 days
            cursor.execute("""
                SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as overdue
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.is_active_project = 1
                AND i.due_date < date('now', '-60 days')
                AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
            """)
            overdue_60_days = cursor.fetchone()['overdue'] or 0

            # Overdue 90+ days
            cursor.execute("""
                SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as overdue
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.is_active_project = 1
                AND i.due_date < date('now', '-90 days')
                AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
            """)
            overdue_90_plus = cursor.fetchone()['overdue'] or 0

            # Recent payments (last 7 days) - active projects only
            cursor.execute("""
                SELECT COALESCE(SUM(i.payment_amount), 0) as recent_payments
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.is_active_project = 1
                AND i.payment_date >= date('now', '-7 days')
                AND i.payment_date <= date('now')
            """)
            recent_payments_7_days = cursor.fetchone()['recent_payments'] or 0

            return {
                "role": "finance",
                "total_outstanding": round(total_outstanding, 2),
                "overdue_30_days": round(overdue_30_days, 2),
                "overdue_60_days": round(overdue_60_days, 2),
                "overdue_90_plus": round(overdue_90_plus, 2),
                "recent_payments_7_days": round(recent_payments_7_days, 2)
            }

        else:
            raise HTTPException(status_code=400, detail=f"Invalid role: {role}. Must be one of: bill, pm, finance")

    finally:
        conn.close()


# ============================================================================
# DASHBOARD STATISTICS
# ============================================================================

@router.get("/dashboard/stats")
async def get_dashboard_stats(role: Optional[str] = Query(None, description="Role filter: bill, pm, finance")):
    """Get comprehensive dashboard statistics with optional role-based filtering

    Args:
        role: Optional role filter (bill, pm, finance) for role-specific KPIs

    Returns:
        - If role is specified: Role-specific KPIs
        - If no role: Legacy comprehensive stats (backward compatible)
    """
    try:
        # Role-based stats
        if role:
            return await get_role_based_stats(role)

        # Legacy comprehensive stats (backward compatible)
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
        # Total contract value for active projects
        cursor.execute("""
            SELECT COALESCE(SUM(total_fee_usd), 0) as total_contract_value
            FROM projects
            WHERE is_active_project = 1
        """)
        total_contract_value = cursor.fetchone()['total_contract_value'] or 0

        # Paid amount for active projects only
        cursor.execute("""
            SELECT COALESCE(SUM(i.payment_amount), 0) as total_paid
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.is_active_project = 1
        """)
        paid_for_active = cursor.fetchone()['total_paid'] or 0
        all_time_paid = paid_for_active  # Keep for compatibility

        # Outstanding for active projects
        cursor.execute("""
            SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as outstanding
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.is_active_project = 1
            AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
        """)
        outstanding_for_active = cursor.fetchone()['outstanding'] or 0

        # Correct calculation: Total - Paid - Outstanding = Remaining (not yet invoiced)
        remaining_contract_value = total_contract_value - paid_for_active - outstanding_for_active

        # ========== PAID IN PERIOD ==========
        if current_start and current_end:
            cursor.execute("""
                SELECT COALESCE(SUM(payment_amount), 0) as paid
                FROM invoices
                WHERE payment_date >= ? AND payment_date <= ?
            """, (current_start, current_end))
            paid_in_period = cursor.fetchone()['paid'] or 0

            # Previous period for comparison
            if prev_start and prev_end:
                cursor.execute("""
                    SELECT COALESCE(SUM(payment_amount), 0) as paid
                    FROM invoices
                    WHERE payment_date >= ? AND payment_date <= ?
                """, (prev_start, prev_end))
                paid_prev_period = cursor.fetchone()['paid'] or 0
            else:
                paid_prev_period = 0
        else:
            paid_in_period = all_time_paid
            paid_prev_period = 0

        paid_trend = calculate_trend(paid_in_period, paid_prev_period)
        # For "paid", up is good

        # ========== OUTSTANDING INVOICES (active projects only) ==========
        cursor.execute("""
            SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as outstanding
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.is_active_project = 1
            AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
        """)
        outstanding_invoices = cursor.fetchone()['outstanding'] or 0

        # Compare to 30 days ago for outstanding trend
        cursor.execute("""
            SELECT COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as outstanding
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.is_active_project = 1
            AND i.invoice_date <= date('now', '-30 days')
            AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
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
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(total_fee_usd), 0) as value
                FROM projects
                WHERE is_active_project = 1
                AND contract_signed_date >= ? AND contract_signed_date <= ?
            """, (current_start, current_end))
            row = cursor.fetchone()
            contracts_signed_count = row['count'] or 0
            contracts_signed_value = row['value'] or 0

            if prev_start and prev_end:
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM projects
                    WHERE is_active_project = 1
                    AND contract_signed_date >= ? AND contract_signed_date <= ?
                """, (prev_start, prev_end))
                contracts_prev = cursor.fetchone()['count'] or 0
            else:
                contracts_prev = 0
        else:
            # All time - use current year
            current_year = datetime.now().year
            cursor.execute("""
                SELECT COUNT(*) as count, COALESCE(SUM(total_fee_usd), 0) as value
                FROM projects
                WHERE is_active_project = 1
                AND contract_signed_date >= ?
            """, (f"{current_year}-01-01",))
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

        # Pipeline value from proposals table (all now USD after data fix)
        cursor.execute("""
            SELECT COALESCE(SUM(project_value), 0) as pipeline
            FROM proposals
            WHERE current_status NOT IN ('Lost', 'Declined', 'Dormant', 'Contract Signed', 'Contract signed', 'Cancelled')
            AND project_value > 0
        """)
        pipeline_value = cursor.fetchone()['pipeline'] or 0

        # Overdue invoices count and amount (active projects only)
        cursor.execute("""
            SELECT COUNT(*) as count,
                   COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as amount
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.is_active_project = 1
            AND i.due_date < date('now')
            AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
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
                "total_contract": total_contract_value,
                "paid": paid_for_active,
                "outstanding": outstanding_for_active,
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

        # Overdue invoices (active projects only)
        cursor.execute("""
            SELECT COUNT(*) as count, COALESCE(SUM(i.invoice_amount - COALESCE(i.payment_amount, 0)), 0) as amount
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.is_active_project = 1
            AND i.due_date < date('now')
            AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
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
    """Executive daily briefing - actionable intelligence for PROPOSALS needing follow-up"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get PROPOSALS needing attention (not active projects!)
        # Focus on proposals that haven't converted to projects yet and need follow-up
        cursor.execute("""
            SELECT
                p.proposal_id,
                p.project_code,
                p.project_name,
                p.current_status,
                p.last_contact_date,
                CASE
                    WHEN p.last_contact_date IS NULL THEN NULL
                    ELSE CAST(julianday('now') - julianday(p.last_contact_date) AS INTEGER)
                END as days_since_contact,
                p.status_notes,
                p.project_value,
                p.last_action,
                p.waiting_for
            FROM proposals p
            WHERE p.is_active_project = 0
              AND p.current_status NOT IN ('Lost', 'Declined', 'Dormant', 'Contract Signed', 'Contract signed', 'Cancelled')
              AND (
                p.last_contact_date IS NULL
                OR julianday('now') - julianday(p.last_contact_date) > 7
              )
            ORDER BY days_since_contact DESC NULLS FIRST
            LIMIT 30
        """)

        proposals = []
        for row in cursor.fetchall():
            proposals.append({
                "proposal_id": row[0],
                "project_code": row[1],
                "project_name": row[2],
                "status": row[3],
                "last_contact_date": row[4],
                "days_since_contact": row[5],
                "status_notes": row[6],
                "project_value": row[7],
                "last_action": row[8],
                "waiting_for": row[9]
            })

        # Categorize by urgency
        urgent = []
        needs_attention = []

        for p in proposals:
            days = p["days_since_contact"]
            status = p.get("status") or "Unknown"

            # Build context with status and days info
            if days is None:
                days_display = "No contact"
                context = f"{status} - no email history"
            else:
                days_display = f"{days} days"
                context = f"{status} - {days} days since contact"

            # Determine next action from available fields
            next_action = p.get("last_action") or p.get("waiting_for") or p.get("status_notes") or "follow up"

            if days is None or days >= 14:
                # Critical: No contact or >14 days
                urgent.append({
                    "type": "no_contact",
                    "priority": "high",
                    "project_code": p["project_code"],
                    "project_name": p["project_name"],
                    "project_title": p["project_name"],  # For backward compatibility
                    "action": f"Call client - {next_action}",
                    "context": context,
                    "days_since_contact": days,
                    "days_display": days_display
                })
            elif days >= 7:
                # Important: 7-13 days
                needs_attention.append({
                    "type": "follow_up",
                    "project_code": p["project_code"],
                    "project_name": p["project_name"],
                    "project_title": p["project_name"],  # For backward compatibility
                    "action": next_action or "Schedule follow up",
                    "context": context,
                    "days_since_contact": days,
                    "days_display": days_display
                })

        conn.close()

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "urgent": urgent,
            "needs_attention": needs_attention,
            "total_active": len(proposals)
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


@router.get("/dashboard/actions")
async def get_action_items():
    """
    Get all actionable items across the system - the "What Needs Attention" view.

    Returns prioritized list of:
    - Proposals where ball is with us (need to act)
    - Urgent/action-required emails
    - Overdue follow-ups
    - Open RFIs
    - Overdue commitments
    - Pending tasks
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        actions = []

        # 1. PROPOSALS - Ball with us (URGENT if > 7 days)
        cursor.execute("""
            SELECT
                proposal_id,
                project_code,
                project_name,
                current_status as status,
                ball_in_court,
                waiting_for,
                next_action,
                next_action_date,
                days_since_contact,
                last_contact_date
            FROM proposals
            WHERE ball_in_court = 'us'
            AND current_status NOT IN ('Archived', 'Contract Signed', 'Declined', 'Lost', 'Dormant', 'On Hold')
            ORDER BY days_since_contact DESC
            LIMIT 20
        """)
        for row in cursor.fetchall():
            r = dict(row)
            urgency = "critical" if (r.get('days_since_contact') or 0) > 14 else "high" if (r.get('days_since_contact') or 0) > 7 else "medium"
            actions.append({
                "type": "proposal_action",
                "urgency": urgency,
                "project_code": r['project_code'],
                "project_name": r['project_name'],
                "title": f"Ball with us - {r['project_name']}",
                "description": r.get('next_action') or r.get('waiting_for') or f"No contact for {r.get('days_since_contact', '?')} days",
                "days_waiting": r.get('days_since_contact'),
                "action": r.get('next_action') or "Follow up required",
                "due_date": r.get('next_action_date'),
                "link": f"/proposals/{r['project_code']}"
            })

        # 2. PROPOSALS - Stale (ball with them but > 14 days)
        cursor.execute("""
            SELECT
                proposal_id,
                project_code,
                project_name,
                current_status as status,
                ball_in_court,
                waiting_for,
                days_since_contact,
                last_contact_date
            FROM proposals
            WHERE (ball_in_court = 'them' OR ball_in_court IS NULL)
            AND days_since_contact > 14
            AND current_status NOT IN ('Archived', 'Contract Signed', 'Declined', 'Lost', 'Dormant', 'On Hold')
            ORDER BY days_since_contact DESC
            LIMIT 15
        """)
        for row in cursor.fetchall():
            r = dict(row)
            urgency = "high" if (r.get('days_since_contact') or 0) > 21 else "medium"
            actions.append({
                "type": "follow_up",
                "urgency": urgency,
                "project_code": r['project_code'],
                "project_name": r['project_name'],
                "title": f"Follow up needed - {r['project_name']}",
                "description": f"No response for {r.get('days_since_contact', '?')} days" + (f". Waiting for: {r['waiting_for']}" if r.get('waiting_for') else ""),
                "days_waiting": r.get('days_since_contact'),
                "action": "Send follow-up email or call",
                "link": f"/proposals/{r['project_code']}"
            })

        # 3. URGENT EMAILS - Recent emails needing action
        cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                date(e.date) as email_date,
                ec.urgency_level,
                ec.action_required,
                ec.ai_summary,
                p.project_code,
                p.project_name,
                julianday('now') - julianday(e.date) as days_ago
            FROM emails e
            JOIN email_content ec ON e.email_id = ec.email_id
            LEFT JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN proposals p ON epl.proposal_id = p.proposal_id
            WHERE (ec.action_required = 1 OR ec.urgency_level IN ('high', 'critical'))
            AND e.date >= date('now', '-14 days')
            AND e.sender_email NOT LIKE '%@bensley.com%'
            ORDER BY e.date DESC
            LIMIT 10
        """)
        for row in cursor.fetchall():
            r = dict(row)
            urgency = "critical" if r.get('urgency_level') == 'critical' else "high" if r.get('action_required') else "medium"
            actions.append({
                "type": "email_action",
                "urgency": urgency,
                "project_code": r.get('project_code'),
                "project_name": r.get('project_name'),
                "title": f"Email needs response: {r['subject'][:50]}",
                "description": r.get('ai_summary') or f"From {r['sender_email']}",
                "from": r['sender_email'],
                "email_date": r['email_date'],
                "days_ago": round(r.get('days_ago', 0)),
                "action": "Review and respond",
                "link": f"/proposals/{r['project_code']}" if r.get('project_code') else None
            })

        # 4. OPEN RFIs
        cursor.execute("""
            SELECT
                r.rfi_id,
                r.rfi_number,
                r.subject,
                r.date_due,
                r.priority,
                r.status,
                r.project_code,
                p.project_name,
                julianday('now') - julianday(r.date_due) as days_overdue
            FROM rfis r
            LEFT JOIN proposals p ON r.project_code = p.project_code
            WHERE r.status = 'open'
            ORDER BY r.date_due ASC
            LIMIT 10
        """)
        for row in cursor.fetchall():
            r = dict(row)
            is_overdue = (r.get('days_overdue') or 0) > 0
            urgency = "critical" if is_overdue else "high" if r.get('priority') == 'high' else "medium"
            actions.append({
                "type": "rfi",
                "urgency": urgency,
                "project_code": r.get('project_code'),
                "project_name": r.get('project_name'),
                "title": f"RFI {r['rfi_number']}: {(r['subject'] or '')[:40]}",
                "description": f"Due: {r['date_due']}" + (" (OVERDUE)" if is_overdue else ""),
                "due_date": r['date_due'],
                "days_overdue": round(r.get('days_overdue', 0)) if is_overdue else None,
                "action": "Respond to RFI",
                "link": f"/proposals/{r['project_code']}" if r.get('project_code') else "/rfis"
            })

        # 5. OVERDUE COMMITMENTS (our commitments)
        cursor.execute("""
            SELECT
                c.commitment_id,
                c.description,
                c.due_date,
                c.commitment_type,
                c.committed_by,
                p.project_code,
                p.project_name,
                julianday('now') - julianday(c.due_date) as days_overdue
            FROM commitments c
            LEFT JOIN proposals p ON c.project_code = p.project_code
            WHERE c.fulfillment_status = 'pending'
            AND c.commitment_type = 'our_commitment'
            AND c.due_date <= date('now', '+7 days')
            ORDER BY c.due_date ASC
            LIMIT 10
        """)
        for row in cursor.fetchall():
            r = dict(row)
            is_overdue = (r.get('days_overdue') or 0) > 0
            urgency = "critical" if is_overdue else "high"
            actions.append({
                "type": "commitment",
                "urgency": urgency,
                "project_code": r.get('project_code'),
                "project_name": r.get('project_name'),
                "title": f"Commitment due: {r['description'][:40]}",
                "description": f"Due: {r['due_date']}" + (" (OVERDUE)" if is_overdue else "") + (f". By: {r['committed_by']}" if r.get('committed_by') else ""),
                "due_date": r['due_date'],
                "days_overdue": round(r.get('days_overdue', 0)) if is_overdue else None,
                "action": "Fulfill commitment",
                "link": f"/proposals/{r['project_code']}" if r.get('project_code') else None
            })

        # 6. PENDING TASKS (high priority or due soon)
        cursor.execute("""
            SELECT
                t.task_id,
                t.title,
                t.description,
                t.due_date,
                t.priority,
                t.status,
                t.project_code,
                p.project_name,
                julianday('now') - julianday(t.due_date) as days_overdue
            FROM tasks t
            LEFT JOIN proposals p ON t.project_code = p.project_code
            WHERE t.status IN ('pending', 'in_progress')
            AND (t.priority = 'high' OR t.due_date <= date('now', '+3 days'))
            ORDER BY t.due_date ASC
            LIMIT 10
        """)
        for row in cursor.fetchall():
            r = dict(row)
            is_overdue = r.get('due_date') and (r.get('days_overdue') or 0) > 0
            urgency = "critical" if is_overdue else "high" if r.get('priority') == 'high' else "medium"
            actions.append({
                "type": "task",
                "urgency": urgency,
                "project_code": r.get('project_code'),
                "project_name": r.get('project_name'),
                "title": r['title'],
                "description": r.get('description') or f"Due: {r.get('due_date', 'Not set')}",
                "due_date": r.get('due_date'),
                "days_overdue": round(r.get('days_overdue', 0)) if is_overdue else None,
                "action": "Complete task",
                "link": f"/tasks"
            })

        # 7. PROPOSALS NEEDING TO BE SENT (status = Drafting for > 7 days)
        cursor.execute("""
            SELECT
                proposal_id,
                project_code,
                project_name,
                current_status,
                days_in_current_status,
                project_value
            FROM proposals
            WHERE current_status = 'Drafting'
            AND days_in_current_status > 7
            ORDER BY days_in_current_status DESC
            LIMIT 5
        """)
        for row in cursor.fetchall():
            r = dict(row)
            urgency = "high" if (r.get('days_in_current_status') or 0) > 14 else "medium"
            actions.append({
                "type": "proposal_send",
                "urgency": urgency,
                "project_code": r['project_code'],
                "project_name": r['project_name'],
                "title": f"Send proposal - {r['project_name']}",
                "description": f"In drafting for {r.get('days_in_current_status', '?')} days",
                "days_waiting": r.get('days_in_current_status'),
                "action": "Finalize and send proposal",
                "link": f"/proposals/{r['project_code']}"
            })

        conn.close()

        # Sort by urgency (critical > high > medium) then by days_waiting
        urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        actions.sort(key=lambda x: (urgency_order.get(x.get('urgency', 'low'), 3), -(x.get('days_waiting') or x.get('days_overdue') or 0)))

        # Summary counts
        summary = {
            "total": len(actions),
            "critical": len([a for a in actions if a.get('urgency') == 'critical']),
            "high": len([a for a in actions if a.get('urgency') == 'high']),
            "by_type": {}
        }
        for a in actions:
            t = a.get('type', 'other')
            summary["by_type"][t] = summary["by_type"].get(t, 0) + 1

        return {
            "success": True,
            "actions": actions,
            "summary": summary,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PORTFOLIO EXCEPTIONS - Projects needing attention
# ============================================================================

@router.get("/dashboard/portfolio-exceptions")
async def get_portfolio_exceptions():
    """Get all projects with exceptions (overdue invoices, stale, etc.)

    Returns only projects that need attention - healthy projects are counted but not listed.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        exceptions = []

        # Get all active projects AND active proposals (Bill's priority)
        cursor.execute("""
            SELECT DISTINCT
                project_code,
                display_name,
                source_type
            FROM (
                -- Active projects
                SELECT
                    p.project_code,
                    COALESCE(pr.project_name, p.project_title, p.project_code) as display_name,
                    'project' as source_type
                FROM projects p
                LEFT JOIN proposals pr ON p.project_code = pr.project_code
                WHERE p.is_active_project = 1 OR p.status = 'Active'

                UNION

                -- Active proposals (not yet in projects or not marked active)
                SELECT
                    pr.project_code,
                    COALESCE(pr.project_name, pr.project_code) as display_name,
                    'proposal' as source_type
                FROM proposals pr
                WHERE pr.status IN ('Proposal Sent', 'In Discussion', 'Drafting', 'Negotiation', 'Active')
                AND pr.project_code NOT IN (
                    SELECT project_code FROM projects WHERE is_active_project = 1 OR status = 'Active'
                )
            )
        """)
        all_items = cursor.fetchall()
        total_count = len(all_items)

        for proj in all_items:
            project_code = proj['project_code']
            project_name = proj['display_name'] or project_code
            issues = []

            # Check for overdue invoices
            cursor.execute("""
                SELECT COUNT(*) as cnt, SUM(invoice_amount - COALESCE(payment_amount, 0)) as amount
                FROM invoices
                WHERE project_id IN (SELECT project_id FROM projects WHERE project_code = ?)
                AND status NOT IN ('paid', 'cancelled', 'void')
                AND due_date < date('now')
            """, (project_code,))
            overdue = cursor.fetchone()
            if overdue and overdue['cnt'] > 0:
                issues.append({
                    "type": "overdue_invoice",
                    "label": f"{overdue['cnt']} overdue",
                    "severity": "high" if overdue['cnt'] > 1 else "medium",
                    "value": overdue['amount'] or 0
                })

            # Check for unpaid invoices (not overdue yet but outstanding)
            cursor.execute("""
                SELECT COUNT(*) as cnt, SUM(invoice_amount - COALESCE(payment_amount, 0)) as amount
                FROM invoices
                WHERE project_id IN (SELECT project_id FROM projects WHERE project_code = ?)
                AND status NOT IN ('paid', 'cancelled', 'void')
                AND (due_date >= date('now') OR due_date IS NULL)
                AND invoice_amount > COALESCE(payment_amount, 0)
            """, (project_code,))
            unpaid = cursor.fetchone()
            if unpaid and unpaid['cnt'] > 0 and (unpaid['amount'] or 0) > 50000:
                issues.append({
                    "type": "unpaid",
                    "label": f"${int((unpaid['amount'] or 0)/1000)}K due",
                    "severity": "low",
                    "value": unpaid['amount'] or 0
                })

            # Check for overdue deliverables
            cursor.execute("""
                SELECT COUNT(*) as cnt
                FROM deliverables
                WHERE project_code = ?
                AND status NOT IN ('delivered', 'approved', 'completed')
                AND due_date < date('now')
            """, (project_code,))
            overdue_del = cursor.fetchone()
            if overdue_del and overdue_del['cnt'] > 0:
                issues.append({
                    "type": "overdue_deliverable",
                    "label": f"{overdue_del['cnt']} overdue",
                    "severity": "high",
                })

            # Check for stale projects (no email activity in 30+ days)
            cursor.execute("""
                SELECT MAX(e.date_normalized) as last_email
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE epl.project_code = ?
            """, (project_code,))
            last_email = cursor.fetchone()
            if last_email and last_email['last_email']:
                try:
                    last_date = datetime.fromisoformat(last_email['last_email'].replace('Z', '+00:00'))
                    days_since = (datetime.now(last_date.tzinfo) - last_date).days if last_date.tzinfo else (datetime.now() - last_date).days
                    if days_since > 30:
                        issues.append({
                            "type": "stale",
                            "label": f"{days_since}d no contact",
                            "severity": "medium" if days_since < 60 else "high",
                            "days": days_since
                        })
                except (ValueError, TypeError):
                    pass

            # Check for overdue follow-up actions (ball in our court)
            cursor.execute("""
                SELECT next_action, next_action_date, ball_in_court
                FROM proposals
                WHERE project_code = ?
                AND ball_in_court = 'us'
                AND next_action_date IS NOT NULL
                AND next_action_date < date('now')
            """, (project_code,))
            overdue_action = cursor.fetchone()
            if overdue_action:
                try:
                    action_date = datetime.strptime(overdue_action['next_action_date'], '%Y-%m-%d')
                    days_overdue = (datetime.now() - action_date).days
                    action_text = overdue_action['next_action'] or 'Action needed'
                    # Truncate action text for label
                    short_action = action_text[:25] + '...' if len(action_text) > 25 else action_text
                    issues.append({
                        "type": "overdue_action",
                        "label": f"{days_overdue}d overdue: {short_action}",
                        "severity": "high" if days_overdue > 7 else "medium",
                        "days": days_overdue
                    })
                except (ValueError, TypeError):
                    pass

            # Add to exceptions if any issues
            if issues:
                exceptions.append({
                    "project_code": project_code,
                    "project_name": project_name,
                    "issues": issues
                })

        # Sort by severity (projects with high severity issues first)
        def get_max_severity(proj):
            severities = {"high": 0, "medium": 1, "low": 2}
            return min(severities.get(i["severity"], 2) for i in proj["issues"])

        exceptions.sort(key=get_max_severity)

        healthy_count = total_count - len(exceptions)

        return {
            "success": True,
            "exceptions": exceptions,
            "healthy_count": healthy_count,
            "total_count": total_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
