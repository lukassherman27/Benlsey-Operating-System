"""
Finance Router - Financial dashboard and metrics endpoints

RBAC: All endpoints require 'executive' or 'finance' role.

Endpoints:
    GET /api/finance/dashboard-metrics - Dashboard financial metrics
    GET /api/finance/recent-payments - Recent payments
    GET /api/finance/projected-invoices - Projected invoices
    GET /api/finance/projects-by-outstanding - Projects by outstanding amount
    GET /api/finance/oldest-unpaid-invoices - Oldest unpaid invoices
    GET /api/finance/projects-by-remaining - Projects by remaining value
"""

from fastapi import APIRouter, Depends, HTTPException, Query
import sqlite3

from api.dependencies import DB_PATH, require_role
from api.helpers import item_response, list_response

# RBAC: All finance endpoints require executive or finance role
finance_access = require_role("executive", "finance")

router = APIRouter(
    prefix="/api",
    tags=["finance"],
    dependencies=[Depends(finance_access)]
)


@router.get("/finance/dashboard-metrics")
async def get_dashboard_metrics():
    """Get financial dashboard metrics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get project totals
        cursor.execute("""
            SELECT
                COALESCE(SUM(p.total_fee_usd), 0) as total_contract_value,
                COUNT(*) as active_project_count
            FROM projects p
            WHERE p.is_active_project = 1
        """)
        project_row = cursor.fetchone()

        # Get invoice totals
        cursor.execute("""
            SELECT
                COALESCE(SUM(invoice_amount), 0) as total_invoiced,
                COALESCE(SUM(payment_amount), 0) as total_paid
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE p.is_active_project = 1
        """)

        invoice_row = cursor.fetchone()

        # Combine metrics
        metrics = {
            'total_contract_value': project_row['total_contract_value'] if project_row else 0,
            'active_project_count': project_row['active_project_count'] if project_row else 0,
            'total_invoiced': invoice_row['total_invoiced'] if invoice_row else 0,
            'total_paid': invoice_row['total_paid'] if invoice_row else 0,
        }
        metrics['total_outstanding'] = metrics['total_invoiced'] - metrics['total_paid']

        # Calculate overdue
        cursor.execute("""
            SELECT COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0) as total_overdue
            FROM invoices
            WHERE status IN ('unpaid', 'partial')
              AND invoice_date < date('now', '-30 days')
        """)
        overdue_row = cursor.fetchone()
        metrics['total_overdue'] = overdue_row['total_overdue'] if overdue_row else 0

        # Calculate remaining
        metrics['total_remaining'] = metrics['total_contract_value'] - metrics['total_invoiced']

        conn.close()

        return {
            "success": True,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/finance/recent-payments")
async def get_recent_payments(limit: int = Query(5, ge=1, le=50)):
    """Get recent payments"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.invoice_id,
                i.invoice_number,
                p.project_code,
                p.project_title as project_name,
                i.payment_date as paid_on,
                i.payment_amount as amount_usd,
                i.status
            FROM invoices i
            LEFT JOIN projects p ON i.project_id = p.project_id
            WHERE i.payment_date IS NOT NULL
              AND i.payment_amount IS NOT NULL
              AND i.payment_amount > 0
            ORDER BY i.payment_date DESC
            LIMIT ?
        """, (limit,))

        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "payments": payments,
            "count": len(payments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/finance/projected-invoices")
async def get_projected_invoices(limit: int = Query(5, ge=1, le=50)):
    """Get projected upcoming invoices"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get projects with remaining value to invoice
        cursor.execute("""
            SELECT
                p.project_code,
                p.project_title,
                p.total_fee_usd,
                COALESCE(inv.total_invoiced, 0) as total_invoiced_usd,
                (p.total_fee_usd - COALESCE(inv.total_invoiced, 0)) as remaining_to_invoice,
                p.current_phase
            FROM projects p
            LEFT JOIN (
                SELECT project_id, SUM(invoice_amount) as total_invoiced
                FROM invoices GROUP BY project_id
            ) inv ON p.project_id = inv.project_id
            WHERE p.is_active_project = 1
              AND (p.total_fee_usd - COALESCE(inv.total_invoiced, 0)) > 0
            ORDER BY remaining_to_invoice DESC
            LIMIT ?
        """, (limit,))

        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "projected_invoices": invoices,
            "count": len(invoices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/finance/projects-by-outstanding")
async def get_projects_by_outstanding(limit: int = Query(5, ge=1, le=50)):
    """Get projects sorted by outstanding balance"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.project_code,
                p.project_title,
                COALESCE(inv.total_invoiced, 0) - COALESCE(inv.total_paid, 0) as outstanding_balance_usd,
                COALESCE(inv.total_invoiced, 0) as total_invoiced_usd,
                COALESCE(inv.total_paid, 0) as total_paid_usd
            FROM projects p
            LEFT JOIN (
                SELECT project_id,
                       SUM(invoice_amount) as total_invoiced,
                       SUM(COALESCE(payment_amount, 0)) as total_paid
                FROM invoices GROUP BY project_id
            ) inv ON p.project_id = inv.project_id
            WHERE (COALESCE(inv.total_invoiced, 0) - COALESCE(inv.total_paid, 0)) > 0
            ORDER BY outstanding_balance_usd DESC
            LIMIT ?
        """, (limit,))

        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "projects": projects,
            "count": len(projects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/finance/oldest-unpaid-invoices")
async def get_oldest_unpaid_invoices(limit: int = Query(5, ge=1, le=50)):
    """Get oldest unpaid invoices"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                i.invoice_id,
                i.invoice_number,
                p.project_code,
                p.project_title as project_name,
                i.invoice_date,
                i.due_date,
                i.invoice_amount,
                CAST(julianday('now') - julianday(i.invoice_date) AS INTEGER) as days_outstanding,
                CASE
                    WHEN i.due_date IS NOT NULL
                    THEN CAST(julianday('now') - julianday(i.due_date) AS INTEGER)
                    ELSE 0
                END as days_overdue,
                (i.invoice_amount - COALESCE(i.payment_amount, 0)) as amount_outstanding,
                CASE
                    WHEN i.due_date IS NULL OR julianday(i.due_date) >= julianday('now') THEN 'Current'
                    WHEN julianday('now') - julianday(i.due_date) <= 30 THEN '1-30 days'
                    WHEN julianday('now') - julianday(i.due_date) <= 60 THEN '31-60 days'
                    WHEN julianday('now') - julianday(i.due_date) <= 90 THEN '61-90 days'
                    ELSE '90+ days'
                END as aging_bucket
            FROM invoices i
            LEFT JOIN projects p ON i.project_id = p.project_id
            WHERE i.status IN ('unpaid', 'partial', 'outstanding')
              AND i.invoice_date IS NOT NULL
              AND (i.invoice_amount - COALESCE(i.payment_amount, 0)) > 0
            ORDER BY i.invoice_date ASC
            LIMIT ?
        """, (limit,))

        invoices = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "invoices": invoices,
            "count": len(invoices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/finance/projects-by-remaining")
async def get_projects_by_remaining(limit: int = Query(5, ge=1, le=50)):
    """Get projects by remaining contract value"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.project_code,
                p.project_title,
                p.total_fee_usd,
                COALESCE(inv.total_invoiced, 0) as total_invoiced_usd,
                (p.total_fee_usd - COALESCE(inv.total_invoiced, 0)) as remaining_value
            FROM projects p
            LEFT JOIN (
                SELECT project_id, SUM(invoice_amount) as total_invoiced
                FROM invoices GROUP BY project_id
            ) inv ON p.project_id = inv.project_id
            WHERE p.is_active_project = 1
              AND (p.total_fee_usd - COALESCE(inv.total_invoiced, 0)) > 0
            ORDER BY remaining_value DESC
            LIMIT ?
        """, (limit,))

        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "projects": projects,
            "count": len(projects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")
