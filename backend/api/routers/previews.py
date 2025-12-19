"""
Preview API Router - Lightweight entity previews for hover cards.

These endpoints return minimal data optimized for hover preview cards.
All responses are cached and designed to be fast (~50ms).
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import sqlite3
import json
from datetime import datetime, timedelta

from api.dependencies import DB_PATH

router = APIRouter(prefix="/api/preview", tags=["previews"])


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =============================================================================
# PROPOSAL PREVIEW
# =============================================================================

@router.get("/proposal/{project_code}")
async def get_proposal_preview(project_code: str):
    """
    Get lightweight proposal preview for hover cards.
    Returns: name, client, value, status, health, ball_in_court, days_since_contact
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.project_code,
                p.project_name,
                p.client_company,
                COALESCE(p.project_value, 0) as project_value,
                p.status,
                COALESCE(p.health_score, 50) as health_score,
                COALESCE(p.ball_in_court, 'mutual') as ball_in_court,
                p.waiting_for,
                p.last_contact_date,
                julianday('now') - julianday(COALESCE(p.last_contact_date, p.created_at)) as days_since_contact
            FROM proposals p
            WHERE p.project_code = ?
            LIMIT 1
        """, (project_code,))

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Proposal not found: {project_code}")

        return {
            "success": True,
            "preview": {
                "project_code": row["project_code"],
                "project_name": row["project_name"] or row["project_code"],
                "client_company": row["client_company"] or "Unknown Client",
                "project_value": float(row["project_value"] or 0),
                "status": row["status"] or "Unknown",
                "health_score": int(row["health_score"] or 50),
                "ball_in_court": row["ball_in_court"] or "mutual",
                "days_since_contact": int(row["days_since_contact"] or 0),
                "waiting_for": row["waiting_for"],
            }
        }
    finally:
        conn.close()


# =============================================================================
# PROJECT PREVIEW
# =============================================================================

@router.get("/project/{project_code}")
async def get_project_preview(project_code: str):
    """
    Get lightweight project preview for hover cards.
    Returns: name, client, contract value, paid, outstanding, health, days_since_activity
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Get project with financial summary
        cursor.execute("""
            SELECT
                p.project_code,
                COALESCE(p.project_title, pr.project_name) as project_title,
                COALESCE(pr.client_company, c.company_name, 'Unknown Client') as client_name,
                COALESCE(p.total_fee_usd, pr.project_value, 0) as total_fee_usd,
                COALESCE(
                    (SELECT SUM(payment_amount) FROM invoices i WHERE i.project_id = p.project_id),
                    0
                ) as total_paid,
                COALESCE(
                    (SELECT SUM(invoice_amount - COALESCE(payment_amount, 0))
                     FROM invoices i
                     WHERE i.project_id = p.project_id AND i.status != 'paid'),
                    0
                ) as outstanding
            FROM projects p
            LEFT JOIN proposals pr ON p.project_code = pr.project_code
            LEFT JOIN clients c ON p.client_id = c.client_id
            WHERE p.project_code = ?
            LIMIT 1
        """, (project_code,))

        row = cursor.fetchone()

        if not row:
            # Try to find in proposals (might be a proposal, not project)
            cursor.execute("""
                SELECT
                    project_code,
                    project_name as project_title,
                    client_company as client_name,
                    COALESCE(project_value, 0) as total_fee_usd,
                    0 as total_paid,
                    0 as outstanding
                FROM proposals
                WHERE project_code = ?
                LIMIT 1
            """, (project_code,))
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_code}")

        # Get days since last activity (email or invoice)
        cursor.execute("""
            SELECT MAX(last_date) as last_activity FROM (
                SELECT MAX(e.date) as last_date
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE epl.project_code = ?
                UNION ALL
                SELECT MAX(i.invoice_date) as last_date
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.project_code = ?
            )
        """, (project_code, project_code))

        activity_row = cursor.fetchone()
        days_since_activity = 0
        if activity_row and activity_row["last_activity"]:
            try:
                last_activity = datetime.strptime(activity_row["last_activity"][:10], "%Y-%m-%d")
                days_since_activity = (datetime.now() - last_activity).days
            except:
                days_since_activity = 0

        # Calculate health status
        outstanding = float(row["outstanding"] or 0)
        health_status = "healthy"
        if outstanding > 0:
            # Check for overdue invoices
            cursor.execute("""
                SELECT COUNT(*) as overdue_count
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.project_code = ?
                AND i.due_date < date('now')
                AND i.status != 'paid'
            """, (project_code,))
            overdue = cursor.fetchone()
            if overdue and overdue["overdue_count"] > 0:
                health_status = "at_risk" if overdue["overdue_count"] > 2 else "attention"

        return {
            "success": True,
            "preview": {
                "project_code": row["project_code"],
                "project_title": row["project_title"] or row["project_code"],
                "client_name": row["client_name"] or "Unknown Client",
                "total_fee_usd": float(row["total_fee_usd"] or 0),
                "total_paid": float(row["total_paid"] or 0),
                "outstanding": outstanding,
                "health_status": health_status,
                "days_since_activity": days_since_activity,
            }
        }
    finally:
        conn.close()


# =============================================================================
# CONTACT PREVIEW
# =============================================================================

@router.get("/contact/{contact_id}")
async def get_contact_preview(contact_id: int):
    """
    Get lightweight contact preview for hover cards.
    Returns: name, email, company, role, email_count, last_contact, is_primary
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        # First try contacts table
        cursor.execute("""
            SELECT
                c.contact_id,
                c.name,
                c.email,
                c.company,
                c.role,
                c.is_primary_contact as is_primary,
                (SELECT COUNT(*) FROM emails e WHERE e.sender_email = c.email OR e.to_address LIKE '%' || c.email || '%') as email_count,
                (SELECT MAX(date) FROM emails e WHERE e.sender_email = c.email) as last_contact_date
            FROM contacts c
            WHERE c.contact_id = ?
            LIMIT 1
        """, (contact_id,))

        row = cursor.fetchone()

        if not row:
            # Try contact_project_mappings
            cursor.execute("""
                SELECT
                    mapping_id as contact_id,
                    contact_name as name,
                    contact_email as email,
                    '' as company,
                    '' as role,
                    is_primary_contact as is_primary,
                    email_count,
                    last_email_date as last_contact_date
                FROM contact_project_mappings
                WHERE mapping_id = ?
                LIMIT 1
            """, (contact_id,))
            row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Contact not found: {contact_id}")

        return {
            "success": True,
            "preview": {
                "contact_id": row["contact_id"],
                "name": row["name"] or "Unknown",
                "email": row["email"] or "",
                "company": row["company"] or "",
                "role": row["role"] or "",
                "email_count": int(row["email_count"] or 0),
                "last_contact_date": row["last_contact_date"],
                "is_primary": bool(row["is_primary"]),
            }
        }
    finally:
        conn.close()


# =============================================================================
# EMAIL PREVIEW
# =============================================================================

@router.get("/email/{email_id}")
async def get_email_preview(email_id: int):
    """
    Get lightweight email preview for hover cards.
    Returns: subject, sender, date, ai_summary, sentiment, urgency, key_points
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_name,
                e.sender_email,
                e.date,
                ec.ai_summary,
                ec.sentiment,
                ec.urgency_level,
                ec.key_points
            FROM emails e
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE e.email_id = ?
            LIMIT 1
        """, (email_id,))

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail=f"Email not found: {email_id}")

        # Parse key_points JSON
        key_points = []
        if row["key_points"]:
            try:
                key_points = json.loads(row["key_points"])
                if isinstance(key_points, list):
                    key_points = key_points[:5]  # Limit to 5 points
            except:
                key_points = []

        return {
            "success": True,
            "preview": {
                "email_id": row["email_id"],
                "subject": row["subject"] or "(No Subject)",
                "sender_name": row["sender_name"] or "",
                "sender_email": row["sender_email"] or "",
                "date": row["date"] or "",
                "ai_summary": row["ai_summary"],
                "sentiment": row["sentiment"],
                "urgency_level": row["urgency_level"],
                "key_points": key_points,
            }
        }
    finally:
        conn.close()
