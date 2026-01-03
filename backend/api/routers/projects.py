"""
Projects Router - Project management endpoints

RBAC:
    - All endpoints require authentication
    - PMs only see projects they are assigned to
    - Financial data (contract values, invoices) hidden from PMs
    - Executive/Finance can see all data

Endpoints:
    GET /api/projects/active - List active projects
    GET /api/projects/{project_code} - Get project details
    ... and more
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import sqlite3

from api.services import (
    proposal_service,
    financial_service,
    contract_service,
)
from api.dependencies import (
    DB_PATH,
    get_db,
    get_current_user,
    get_current_user_optional,
    get_user_access_level,
)
from api.models import ProjectCreateRequest
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["projects"])


# ============================================================================
# RBAC HELPERS
# ============================================================================

def get_pm_assigned_projects(staff_id: int, db: sqlite3.Connection) -> List[str]:
    """Get list of project codes assigned to a PM."""
    cursor = db.cursor()
    cursor.execute("""
        SELECT DISTINCT project_code
        FROM project_team
        WHERE staff_id = ? AND is_active = 1
    """, (staff_id,))
    return [row[0] for row in cursor.fetchall()]


def filter_financial_data(data: dict, user: dict) -> dict:
    """Remove financial fields from response for PM/staff users."""
    access_level = get_user_access_level(user)

    # Only PMs and staff have financial data hidden
    if access_level not in ("pm", "staff"):
        return data

    # Fields to hide
    financial_fields = [
        "contract_value", "contract_value_usd", "total_fee_usd",
        "total_invoiced", "total_paid", "paid_to_date_usd",
        "outstanding", "outstanding_usd", "remaining_value",
        "remaining_to_invoice", "invoice_amount", "payment_amount",
        "total_contract_value", "percent_invoiced", "percent_paid",
        "percentage_invoiced"
    ]

    filtered = dict(data)
    for field in financial_fields:
        if field in filtered:
            filtered[field] = None
    return filtered


def can_access_project(user: dict, project_code: str, db: sqlite3.Connection) -> bool:
    """Check if user can access a specific project."""
    access_level = get_user_access_level(user)

    # Executive, admin, finance can see all
    if access_level in ("executive", "admin", "finance"):
        return True

    # PMs can only see assigned projects
    if access_level == "pm":
        staff_id = user.get("staff_id")
        assigned = get_pm_assigned_projects(staff_id, db)
        return project_code in assigned

    # Staff have no project access by default
    return False


# ============================================================================
# PROJECT LIST ENDPOINTS
# ============================================================================

@router.get("/projects/active")
async def get_active_projects(
    user: dict = Depends(get_current_user_optional),
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Get all active projects with invoice data.

    RBAC:
    - Executive/Finance: See all projects with full financial data
    - PM: See only assigned projects, financial data hidden
    - Staff: No access
    - Unauthenticated: See all projects (temporary until auth is fixed)
    """
    try:
        # Handle unauthenticated requests - show all data while auth is broken
        access_level = get_user_access_level(user) if user else "executive"
        cursor = db.cursor()

        # Staff have no project access (only when authenticated)
        if user and access_level == "staff":
            return list_response([], 0)

        # Build base query
        base_query = """
            SELECT
                p.project_code,
                p.project_title,
                COALESCE(pr.client_company, p.client_company, p.project_title) as client_name,
                p.total_fee_usd as contract_value,
                p.status,
                p.project_phase as current_phase,
                p.project_id as project_id,
                p.contract_signed_date,
                p.country,
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
            LEFT JOIN invoices i ON p.project_id = i.project_id
            WHERE (p.is_active_project = 1 OR p.status IN ('active', 'active_project', 'Active'))
        """

        params = []

        # PM filtering - only see assigned projects (when authenticated)
        if user and access_level == "pm":
            staff_id = user.get("staff_id")
            assigned = get_pm_assigned_projects(staff_id, db)
            if not assigned:
                return list_response([], 0)
            placeholders = ",".join("?" * len(assigned))
            base_query += f" AND p.project_code IN ({placeholders})"
            params = assigned

        base_query += """
            GROUP BY p.project_id, p.project_code, p.project_title, pr.client_company, p.client_company,
                     p.total_fee_usd, p.status, p.project_phase, p.contract_signed_date, p.country
            ORDER BY p.project_code DESC
        """

        cursor.execute(base_query, params)

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

            # Filter financial data for PM/staff (only when authenticated)
            if user:
                project = filter_financial_data(project, user)
            projects.append(project)

        response = list_response(projects, len(projects))
        response["count"] = len(projects)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/projects/linking-list")
async def get_projects_for_linking():
    """Get simplified project list for email linking dropdowns"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                project_code as code,
                project_title as name,
                status,
                COALESCE(is_active_project, 0) as is_active_project
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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/projects/{project_code}/financial-summary")
async def get_project_financial_summary(project_code: str):
    """Get financial summary for a project"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # First try to find in projects table
        cursor.execute("""
            SELECT p.project_id, p.project_code, p.project_title,
                   p.project_title as project_name,
                   COALESCE(p.client_company, p.project_title) as client_name,
                   p.total_fee_usd as contract_value,
                   p.total_fee_usd as contract_value_usd,
                   p.total_fee_usd as total_fee_usd,
                   p.project_phase as current_phase,
                   p.status,
                   p.contract_signed_date,
                   p.city,
                   p.country
            FROM projects p
            WHERE p.project_code = ?
        """, (project_code,))

        project_row = cursor.fetchone()

        # If not found in projects, try proposals (for pre-contract proposals)
        if not project_row:
            cursor.execute("""
                SELECT
                    NULL as project_id,
                    project_code,
                    project_name as project_title,
                    project_name,
                    client_company as client_name,
                    total_value as contract_value,
                    total_value as contract_value_usd,
                    total_value as total_fee_usd,
                    status as current_phase,
                    status,
                    NULL as contract_signed_date,
                    city,
                    country
                FROM proposals
                WHERE project_code = ?
            """, (project_code,))
            project_row = cursor.fetchone()

        if not project_row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project = dict(project_row)

        # Get invoice totals using project_code (project_id is NULL in invoices table)
        cursor.execute("""
            SELECT
                COALESCE(SUM(invoice_amount), 0) as total_invoiced,
                COALESCE(SUM(payment_amount), 0) as total_paid
            FROM invoices
            WHERE project_code = ?
        """, (project_code,))
        totals = cursor.fetchone()
        total_invoiced = totals['total_invoiced'] if totals else 0
        total_paid = totals['total_paid'] if totals else 0

        conn.close()

        contract_value = project.get('contract_value') or 0

        summary = {
            "project_code": project_code,
            "project_title": project.get('project_title'),
            "project_name": project.get('project_name') or project.get('project_title'),
            "client_name": project.get('client_name'),
            "contract_value": contract_value,
            "contract_value_usd": contract_value,
            "total_fee_usd": contract_value,
            "current_phase": project.get('current_phase'),
            "status": project.get('status'),
            "contract_signed_date": project.get('contract_signed_date'),
            "city": project.get('city'),
            "country": project.get('country'),
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "paid_to_date_usd": total_paid,
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
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# PROJECT CONTACTS
# ============================================================================

@router.get("/projects/{project_code}/contacts")
async def get_project_contacts(project_code: str):
    """
    Get contacts associated with a project.

    Returns contacts from:
    1. contact_project_mappings (derived from email activity)
    2. project_contact_links (manually linked or AI suggested)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get contacts from contact_project_mappings (email-derived)
        cursor.execute("""
            SELECT
                cpm.contact_email as email,
                cpm.contact_name as name,
                cpm.email_count,
                cpm.first_email_date,
                cpm.last_email_date,
                cpm.is_primary_contact,
                c.company,
                c.role,
                c.phone,
                'email_activity' as source
            FROM contact_project_mappings cpm
            LEFT JOIN contacts c ON cpm.contact_email = c.email
            WHERE cpm.project_code = ?
            ORDER BY cpm.email_count DESC, cpm.is_primary_contact DESC
        """, (project_code,))

        contacts = [dict(row) for row in cursor.fetchall()]

        # Also check proposals table for main contact
        cursor.execute("""
            SELECT contact_email, contact_person, client_company
            FROM proposals WHERE project_code = ?
        """, (project_code,))
        proposal = cursor.fetchone()

        if proposal and proposal['contact_email']:
            # Check if main contact is already in list
            existing_emails = {c['email'] for c in contacts}
            if proposal['contact_email'] not in existing_emails:
                contacts.insert(0, {
                    'email': proposal['contact_email'],
                    'name': proposal['contact_person'],
                    'company': proposal['client_company'],
                    'is_primary_contact': 1,
                    'source': 'proposal',
                    'email_count': 0
                })

        conn.close()

        response = list_response(contacts, len(contacts))
        response["contacts"] = contacts
        response["count"] = len(contacts)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/projects/{project_code}/phases")
async def get_project_phases(project_code: str):
    """
    Get project phases with status for phase progress visualization.

    Returns phases grouped by discipline with completion status.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get project_id
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_id = project['project_id']

        # Get all phases for this project with invoice totals
        cursor.execute("""
            SELECT
                cp.phase_id,
                cp.discipline,
                cp.phase_name,
                cp.phase_order,
                cp.phase_fee_usd,
                cp.invoiced_amount_usd,
                cp.paid_amount_usd,
                cp.status,
                cp.start_date,
                cp.expected_completion_date,
                cp.actual_completion_date,
                -- Calculate totals from invoices if not in phase record
                COALESCE(cp.invoiced_amount_usd,
                    (SELECT COALESCE(SUM(i.invoice_amount), 0)
                     FROM invoices i
                     WHERE i.project_id = cp.project_id
                       AND i.discipline = cp.discipline
                       AND i.phase = cp.phase_name)
                ) as total_invoiced,
                COALESCE(cp.paid_amount_usd,
                    (SELECT COALESCE(SUM(i.amount_paid), 0)
                     FROM invoices i
                     WHERE i.project_id = cp.project_id
                       AND i.discipline = cp.discipline
                       AND i.phase = cp.phase_name)
                ) as total_paid
            FROM contract_phases cp
            WHERE cp.project_id = ?
            ORDER BY cp.discipline, cp.phase_order
        """, (project_id,))

        phases = []
        for row in cursor.fetchall():
            phase_dict = dict(row)

            # Determine status based on invoicing if not explicitly set
            if phase_dict['status'] in ('pending', None):
                total_invoiced = phase_dict.get('total_invoiced', 0) or 0
                total_paid = phase_dict.get('total_paid', 0) or 0
                phase_fee = phase_dict.get('phase_fee_usd', 0) or 0

                if phase_fee > 0 and total_paid >= phase_fee:
                    phase_dict['status'] = 'completed'
                elif total_invoiced > 0:
                    phase_dict['status'] = 'in_progress'
                else:
                    phase_dict['status'] = 'pending'

            phases.append(phase_dict)

        conn.close()

        # Group by discipline
        by_discipline = {}
        for phase in phases:
            disc = phase.get('discipline', 'Unknown')
            if disc not in by_discipline:
                by_discipline[disc] = []
            by_discipline[disc].append(phase)

        return {
            "success": True,
            "project_code": project_code,
            "phases": phases,
            "by_discipline": by_discipline,
            "total": len(phases)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# PHASE FEES ENDPOINTS
# ============================================================================

from pydantic import BaseModel, Field


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


class PhaseTimelineUpdate(BaseModel):
    """Request model for updating phase timeline fields (Issue #242)."""
    contract_duration_months: Optional[int] = None
    contract_end_date: Optional[str] = None
    sd_allocated_months: Optional[int] = None
    sd_start_date: Optional[str] = None
    sd_deadline: Optional[str] = None
    sd_actual_completion: Optional[str] = None
    dd_allocated_months: Optional[int] = None
    dd_start_date: Optional[str] = None
    dd_deadline: Optional[str] = None
    dd_actual_completion: Optional[str] = None
    cd_allocated_months: Optional[int] = None
    cd_start_date: Optional[str] = None
    cd_deadline: Optional[str] = None
    cd_actual_completion: Optional[str] = None
    ca_allocated_months: Optional[int] = None
    ca_start_date: Optional[str] = None
    ca_deadline: Optional[str] = None
    ca_actual_completion: Optional[str] = None


def _calculate_phase_status(start: str, deadline: str, actual: str) -> str:
    """Calculate status for a phase based on dates."""
    from datetime import date
    today = date.today().isoformat()
    if actual:
        return "completed"
    if not start:
        return "not_started"
    if start > today:
        return "not_started"
    if deadline and deadline < today:
        return "overdue"
    return "in_progress"


@router.get("/projects/{project_code}/phase-timeline")
async def get_project_phase_timeline(project_code: str):
    """Get phase timeline for a project (Issue #242)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT project_code, project_title,
                   contract_duration_months, contract_end_date,
                   contract_start_date, contract_expiry_date,
                   sd_allocated_months, sd_start_date, sd_deadline, sd_actual_completion,
                   dd_allocated_months, dd_start_date, dd_deadline, dd_actual_completion,
                   cd_allocated_months, cd_start_date, cd_deadline, cd_actual_completion,
                   ca_allocated_months, ca_start_date, ca_deadline, ca_actual_completion
            FROM projects WHERE project_code = ?
        """, (project_code,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")
        data = dict(row)
        phases = {}
        for phase in ['sd', 'dd', 'cd', 'ca']:
            start = data.get(f'{phase}_start_date')
            deadline = data.get(f'{phase}_deadline')
            actual = data.get(f'{phase}_actual_completion')
            phases[phase] = {
                'allocated_months': data.get(f'{phase}_allocated_months'),
                'start_date': start,
                'deadline': deadline,
                'actual_completion': actual,
                'status': _calculate_phase_status(start, deadline, actual)
            }
        return {
            "success": True,
            "project_code": project_code,
            "project_title": data.get('project_title'),
            "contract": {
                "duration_months": data.get('contract_duration_months'),
                "start_date": data.get('contract_start_date'),
                "end_date": data.get('contract_end_date') or data.get('contract_expiry_date'),
            },
            "phases": phases
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.patch("/projects/{project_code}/phase-timeline")
async def update_project_phase_timeline(project_code: str, request: PhaseTimelineUpdate):
    """Update phase timeline fields for a project (Issue #242)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")
        updates = []
        params = []
        fields = [
            'contract_duration_months', 'contract_end_date',
            'sd_allocated_months', 'sd_start_date', 'sd_deadline', 'sd_actual_completion',
            'dd_allocated_months', 'dd_start_date', 'dd_deadline', 'dd_actual_completion',
            'cd_allocated_months', 'cd_start_date', 'cd_deadline', 'cd_actual_completion',
            'ca_allocated_months', 'ca_start_date', 'ca_deadline', 'ca_actual_completion',
        ]
        request_dict = request.model_dump(exclude_unset=True)
        for field in fields:
            if field in request_dict:
                updates.append(f"{field} = ?")
                params.append(request_dict[field])
        if not updates:
            conn.close()
            raise HTTPException(status_code=400, detail="No fields to update")
        params.append(project_code)
        query = f"UPDATE projects SET {', '.join(updates)} WHERE project_code = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return {"success": True, "message": "Phase timeline updated", "fields_updated": list(request_dict.keys())}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# UNIFIED TIMELINE ENDPOINT
# ============================================================================

@router.get("/projects/{project_code}/unified-timeline")
async def get_unified_timeline(
    project_code: str,
    limit: int = Query(100, ge=1, le=500),
    item_types: Optional[str] = Query(None, description="Comma-separated types: email,transcript,invoice,rfi"),
    person: Optional[str] = Query(None, description="Filter by person (sender email or name)"),
    date_from: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)")
):
    """Get unified timeline combining emails, transcripts, invoices, and RFIs for a project.

    Returns chronological list with each item having:
    - type: email, transcript, invoice, rfi
    - date: ISO date string
    - title: Subject/title of the item
    - summary: Brief description
    - id: Item ID for linking
    - email_category: For emails, internal/client/external
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

        # Bensley internal domains
        internal_domains = ['bensley.com', 'bensley.co.id']

        # Get emails (from email_project_links)
        if not type_filter or 'email' in type_filter:
            # Build query with optional filters
            email_query = """
                SELECT
                    e.email_id as id,
                    'email' as type,
                    e.date,
                    e.subject as title,
                    COALESCE(e.snippet, SUBSTR(e.body_full, 1, 200)) as summary,
                    e.sender_email as sender,
                    e.sender_name,
                    e.recipient_emails,
                    ec.category,
                    e.folder,
                    epl.confidence,
                    epl.link_method
                FROM emails e
                JOIN email_project_links epl ON e.email_id = epl.email_id
                LEFT JOIN email_content ec ON e.email_id = ec.email_id
                WHERE epl.project_id = ?
            """
            params = [project_id]

            # Add person filter
            if person:
                email_query += " AND (e.sender_email LIKE ? OR e.sender_name LIKE ? OR e.recipient_emails LIKE ?)"
                person_pattern = f"%{person}%"
                params.extend([person_pattern, person_pattern, person_pattern])

            # Add date filters
            if date_from:
                email_query += " AND e.date >= ?"
                params.append(date_from)
            if date_to:
                email_query += " AND e.date <= ?"
                params.append(date_to + " 23:59:59")

            email_query += " ORDER BY e.date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(email_query, params)

            for row in cursor.fetchall():
                item = dict(row)
                item['date'] = item.get('date', '')

                # Determine email_category (internal/external)
                sender = (item.get('sender') or '').lower()
                is_internal = any(domain in sender for domain in internal_domains)

                # Check category field for more context
                category = item.get('category', '') or ''

                if is_internal or category == 'internal':
                    item['email_category'] = 'internal'
                elif category in ['contract', 'design', 'financial', 'meeting', 'administrative']:
                    # These are likely project-related client communications
                    item['email_category'] = 'client'
                else:
                    item['email_category'] = 'external'

                # Determine direction
                if item.get('folder') == 'SENT' or item.get('folder') == 'Sent':
                    item['direction'] = 'sent'
                else:
                    item['direction'] = 'received'

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

        # Extract unique people (for filter dropdown)
        people_set = set()
        for item in timeline_items:
            if item.get('type') == 'email':
                sender = item.get('sender_name') or item.get('sender')
                if sender:
                    # Clean up sender - remove email-style formatting
                    sender_clean = sender.split('<')[0].strip().strip('"')
                    if sender_clean and '@' not in sender_clean:
                        people_set.add(sender_clean)
            elif item.get('type') == 'transcript':
                participants = item.get('participants', '')
                if participants:
                    for p in participants.split(','):
                        p_clean = p.strip()
                        if p_clean:
                            people_set.add(p_clean)

        unique_people = sorted(list(people_set))

        # Count email categories
        email_category_counts = {
            "internal": sum(1 for i in timeline_items if i.get('type') == 'email' and i.get('email_category') == 'internal'),
            "client": sum(1 for i in timeline_items if i.get('type') == 'email' and i.get('email_category') == 'client'),
            "external": sum(1 for i in timeline_items if i.get('type') == 'email' and i.get('email_category') == 'external'),
        }

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
            },
            "email_category_counts": email_category_counts,
            "unique_people": unique_people,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")

# ============================================================================
# PROJECT TEAM ENDPOINT
# ============================================================================

@router.get("/projects/{project_code}/team")
async def get_project_team(project_code: str):
    """
    Get team assignments for a project from contact_project_mappings.
    
    Returns list of team members with their roles and disciplines.
    Uses contact_project_mappings table which has 119+ records.
    
    Example: GET /api/projects/25%20BK-033/team
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get team members from contact_project_mappings
        cursor.execute("""
            SELECT 
                cpm.contact_email,
                cpm.contact_name as name,
                c.role,
                c.position as discipline,
                c.company,
                c.phone,
                cpm.email_count,
                cpm.first_email_date,
                cpm.last_email_date,
                cpm.is_primary_contact,
                c.contact_id
            FROM contact_project_mappings cpm
            LEFT JOIN contacts c ON cpm.contact_email = c.email
            WHERE cpm.project_code = ?
            ORDER BY cpm.is_primary_contact DESC, cpm.email_count DESC, cpm.contact_name
        """, (project_code,))
        
        team_members = []
        by_discipline = {}

        for row in cursor.fetchall():
            member = dict(row)
            # Clean up the data
            member['name'] = member.get('name') or 'Unknown'
            member['role'] = member.get('role') or 'Team Member'
            discipline = member.get('discipline') or 'General'
            member['discipline'] = discipline

            # Remap contact fields for frontend compatibility
            member['contact_id'] = member.get('contact_id')
            member['email'] = member.get('contact_email')
            member['email_count'] = member.get('email_count') or 0
            member['is_primary'] = member.get('is_primary_contact') or 0

            team_members.append(member)

            # Group by discipline for frontend
            if discipline not in by_discipline:
                by_discipline[discipline] = []
            by_discipline[discipline].append(member)

        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "team": team_members,
            "by_discipline": by_discipline,
            "count": len(team_members)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/projects/{project_code}/schedule")
async def get_project_schedule(project_code: str, days: int = 30):
    """
    Get schedule entries for a project showing who worked when.

    Returns schedule entries from schedule_entries table with staff names.
    Useful for tracking actual work days per phase.

    Example: GET /api/projects/25%20BK-033/schedule?days=365
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get schedule entries for this project
        cursor.execute("""
            SELECT
                se.entry_id,
                se.work_date as schedule_date,
                tm.full_name as staff_name,
                tm.nickname,
                se.discipline,
                se.phase,
                se.task_description as activity_type,
                1 as hours_worked
            FROM schedule_entries se
            LEFT JOIN team_members tm ON se.member_id = tm.member_id
            WHERE se.project_code LIKE ?
              AND se.work_date >= date('now', '-' || ? || ' days')
              AND se.is_on_leave = 0
              AND se.is_unassigned = 0
            ORDER BY se.work_date DESC
        """, (f"%{project_code}%", days))

        entries = []
        staff_set = set()
        phases_set = set()

        for row in cursor.fetchall():
            entry = dict(row)
            # Use nickname or full name
            entry['staff_name'] = entry.get('nickname') or entry.get('staff_name') or 'Unknown'
            entries.append(entry)
            if entry.get('staff_name'):
                staff_set.add(entry['staff_name'])
            if entry.get('phase'):
                phases_set.add(entry['phase'])

        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "days": days,
            "entries": entries,
            "summary": {
                "total_entries": len(entries),
                "staff_involved": list(staff_set),
                "phases_worked": list(phases_set)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/projects/{project_code}/schedule-team")
async def get_project_schedule_team(project_code: str):
    """Get Bensley staff assigned to project from schedule_entries (internal team, not clients)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tm.member_id, tm.full_name, tm.office, tm.discipline,
                   se.phase, se.task_description, COUNT(*) as work_days,
                   MAX(se.work_date) as last_work_date
            FROM schedule_entries se
            JOIN team_members tm ON se.member_id = tm.member_id
            WHERE se.project_code = ? OR se.project_name LIKE ?
            GROUP BY tm.member_id
            ORDER BY work_days DESC, tm.full_name
        """, (project_code, f"%{project_code.split()[1] if ' ' in project_code else project_code}%"))
        team = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"success": True, "project_code": project_code, "team": team, "count": len(team)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# TEAM ASSIGNMENT ENDPOINTS (Issue #190)
# ============================================================================

# Project roles for team assignments
PROJECT_ROLES = [
    "Project Lead",
    "Project Manager",
    "Designer",
    "Draftsperson",
    "Admin Support",
]


@router.get("/staff")
async def get_staff_list():
    """
    Get list of active Bensley staff for team assignment dropdown.

    Returns all active staff members sorted by name.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                staff_id,
                first_name,
                last_name,
                nickname,
                email,
                role,
                department,
                office
            FROM staff
            WHERE is_active = 1
            ORDER BY first_name, last_name
        """)

        staff = []
        for row in cursor.fetchall():
            s = dict(row)
            # Create display name
            name_parts = [s.get('first_name', '')]
            if s.get('last_name'):
                name_parts.append(s['last_name'])
            s['display_name'] = ' '.join(name_parts)
            if s.get('nickname'):
                s['display_name'] += f" ({s['nickname']})"
            staff.append(s)

        conn.close()

        return {
            "success": True,
            "staff": staff,
            "count": len(staff),
            "roles": PROJECT_ROLES
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/projects/{project_code}/assignments")
async def get_project_assignments(project_code: str):
    """
    Get explicit team assignments for a project from project_team table.

    Returns staff members assigned to this project with their roles.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                pt.id as assignment_id,
                pt.staff_id,
                s.first_name,
                s.last_name,
                s.nickname,
                s.email,
                s.department,
                s.office,
                pt.role_custom as role,
                pt.is_active,
                pt.start_date,
                pt.notes,
                pt.created_at
            FROM project_team pt
            JOIN staff s ON pt.staff_id = s.staff_id
            WHERE pt.project_code = ?
              AND pt.staff_id IS NOT NULL
              AND pt.is_active = 1
            ORDER BY
                CASE pt.role_custom
                    WHEN 'Project Lead' THEN 1
                    WHEN 'Project Manager' THEN 2
                    WHEN 'Designer' THEN 3
                    WHEN 'Draftsperson' THEN 4
                    ELSE 5
                END,
                s.first_name
        """, (project_code,))

        assignments = []
        for row in cursor.fetchall():
            a = dict(row)
            # Create display name
            name_parts = [a.get('first_name', '')]
            if a.get('last_name'):
                name_parts.append(a['last_name'])
            a['display_name'] = ' '.join(name_parts)
            assignments.append(a)

        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "assignments": assignments,
            "count": len(assignments),
            "roles": PROJECT_ROLES
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


class AddTeamMemberRequest(BaseModel):
    """Request to add a team member to a project."""
    staff_id: int
    role: str
    notes: Optional[str] = None


@router.post("/projects/{project_code}/assignments")
async def add_project_assignment(project_code: str, request: AddTeamMemberRequest):
    """
    Add a staff member to a project with a role.

    Creates a new entry in project_team table.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if assignment already exists
        cursor.execute("""
            SELECT id FROM project_team
            WHERE project_code = ? AND staff_id = ? AND is_active = 1
        """, (project_code, request.staff_id))

        if cursor.fetchone():
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Staff member is already assigned to this project"
            )

        # Verify staff exists
        cursor.execute("SELECT staff_id FROM staff WHERE staff_id = ?", (request.staff_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Staff member not found")

        # Create assignment
        cursor.execute("""
            INSERT INTO project_team (project_code, staff_id, role_custom, notes, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (project_code, request.staff_id, request.role, request.notes))

        assignment_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Team member added successfully",
            "assignment_id": assignment_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


class UpdateTeamMemberRequest(BaseModel):
    """Request to update a team member's role."""
    role: Optional[str] = None
    notes: Optional[str] = None


@router.put("/projects/{project_code}/assignments/{assignment_id}")
async def update_project_assignment(
    project_code: str,
    assignment_id: int,
    request: UpdateTeamMemberRequest
):
    """
    Update a team member's role on a project.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Build update query dynamically
        updates = []
        values = []

        if request.role is not None:
            updates.append("role_custom = ?")
            values.append(request.role)

        if request.notes is not None:
            updates.append("notes = ?")
            values.append(request.notes)

        if not updates:
            conn.close()
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = datetime('now')")
        values.extend([project_code, assignment_id])

        cursor.execute(f"""
            UPDATE project_team
            SET {', '.join(updates)}
            WHERE project_code = ? AND id = ?
        """, values)

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Assignment not found")

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Assignment updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/projects/{project_code}/assignments/{assignment_id}")
async def remove_project_assignment(project_code: str, assignment_id: int):
    """
    Remove a team member from a project.

    Sets is_active = 0 (soft delete).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_team
            SET is_active = 0, updated_at = datetime('now')
            WHERE project_code = ? AND id = ?
        """, (project_code, assignment_id))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Assignment not found")

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Team member removed from project"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# DAILY WORK ENDPOINTS (Issue #244)
# ============================================================================

class DailyWorkSubmission(BaseModel):
    """Request to submit daily work."""
    work_date: str
    description: str
    task_type: Optional[str] = None  # 'drawing', 'model', 'presentation', etc.
    discipline: Optional[str] = None  # 'Architecture', 'Interior', 'Landscape', etc.
    phase: Optional[str] = None  # 'Concept', 'SD', 'DD', 'CD', 'CA'
    hours_spent: Optional[float] = None
    staff_id: Optional[int] = None
    staff_name: Optional[str] = None
    attachments: Optional[List[dict]] = None  # [{file_id, filename}]


class DailyWorkReview(BaseModel):
    """Request to review daily work (Bill/Brian)."""
    review_status: str  # 'reviewed', 'needs_revision', 'approved'
    review_comments: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None


@router.post("/projects/{project_code}/daily-work")
async def submit_daily_work(project_code: str, request: DailyWorkSubmission):
    """
    Submit daily work for a project.

    Junior architects use this to log their daily work with optional file attachments.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get project_id
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_id = project['project_id']

        # Convert attachments to JSON string
        import json
        attachments_json = json.dumps(request.attachments) if request.attachments else None

        cursor.execute("""
            INSERT INTO daily_work (
                project_id, project_code, work_date, description,
                task_type, discipline, phase, hours_spent,
                staff_id, staff_name, attachments, review_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (
            project_id, project_code, request.work_date, request.description,
            request.task_type, request.discipline, request.phase, request.hours_spent,
            request.staff_id, request.staff_name, attachments_json
        ))

        daily_work_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Daily work submitted successfully",
            "daily_work_id": daily_work_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/projects/{project_code}/daily-work")
async def get_project_daily_work(
    project_code: str,
    status: Optional[str] = Query(None, description="Filter by review_status"),
    staff_id: Optional[int] = Query(None, description="Filter by staff"),
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get daily work submissions for a project.

    Supports filtering by status, staff, and date range.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT
                daily_work_id, project_code, work_date, submitted_at,
                description, task_type, discipline, phase, hours_spent,
                staff_id, staff_name, attachments,
                reviewer_id, reviewer_name, review_status, review_comments, reviewed_at
            FROM daily_work
            WHERE project_code = ?
        """
        params = [project_code]

        if status:
            query += " AND review_status = ?"
            params.append(status)

        if staff_id:
            query += " AND staff_id = ?"
            params.append(staff_id)

        if date_from:
            query += " AND work_date >= ?"
            params.append(date_from)

        if date_to:
            query += " AND work_date <= ?"
            params.append(date_to)

        query += " ORDER BY work_date DESC, submitted_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        import json
        submissions = []
        for row in cursor.fetchall():
            item = dict(row)
            # Parse attachments JSON
            if item.get('attachments'):
                try:
                    item['attachments'] = json.loads(item['attachments'])
                except:
                    item['attachments'] = []
            else:
                item['attachments'] = []
            submissions.append(item)

        # Get summary stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN review_status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN review_status = 'reviewed' THEN 1 ELSE 0 END) as reviewed,
                SUM(CASE WHEN review_status = 'needs_revision' THEN 1 ELSE 0 END) as needs_revision,
                SUM(CASE WHEN review_status = 'approved' THEN 1 ELSE 0 END) as approved
            FROM daily_work
            WHERE project_code = ?
        """, (project_code,))
        stats = dict(cursor.fetchone())

        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "submissions": submissions,
            "count": len(submissions),
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/daily-work/{daily_work_id}")
async def get_daily_work_detail(daily_work_id: int):
    """Get a single daily work submission with full details."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM daily_work WHERE daily_work_id = ?", (daily_work_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"Daily work {daily_work_id} not found")

        import json
        item = dict(row)
        if item.get('attachments'):
            try:
                item['attachments'] = json.loads(item['attachments'])
            except:
                item['attachments'] = []

        return {"success": True, "data": item}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.patch("/daily-work/{daily_work_id}/review")
async def review_daily_work(daily_work_id: int, request: DailyWorkReview):
    """
    Add review to daily work submission.

    Used by Bill/Brian to provide feedback on junior architect work.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verify submission exists
        cursor.execute("SELECT daily_work_id FROM daily_work WHERE daily_work_id = ?", (daily_work_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Daily work {daily_work_id} not found")

        cursor.execute("""
            UPDATE daily_work
            SET review_status = ?,
                review_comments = ?,
                reviewer_id = ?,
                reviewer_name = ?,
                reviewed_at = datetime('now')
            WHERE daily_work_id = ?
        """, (
            request.review_status,
            request.review_comments,
            request.reviewer_id,
            request.reviewer_name,
            daily_work_id
        ))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"Daily work marked as {request.review_status}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.patch("/daily-work/{daily_work_id}")
async def update_daily_work(daily_work_id: int, request: DailyWorkSubmission):
    """Update a daily work submission (before review)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        import json
        attachments_json = json.dumps(request.attachments) if request.attachments else None

        cursor.execute("""
            UPDATE daily_work
            SET work_date = ?,
                description = ?,
                task_type = ?,
                discipline = ?,
                phase = ?,
                hours_spent = ?,
                attachments = ?
            WHERE daily_work_id = ?
        """, (
            request.work_date, request.description, request.task_type,
            request.discipline, request.phase, request.hours_spent,
            attachments_json, daily_work_id
        ))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Daily work {daily_work_id} not found")

        conn.commit()
        conn.close()

        return {"success": True, "message": "Daily work updated"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/daily-work/{daily_work_id}")
async def delete_daily_work(daily_work_id: int):
    """Delete a daily work submission."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM daily_work WHERE daily_work_id = ?", (daily_work_id,))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Daily work {daily_work_id} not found")

        conn.commit()
        conn.close()

        return {"success": True, "message": "Daily work deleted"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# PROJECT PROGRESS ENDPOINTS (Issue #246)
# ============================================================================

@router.get("/projects/{project_code}/progress")
async def get_project_progress(project_code: str):
    """
    Get comprehensive project progress including per-phase breakdown.

    Returns overall progress, phase-by-phase progress with task/deliverable counts,
    and timeline status (behind/on_track/ahead).
    """
    from services.progress_calculator import get_progress_calculator

    try:
        calculator = get_progress_calculator(DB_PATH)
        result = calculator.get_project_progress(project_code)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


class UpdatePhaseProgressRequest(BaseModel):
    """Request to update phase progress."""
    progress_percent: float = Field(..., ge=0, le=100)
    status: Optional[str] = None


@router.patch("/projects/{project_code}/phases/{phase_id}/progress")
async def update_phase_progress(
    project_code: str,
    phase_id: int,
    request: UpdatePhaseProgressRequest
):
    """
    Update progress for a specific project phase.

    Used by PMs to manually update phase completion percentage.
    """
    from services.progress_calculator import get_progress_calculator

    try:
        calculator = get_progress_calculator(DB_PATH)
        success = calculator.update_phase_progress(
            phase_id=phase_id,
            progress_percent=request.progress_percent,
            status=request.status
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"Phase {phase_id} not found")

        return {
            "success": True,
            "message": f"Phase progress updated to {request.progress_percent}%"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/projects/progress-summary")
async def get_projects_progress_summary(
    project_codes: Optional[str] = Query(None, description="Comma-separated project codes")
):
    """
    Get progress summary for multiple projects.

    Useful for dashboard views showing portfolio-wide progress.
    """
    from services.progress_calculator import get_progress_calculator

    try:
        calculator = get_progress_calculator(DB_PATH)

        codes = None
        if project_codes:
            codes = [c.strip() for c in project_codes.split(",")]

        results = calculator.get_progress_summary(codes)

        return {
            "success": True,
            "projects": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# PROJECT HEALTH ENDPOINT (Issue #197)
# ============================================================================

@router.get("/projects/{project_code}/health")
async def get_project_health(project_code: str):
    """
    Calculate and return project health score.

    Health is a weighted average of:
    - Invoice payment status (30%) - overdue invoices reduce score
    - RFI response time (20%) - open RFIs > 14 days reduce score
    - Activity recency (20%) - days since last email activity
    - Deliverable status (30%) - overdue deliverables reduce score

    Returns:
    - health_score: 0-100
    - status: "healthy" (>70), "warning" (40-70), "critical" (<40)
    - issues: List of specific problems
    - metrics: Breakdown by category
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get project_id
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project = cursor.fetchone()
        if not project:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project {project_code} not found")

        project_id = project['project_id']
        issues = []

        # 1. Invoice Health (30%)
        cursor.execute("""
            SELECT
                COUNT(*) as overdue_count,
                COALESCE(SUM(invoice_amount - COALESCE(payment_amount, 0)), 0) as overdue_amount
            FROM invoices
            WHERE project_id = ?
              AND status NOT IN ('paid', 'cancelled')
              AND due_date < date('now')
        """, (project_id,))
        invoice_data = cursor.fetchone()
        overdue_invoices = invoice_data['overdue_count'] or 0
        overdue_amount = invoice_data['overdue_amount'] or 0

        if overdue_invoices > 0:
            invoice_health = max(0, 100 - (overdue_invoices * 25))
            issues.append({
                "type": "overdue_invoice",
                "message": f"{overdue_invoices} invoice{'s' if overdue_invoices > 1 else ''} overdue (${overdue_amount:,.0f})",
                "severity": "high" if overdue_invoices > 2 or overdue_amount > 50000 else "medium"
            })
        else:
            invoice_health = 100

        # 2. RFI Health (20%)
        cursor.execute("""
            SELECT COUNT(*) as open_rfis,
                   SUM(CASE WHEN julianday('now') - julianday(created_at) > 14 THEN 1 ELSE 0 END) as stale_rfis
            FROM rfis
            WHERE project_id = ? AND status = 'open'
        """, (project_id,))
        rfi_data = cursor.fetchone()
        open_rfis = rfi_data['open_rfis'] or 0
        stale_rfis = rfi_data['stale_rfis'] or 0

        if stale_rfis > 0:
            rfi_health = max(0, 100 - (stale_rfis * 20))
            issues.append({
                "type": "stale_rfi",
                "message": f"{stale_rfis} RFI{'s' if stale_rfis > 1 else ''} open > 14 days",
                "severity": "medium"
            })
        elif open_rfis > 3:
            rfi_health = 80
            issues.append({
                "type": "open_rfis",
                "message": f"{open_rfis} open RFIs pending response",
                "severity": "low"
            })
        else:
            rfi_health = 100

        # 3. Activity Health (20%)
        cursor.execute("""
            SELECT MAX(e.date) as last_email_date
            FROM emails e
            JOIN email_project_links epl ON e.email_id = epl.email_id
            WHERE epl.project_code = ?
        """, (project_code,))
        activity_data = cursor.fetchone()
        last_email = activity_data['last_email_date'] if activity_data else None

        if last_email:
            from datetime import datetime
            try:
                last_date = datetime.fromisoformat(last_email.replace('Z', '+00:00'))
                days_since = (datetime.now(last_date.tzinfo) - last_date).days if last_date.tzinfo else (datetime.now() - last_date).days
            except:
                days_since = 30

            if days_since > 30:
                activity_health = max(0, 100 - ((days_since - 30) * 2))
                issues.append({
                    "type": "inactive",
                    "message": f"No email activity in {days_since} days",
                    "severity": "medium" if days_since > 60 else "low"
                })
            elif days_since > 14:
                activity_health = 80
            else:
                activity_health = 100
        else:
            activity_health = 50
            issues.append({
                "type": "no_emails",
                "message": "No email activity linked to project",
                "severity": "low"
            })

        # 4. Deliverable Health (30%)
        cursor.execute("""
            SELECT
                COUNT(*) as overdue_count
            FROM deliverables
            WHERE project_id = ?
              AND status NOT IN ('delivered', 'approved', 'cancelled')
              AND due_date < date('now')
        """, (project_id,))
        deliverable_data = cursor.fetchone()
        overdue_deliverables = deliverable_data['overdue_count'] or 0

        if overdue_deliverables > 0:
            deliverable_health = max(0, 100 - (overdue_deliverables * 15))
            issues.append({
                "type": "overdue_deliverable",
                "message": f"{overdue_deliverables} deliverable{'s' if overdue_deliverables > 1 else ''} overdue",
                "severity": "high" if overdue_deliverables > 3 else "medium"
            })
        else:
            deliverable_health = 100

        conn.close()

        # Calculate weighted health score
        health_score = round(
            (invoice_health * 0.30) +
            (rfi_health * 0.20) +
            (activity_health * 0.20) +
            (deliverable_health * 0.30)
        )

        # Determine status
        if health_score >= 70:
            status = "healthy"
        elif health_score >= 40:
            status = "warning"
        else:
            status = "critical"

        # Sort issues by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 2))

        return {
            "success": True,
            "project_code": project_code,
            "health_score": health_score,
            "status": status,
            "issues": issues,
            "metrics": {
                "invoice_health": invoice_health,
                "rfi_health": rfi_health,
                "activity_health": activity_health,
                "deliverable_health": deliverable_health
            },
            "weights": {
                "invoice": 0.30,
                "rfi": 0.20,
                "activity": 0.20,
                "deliverable": 0.30
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")
