"""
Projects Router - Project management endpoints

Endpoints:
    GET /api/projects/active - List active projects
    GET /api/projects/{project_code} - Get project details
    POST /api/projects - Create a project
    PUT /api/projects/{project_code} - Update a project
    GET /api/projects/{project_code}/financial-summary - Financial summary
    GET /api/projects/{project_code}/contacts - Project contacts
    ... and more
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import sqlite3

from api.services import (
    proposal_service,
    financial_service,
    contract_service,
)
from api.dependencies import DB_PATH
from api.models import ProjectCreateRequest
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["projects"])


# ============================================================================
# PROJECT LIST ENDPOINTS
# ============================================================================

@router.get("/projects/active")
async def get_active_projects():
    """Get all active projects (where first payment received) with invoice data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, c.company_name, p.project_title) as client_name,
                p.total_fee_usd as contract_value,
                p.status,
                p.current_phase as current_phase,
                p.project_id as project_id,
                p.contract_signed_date,
                COALESCE(SUM(i.invoice_amount), 0) as total_invoiced,
                COALESCE(SUM(i.payment_amount), 0) as paid_to_date_usd,
                (p.total_fee_usd - COALESCE(SUM(i.payment_amount), 0)) as outstanding_usd,
                CASE
                    WHEN p.total_fee_usd > 0 THEN
                        ROUND((COALESCE(SUM(i.invoice_amount), 0) / p.total_fee_usd * 100), 1)
                    ELSE 0
                END as percentage_invoiced
            FROM projects p
            LEFT JOIN proposals pr ON p.project_code = pr.project_code
            LEFT JOIN clients c ON p.client_id = c.client_id
            LEFT JOIN invoices i ON p.project_id = i.project_id
            WHERE p.is_active_project = 1 OR p.status IN ('active', 'active_project', 'Active')
            GROUP BY p.project_id, p.project_code, p.project_title, pr.client_company, c.company_name,
                     p.total_fee_usd, p.status, p.current_phase, p.contract_signed_date
            ORDER BY p.project_code DESC
        """)

        projects = []
        for row in cursor.fetchall():
            project = dict(row)
            contract_value = project.get('contract_value') or 0
            total_invoiced = project.get('total_invoiced') or 0
            total_paid = project.get('paid_to_date_usd') or 0
            project['remaining_value'] = contract_value - total_invoiced

            if total_paid > 0:
                if total_invoiced > total_paid:
                    project['payment_status'] = 'outstanding'
                else:
                    project['payment_status'] = 'paid'
            else:
                project['payment_status'] = 'pending'

            projects.append(project)

        conn.close()

        response = list_response(projects, len(projects))
        response["count"] = len(projects)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/linking-list")
async def get_projects_for_linking():
    """Get simplified project list for email linking dropdowns"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT project_code, project_title, client_name, status
            FROM projects
            WHERE project_code IS NOT NULL
            ORDER BY project_code DESC
            LIMIT 500
        """)

        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()

        response = list_response(projects, len(projects))
        response["projects"] = projects  # Backward compat
        response["count"] = len(projects)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT DETAIL ENDPOINTS
# ============================================================================

@router.get("/projects/{project_code}")
async def get_project(project_code: str):
    """Get project details by project code"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM projects WHERE project_code = ?
        """, (project_code,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        return item_response(dict(row))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_code}/financial-summary")
async def get_project_financial_summary(project_code: str):
    """Get financial summary for a project"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.project_id, p.project_code, p.project_title,
                   c.company_name as client_name,
                   p.total_fee_usd as contract_value
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.client_id
            WHERE p.project_code = ?
        """, (project_code,))

        project_row = cursor.fetchone()
        if not project_row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project = dict(project_row)
        project_id = project['project_id']

        # Get invoice totals
        cursor.execute("""
            SELECT
                COALESCE(SUM(invoice_amount), 0) as total_invoiced,
                COALESCE(SUM(payment_amount), 0) as total_paid
            FROM invoices
            WHERE project_id = ?
        """, (project_id,))

        totals = cursor.fetchone()
        conn.close()

        contract_value = project.get('contract_value') or 0
        total_invoiced = totals['total_invoiced'] if totals else 0
        total_paid = totals['total_paid'] if totals else 0

        summary = {
            "project_code": project_code,
            "project_title": project['project_title'],
            "client_name": project['client_name'],
            "contract_value": contract_value,
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "outstanding": total_invoiced - total_paid,
            "remaining_to_invoice": contract_value - total_invoiced,
            "percent_invoiced": round((total_invoiced / contract_value * 100), 1) if contract_value > 0 else 0,
            "percent_paid": round((total_paid / contract_value * 100), 1) if contract_value > 0 else 0
        }
        response = item_response(summary)
        response.update(summary)  # Backward compat - flatten at root
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT CONTACTS
# ============================================================================

@router.get("/projects/{project_code}/contacts")
async def get_project_contacts(project_code: str):
    """Get contacts associated with a project"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get project ID first
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        # Get contacts for this project
        cursor.execute("""
            SELECT c.*
            FROM contacts c
            JOIN project_contacts pc ON c.contact_id = pc.contact_id
            WHERE pc.project_id = ?
            ORDER BY c.name
        """, (project['project_id'],))

        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()

        response = list_response(contacts, len(contacts))
        response["contacts"] = contacts  # Backward compat
        response["count"] = len(contacts)  # Backward compat
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT SCOPE & CONTRACT
# ============================================================================

@router.get("/projects/{project_code}/scope")
async def get_project_scope(project_code: str):
    """Get project scope details"""
    try:
        result = contract_service.get_scope(project_code)
        if not result:
            raise HTTPException(status_code=404, detail=f"Scope for {project_code} not found")
        return item_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_code}/contract")
async def get_project_contract(project_code: str):
    """Get project contract details"""
    try:
        result = contract_service.get_contract(project_code)
        if not result:
            raise HTTPException(status_code=404, detail=f"Contract for {project_code} not found")
        return item_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_code}/fee-breakdown")
async def get_project_fee_breakdown(project_code: str):
    """Get fee breakdown for a project. Returns standardized list response."""
    try:
        result = financial_service.get_fee_breakdown(project_code)
        breakdown = result if isinstance(result, list) else [result] if result else []
        response = list_response(breakdown, len(breakdown))
        response["fee_breakdown"] = result  # Backward compat
        response["breakdowns"] = breakdown  # Frontend expects this key
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_code}/timeline")
async def get_project_timeline(project_code: str):
    """Get project timeline - key dates and milestones. Returns standardized list response."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get project dates
        cursor.execute("""
            SELECT project_id, project_code, project_title, status,
                   first_contact_date, proposal_sent_date, contract_signed_date,
                   contract_start_date, contract_expiry_date, target_completion,
                   date_created
            FROM projects
            WHERE project_code = ?
        """, (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_dict = dict(project)
        project_id = project_dict['project_id']
        timeline = []

        # Add project milestone dates
        date_fields = [
            ('first_contact_date', 'First Contact'),
            ('proposal_sent_date', 'Proposal Sent'),
            ('contract_signed_date', 'Contract Signed'),
            ('contract_start_date', 'Contract Start'),
            ('target_completion', 'Target Completion'),
            ('contract_expiry_date', 'Contract Expiry'),
        ]
        for field, label in date_fields:
            if project_dict.get(field):
                timeline.append({
                    'date': project_dict[field],
                    'event': label,
                    'type': 'milestone'
                })

        # Get invoice dates
        cursor.execute("""
            SELECT invoice_number, invoice_date, payment_date, invoice_amount, status
            FROM invoices
            WHERE project_id = ?
            ORDER BY invoice_date
        """, (project_id,))
        for inv in cursor.fetchall():
            inv_dict = dict(inv)
            if inv_dict.get('invoice_date'):
                timeline.append({
                    'date': inv_dict['invoice_date'],
                    'event': f"Invoice {inv_dict.get('invoice_number', 'N/A')}",
                    'type': 'invoice',
                    'amount': inv_dict.get('invoice_amount'),
                    'status': inv_dict.get('status')
                })
            if inv_dict.get('payment_date'):
                timeline.append({
                    'date': inv_dict['payment_date'],
                    'event': f"Payment for Invoice {inv_dict.get('invoice_number', 'N/A')}",
                    'type': 'payment'
                })

        conn.close()

        # Sort by date
        timeline.sort(key=lambda x: x['date'] if x['date'] else '9999-99-99')

        response = list_response(timeline, len(timeline))
        response["timeline"] = timeline  # Backward compat
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_code}/hierarchy")
async def get_project_hierarchy(project_code: str):
    """Get project financial hierarchy: disciplines → phases → invoices"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get project
        cursor.execute("SELECT * FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_dict = dict(project)
        project_id = project_dict['project_id']

        # Get fee breakdowns grouped by discipline and phase
        cursor.execute("""
            SELECT
                breakdown_id,
                discipline,
                phase,
                phase_fee_usd,
                total_invoiced,
                total_paid
            FROM project_fee_breakdown
            WHERE project_code = ?
            ORDER BY discipline, phase
        """, (project_code,))
        breakdowns = [dict(row) for row in cursor.fetchall()]

        # Get all invoices for this project
        cursor.execute("""
            SELECT
                i.invoice_id,
                i.invoice_number,
                i.invoice_amount,
                i.payment_amount,
                i.status,
                i.invoice_date,
                i.breakdown_id
            FROM invoices i
            WHERE i.project_id = ?
            ORDER BY i.invoice_date DESC
        """, (project_id,))
        invoices = [dict(row) for row in cursor.fetchall()]

        conn.close()

        # Build hierarchy: disciplines → phases → invoices
        disciplines = {}
        total_contract_value = 0
        total_invoiced = 0
        total_paid = 0

        for bd in breakdowns:
            discipline = bd['discipline'] or 'Other'
            phase_fee = bd['phase_fee_usd'] or 0
            phase_invoiced = bd['total_invoiced'] or 0
            phase_paid = bd['total_paid'] or 0

            if discipline not in disciplines:
                disciplines[discipline] = {
                    'total_fee': 0,
                    'total_invoiced': 0,
                    'total_paid': 0,
                    'phases': []
                }

            # Find invoices for this breakdown
            phase_invoices = [inv for inv in invoices if inv['breakdown_id'] == bd['breakdown_id']]

            phase_data = {
                'breakdown_id': bd['breakdown_id'],
                'phase': bd['phase'],
                'phase_fee': phase_fee,
                'total_invoiced': phase_invoiced,
                'total_paid': phase_paid,
                'remaining': phase_fee - phase_invoiced,
                'invoices': phase_invoices
            }

            disciplines[discipline]['phases'].append(phase_data)
            disciplines[discipline]['total_fee'] += phase_fee
            disciplines[discipline]['total_invoiced'] += phase_invoiced
            disciplines[discipline]['total_paid'] += phase_paid

            total_contract_value += phase_fee
            total_invoiced += phase_invoiced
            total_paid += phase_paid

        return {
            "success": True,
            "project_code": project_code,
            "project_name": project_dict.get('project_title'),
            "total_contract_value": total_contract_value,
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "disciplines": disciplines
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE FEES ENDPOINTS
# ============================================================================

from pydantic import BaseModel


class CreatePhaseFeeRequest(BaseModel):
    """Request to create a phase fee breakdown"""
    project_code: str
    scope: str = "general"
    discipline: str
    phase: str
    phase_fee_usd: Optional[float] = None
    percentage_of_total: Optional[float] = None


class UpdatePhaseFeeRequest(BaseModel):
    """Request to update a phase fee breakdown"""
    phase_fee_usd: Optional[float] = None
    percentage_of_total: Optional[float] = None
    status: Optional[str] = None


@router.get("/phase-fees")
async def get_all_phase_fees(
    project_code: Optional[str] = None,
    scope: Optional[str] = None
):
    """Get all phase fee breakdowns with optional filtering"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM project_fee_breakdown WHERE 1=1"
        params = []

        if project_code:
            query += " AND project_code = ?"
            params.append(project_code)
        if scope:
            query += " AND scope = ?"
            params.append(scope)

        query += " ORDER BY project_code, scope, discipline, phase"

        cursor.execute(query, params)
        fees = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "data": fees,
            "phase_fees": fees,
            "count": len(fees)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/phase-fees")
async def create_phase_fee(request: CreatePhaseFeeRequest):
    """Create a new phase fee breakdown"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Generate breakdown_id
        breakdown_id = f"{request.project_code}_{request.scope}_{request.discipline}_{request.phase}"

        # Check if already exists
        cursor.execute(
            "SELECT breakdown_id FROM project_fee_breakdown WHERE breakdown_id = ?",
            (breakdown_id,)
        )
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail=f"Phase fee breakdown {breakdown_id} already exists")

        cursor.execute("""
            INSERT INTO project_fee_breakdown (
                breakdown_id, project_code, scope, discipline, phase,
                phase_fee_usd, percentage_of_total
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            breakdown_id,
            request.project_code,
            request.scope,
            request.discipline,
            request.phase,
            request.phase_fee_usd,
            request.percentage_of_total
        ))

        conn.commit()
        conn.close()

        return action_response(True, data={"breakdown_id": breakdown_id}, message="Phase fee created")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/phase-fees/{breakdown_id}")
async def update_phase_fee(breakdown_id: str, request: UpdatePhaseFeeRequest):
    """Update a phase fee breakdown"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        updates = []
        params = []

        if request.phase_fee_usd is not None:
            updates.append("phase_fee_usd = ?")
            params.append(request.phase_fee_usd)
        if request.percentage_of_total is not None:
            updates.append("percentage_of_total = ?")
            params.append(request.percentage_of_total)
        if request.status is not None:
            updates.append("status = ?")
            params.append(request.status)

        if not updates:
            conn.close()
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(breakdown_id)
        query = f"UPDATE project_fee_breakdown SET {', '.join(updates)} WHERE breakdown_id = ?"

        cursor.execute(query, params)
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if not success:
            raise HTTPException(status_code=404, detail=f"Phase fee {breakdown_id} not found")

        return action_response(True, message="Phase fee updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/phase-fees/{breakdown_id}")
async def delete_phase_fee(breakdown_id: str):
    """Delete a phase fee breakdown"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM project_fee_breakdown WHERE breakdown_id = ?", (breakdown_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if not success:
            raise HTTPException(status_code=404, detail=f"Phase fee {breakdown_id} not found")

        return action_response(True, message="Phase fee deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UNIFIED TIMELINE ENDPOINT
# ============================================================================

@router.get("/projects/{project_code}/unified-timeline")
async def get_unified_timeline(
    project_code: str,
    limit: int = Query(100, ge=1, le=500),
    item_types: Optional[str] = Query(None, description="Comma-separated types: email,transcript,invoice,rfi")
):
    """Get unified timeline combining emails, transcripts, invoices, and RFIs for a project.

    Returns chronological list with each item having:
    - type: email, transcript, invoice, rfi
    - date: ISO date string
    - title: Subject/title of the item
    - summary: Brief description
    - id: Item ID for linking
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # First get project_id from project_code
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project_row = cursor.fetchone()

        if not project_row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_id = project_row['project_id']

        # Parse item_types filter
        type_filter = None
        if item_types:
            type_filter = [t.strip().lower() for t in item_types.split(',')]

        timeline_items = []

        # Get emails (from email_project_links)
        if not type_filter or 'email' in type_filter:
            cursor.execute("""
                SELECT
                    e.email_id as id,
                    'email' as type,
                    e.date,
                    e.subject as title,
                    COALESCE(e.snippet, SUBSTR(e.body_full, 1, 200)) as summary,
                    e.sender_email as sender,
                    epl.confidence,
                    epl.link_method
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                WHERE epl.project_id = ?
                ORDER BY e.date DESC
                LIMIT ?
            """, (project_id, limit))

            for row in cursor.fetchall():
                item = dict(row)
                item['date'] = item.get('date', '')
                timeline_items.append(item)

        # Get transcripts
        if not type_filter or 'transcript' in type_filter:
            cursor.execute("""
                SELECT
                    id,
                    'transcript' as type,
                    COALESCE(meeting_date, recorded_date, created_at) as date,
                    COALESCE(meeting_title, audio_filename, 'Meeting Transcript') as title,
                    COALESCE(summary, 'No summary available') as summary,
                    participants,
                    duration_seconds
                FROM meeting_transcripts
                WHERE project_id = ? OR detected_project_code = ?
                ORDER BY COALESCE(meeting_date, recorded_date, created_at) DESC
                LIMIT ?
            """, (project_id, project_code, limit))

            for row in cursor.fetchall():
                item = dict(row)
                timeline_items.append(item)

        # Get invoices
        if not type_filter or 'invoice' in type_filter:
            cursor.execute("""
                SELECT
                    invoice_id as id,
                    'invoice' as type,
                    COALESCE(invoice_date, '') as date,
                    invoice_number as title,
                    printf('$%.2f - %s', invoice_amount, COALESCE(status, 'unknown')) as summary,
                    invoice_amount,
                    payment_amount,
                    status
                FROM invoices
                WHERE project_id = ?
                ORDER BY invoice_date DESC
                LIMIT ?
            """, (project_id, limit))

            for row in cursor.fetchall():
                item = dict(row)
                timeline_items.append(item)

        # Get RFIs (if table exists)
        if not type_filter or 'rfi' in type_filter:
            try:
                cursor.execute("""
                    SELECT
                        rfi_id as id,
                        'rfi' as type,
                        COALESCE(created_at, '') as date,
                        COALESCE(rfi_number, 'RFI') || ': ' || COALESCE(subject, 'No subject') as title,
                        COALESCE(description, 'No description') as summary,
                        status,
                        priority
                    FROM rfis
                    WHERE project_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (project_id, limit))

                for row in cursor.fetchall():
                    item = dict(row)
                    timeline_items.append(item)
            except sqlite3.OperationalError:
                # RFIs table might not exist or have different schema
                pass

        conn.close()

        # Sort all items by date descending
        def get_date_key(item):
            date_str = item.get('date', '')
            if not date_str:
                return ''
            return date_str

        timeline_items.sort(key=get_date_key, reverse=True)

        # Limit to requested size
        timeline_items = timeline_items[:limit]

        return {
            "success": True,
            "project_code": project_code,
            "timeline": timeline_items,
            "total": len(timeline_items),
            "item_counts": {
                "email": sum(1 for i in timeline_items if i.get('type') == 'email'),
                "transcript": sum(1 for i in timeline_items if i.get('type') == 'transcript'),
                "invoice": sum(1 for i in timeline_items if i.get('type') == 'invoice'),
                "rfi": sum(1 for i in timeline_items if i.get('type') == 'rfi'),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))