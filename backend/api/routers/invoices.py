"""
Invoices Router - Invoice management endpoints

Endpoints:
    GET /api/invoices/stats - Invoice statistics
    GET /api/invoices/recent - Recent invoices
    GET /api/invoices/outstanding - Outstanding invoices
    GET /api/invoices/aging - Invoice aging report
    GET /api/invoices/by-project/{project_code} - Project invoices
    ... and more
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3

from api.services import financial_service, invoice_service
from api.dependencies import DB_PATH
from api.models import InvoiceCreateRequest, InvoiceUpdateRequest
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["invoices"])


# ============================================================================
# INVOICE STATISTICS
# ============================================================================

@router.get("/invoices/stats")
async def get_invoice_stats():
    """Get invoice statistics"""
    try:
        stats = financial_service.get_invoice_stats()
        return item_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/aging")
async def get_invoice_aging():
    """Get invoice aging breakdown. Returns standardized response."""
    try:
        aging = invoice_service.get_aging_breakdown()
        response = item_response({"aging": aging})
        response["aging"] = aging  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/aging-breakdown")
async def get_detailed_aging_breakdown():
    """Get detailed invoice aging breakdown with amounts. Returns standardized response."""
    try:
        breakdown = financial_service.get_detailed_aging()
        response = item_response({"breakdown": breakdown})
        response["breakdown"] = breakdown  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INVOICE LISTS
# ============================================================================

@router.get("/invoices/recent")
async def get_recent_invoices(limit: int = Query(20, ge=1, le=100)):
    """Get most recent invoices. Returns standardized list response."""
    try:
        invoices = financial_service.get_recent_invoices(limit=limit)
        response = list_response(invoices, len(invoices))
        response["invoices"] = invoices  # Backward compat
        response["count"] = len(invoices)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/outstanding")
async def get_outstanding_invoices(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200)
):
    """Get all outstanding (unpaid) invoices"""
    try:
        result = financial_service.get_outstanding_invoices(page=page, per_page=per_page)
        return list_response(
            result.get('invoices', []),
            result.get('total', 0),
            page,
            per_page
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/outstanding-filtered")
async def get_filtered_outstanding(
    min_days: int = Query(0, ge=0),
    max_days: Optional[int] = None,
    min_amount: float = Query(0, ge=0),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200)
):
    """Get outstanding invoices with filters"""
    try:
        # Get all outstanding invoices and filter in-memory
        all_invoices = invoice_service.get_outstanding_invoices()

        # Apply filters
        filtered = []
        for inv in all_invoices:
            days_overdue = inv.get('days_overdue', 0) or 0
            amount = inv.get('invoice_amount', 0) or 0

            if days_overdue < min_days:
                continue
            if max_days is not None and days_overdue > max_days:
                continue
            if amount < min_amount:
                continue
            filtered.append(inv)

        # Paginate
        total = len(filtered)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = filtered[start:end]

        return list_response(paginated, total, page, per_page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/recent-paid")
async def get_recent_paid_invoices(limit: int = Query(20, ge=1, le=100)):
    """Get recently paid invoices. Returns standardized list response."""
    try:
        invoices = invoice_service.get_recent_paid_invoices(limit=limit)
        response = list_response(invoices, len(invoices))
        response["invoices"] = invoices  # Backward compat
        response["count"] = len(invoices)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/largest-outstanding")
async def get_largest_outstanding(limit: int = Query(10, ge=1, le=50)):
    """Get largest outstanding invoices. Returns standardized list response."""
    try:
        invoices = invoice_service.get_largest_outstanding_invoices(limit=limit)
        response = list_response(invoices, len(invoices))
        response["invoices"] = invoices  # Backward compat
        response["count"] = len(invoices)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/oldest-unpaid-invoices")
async def get_oldest_unpaid(limit: int = Query(10, ge=1, le=50)):
    """Get oldest unpaid invoices. Returns standardized list response."""
    try:
        invoices = financial_service.get_oldest_unpaid_invoices(limit=limit)
        response = list_response(invoices, len(invoices))
        response["invoices"] = invoices  # Backward compat
        response["count"] = len(invoices)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/top-outstanding")
async def get_top_outstanding(limit: int = Query(10, ge=1, le=50)):
    """Get top outstanding invoices by amount. Returns standardized list response."""
    try:
        invoices = invoice_service.get_largest_outstanding_invoices(limit=limit)
        response = list_response(invoices, len(invoices))
        response["invoices"] = invoices  # Backward compat
        response["count"] = len(invoices)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT INVOICES
# ============================================================================

@router.get("/invoices/by-project/{project_code}")
async def get_project_invoices(project_code: str):
    """Get all invoices for a project. Returns standardized list response."""
    try:
        invoices = financial_service.get_invoices_by_project(project_code)
        response = list_response(invoices, len(invoices))
        response["invoices"] = invoices  # Backward compat
        response["count"] = len(invoices)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INVOICE CRUD
# ============================================================================

@router.post("/invoices", status_code=201)
async def create_invoice(request: InvoiceCreateRequest):
    """Create a new invoice"""
    try:
        result = financial_service.create_invoice(
            project_code=request.project_code,
            invoice_number=request.invoice_number,
            amount_usd=request.amount_usd,
            invoice_date=request.invoice_date,
            due_date=request.due_date,
            description=request.description,
            status=request.status
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message'))
        return action_response(True, data=result.get('invoice'), message="Invoice created")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/invoices/{invoice_number}")
async def update_invoice(invoice_number: str, request: InvoiceUpdateRequest):
    """Update an invoice"""
    try:
        updates = request.dict(exclude_unset=True)
        result = financial_service.update_invoice(invoice_number, updates)
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message'))
        return action_response(True, data=result.get('invoice'), message="Invoice updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FINANCIAL ANALYTICS - Revenue Trends & Client Payment Behavior
# ============================================================================

@router.get("/invoices/revenue-trends")
async def get_revenue_trends(months: int = Query(12, ge=1, le=24)):
    """
    Get monthly revenue/collections trends for the past N months.
    Returns invoiced amounts, paid amounts, and collection rates by month.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                strftime('%Y-%m', invoice_date) as month,
                COUNT(*) as invoice_count,
                COALESCE(SUM(invoice_amount), 0) as total_invoiced,
                COALESCE(SUM(CASE WHEN payment_amount > 0 THEN payment_amount ELSE 0 END), 0) as total_paid,
                COUNT(CASE WHEN payment_amount > 0 THEN 1 END) as paid_count,
                AVG(CASE
                    WHEN payment_date IS NOT NULL AND invoice_date IS NOT NULL
                    THEN julianday(payment_date) - julianday(invoice_date)
                END) as avg_days_to_pay
            FROM invoices
            WHERE invoice_date IS NOT NULL
              AND invoice_date >= date('now', '-' || ? || ' months')
            GROUP BY month
            ORDER BY month ASC
        """, (months,))

        rows = cursor.fetchall()

        trends = []
        for row in rows:
            total_inv = row['total_invoiced'] or 0
            total_pd = row['total_paid'] or 0
            trends.append({
                "month": row['month'],
                "invoice_count": row['invoice_count'],
                "total_invoiced": round(total_inv, 2),
                "total_paid": round(total_pd, 2),
                "paid_count": row['paid_count'],
                "collection_rate": round((total_pd / total_inv * 100), 1) if total_inv > 0 else 0,
                "avg_days_to_pay": round(row['avg_days_to_pay'], 0) if row['avg_days_to_pay'] else None
            })

        conn.close()

        return {
            "success": True,
            "data": trends,
            "count": len(trends)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invoices/client-payment-behavior")
async def get_client_payment_behavior(limit: int = Query(10, ge=1, le=50)):
    """
    Get payment behavior analytics by project/client.
    Returns top projects by payments with average days to pay and collection metrics.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.project_code,
                p.project_title as project_name,
                COUNT(i.invoice_id) as invoice_count,
                COALESCE(SUM(i.invoice_amount), 0) as total_invoiced,
                COALESCE(SUM(i.payment_amount), 0) as total_paid,
                COALESCE(SUM(i.invoice_amount) - SUM(COALESCE(i.payment_amount, 0)), 0) as outstanding,
                COUNT(CASE WHEN i.payment_amount > 0 THEN 1 END) as paid_invoice_count,
                AVG(CASE
                    WHEN i.payment_date IS NOT NULL AND i.invoice_date IS NOT NULL
                    THEN julianday(i.payment_date) - julianday(i.invoice_date)
                END) as avg_days_to_pay,
                MIN(i.invoice_date) as first_invoice,
                MAX(i.invoice_date) as last_invoice
            FROM invoices i
            JOIN projects p ON i.project_id = p.project_id
            WHERE i.invoice_amount > 0
            GROUP BY p.project_id
            HAVING total_paid > 0
            ORDER BY total_paid DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()

        clients = []
        for row in rows:
            total_inv = row['total_invoiced'] or 0
            total_pd = row['total_paid'] or 0
            clients.append({
                "project_code": row['project_code'],
                "project_name": row['project_name'],
                "invoice_count": row['invoice_count'],
                "total_invoiced": round(total_inv, 2),
                "total_paid": round(total_pd, 2),
                "outstanding": round(row['outstanding'] or 0, 2),
                "paid_invoice_count": row['paid_invoice_count'],
                "collection_rate": round((total_pd / total_inv * 100), 1) if total_inv > 0 else 0,
                "avg_days_to_pay": round(row['avg_days_to_pay'], 0) if row['avg_days_to_pay'] else None,
                "payment_speed": (
                    "Fast" if row['avg_days_to_pay'] and row['avg_days_to_pay'] < 30
                    else "Normal" if row['avg_days_to_pay'] and row['avg_days_to_pay'] < 60
                    else "Slow" if row['avg_days_to_pay'] else "Unknown"
                ),
                "first_invoice": row['first_invoice'],
                "last_invoice": row['last_invoice']
            })

        conn.close()

        return {
            "success": True,
            "data": clients,
            "count": len(clients)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
