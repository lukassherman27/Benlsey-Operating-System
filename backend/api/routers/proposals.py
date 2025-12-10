"""
Proposals Router - Proposal and proposal-tracker endpoints

Endpoints:
    GET /api/proposals - List all proposals
    GET /api/proposals/stats - Get proposal statistics
    GET /api/proposals/at-risk - Get at-risk proposals
    GET /api/proposals/needs-follow-up - Get proposals needing follow-up
    POST /api/proposals - Create a proposal
    PATCH /api/proposals/{identifier} - Update a proposal
    GET /api/proposal-tracker/list - List proposals for tracker
    GET /api/proposal-tracker/stats - Get tracker statistics
    ... and more
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from api.services import proposal_service, proposal_tracker_service
from api.dependencies import DB_PATH
from api.models import (
    CreateProposalRequest,
    UpdateProposalRequest,
    ProposalStatusUpdateRequest,
)
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["proposals"])


# ============================================================================
# PROPOSALS ENDPOINTS
# ============================================================================

@router.get("/proposals")
async def list_proposals(
    status: Optional[str] = None,
    is_active_project: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("health_score", regex="^(proposal_id|project_code|project_title|status|health_score|days_since_contact|is_active_project|created_at|updated_at)$"),
    sort_order: str = Query("ASC", regex="^(ASC|DESC)$")
):
    """
    List all proposals with optional filtering and pagination
    """
    try:
        result = proposal_service.get_all_proposals(
            status=status,
            is_active_project=is_active_project,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposals: {str(e)}")


@router.get("/proposals/stats")
async def get_proposal_stats():
    """Get proposal statistics"""
    try:
        stats = proposal_service.get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal stats: {str(e)}")


@router.get("/proposals/at-risk")
async def get_at_risk_proposals(
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get proposals at risk (health_score < 50). Returns standardized response."""
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Query proposals table (not projects!)
            cursor.execute("""
                SELECT COUNT(*) FROM proposals
                WHERE health_score IS NOT NULL AND health_score < 50
                AND status NOT IN ('Lost', 'Declined', 'Contract Signed', 'Dormant')
            """)
            total = cursor.fetchone()[0] or 0

            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT
                    proposal_id, project_code, project_name, client_company,
                    health_score, days_since_contact, last_contact_date,
                    next_action, status, project_value,
                    contact_person, created_at, updated_at
                FROM proposals
                WHERE health_score IS NOT NULL AND health_score < 50
                AND status NOT IN ('Lost', 'Declined', 'Contract Signed', 'Dormant')
                ORDER BY health_score ASC
                LIMIT ? OFFSET ?
            """, (per_page, offset))

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_name": row[2],
                    "client_company": row[3],
                    "health_score": row[4],
                    "days_since_contact": row[5],
                    "last_contact_date": row[6],
                    "next_action": row[7],
                    "status": row[8],
                    "project_value": row[9],
                    "contact_person": row[10],
                    "created_at": row[11],
                    "updated_at": row[12]
                })

            data = proposals[:limit] if limit < per_page else proposals
            return list_response(data, total, page, per_page)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get at-risk proposals: {str(e)}")


@router.get("/proposals/needs-follow-up")
async def get_needs_follow_up_proposals(
    min_days: int = Query(14, ge=1),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get proposals needing follow-up (no contact in X days). Returns standardized response."""
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Query proposals table (not projects!)
            cursor.execute("""
                SELECT COUNT(*) FROM proposals
                WHERE days_since_contact >= ?
                AND status NOT IN ('Lost', 'Declined', 'Contract Signed', 'Dormant')
            """, (min_days,))
            total = cursor.fetchone()[0] or 0

            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT
                    proposal_id, project_code, project_name,
                    health_score, days_since_contact, status,
                    project_value, country, updated_at
                FROM proposals
                WHERE days_since_contact >= ?
                AND status NOT IN ('Lost', 'Declined', 'Contract Signed', 'Dormant')
                ORDER BY days_since_contact DESC
                LIMIT ? OFFSET ?
            """, (min_days, per_page, offset))

            proposals = []
            for row in cursor.fetchall():
                proposals.append({
                    "proposal_id": row[0],
                    "project_code": row[1],
                    "project_name": row[2],
                    "health_score": row[3],
                    "days_since_contact": row[4],
                    "status": row[5],
                    "project_value": row[6],
                    "country": row[7],
                    "updated_at": row[8]
                })

            data = proposals[:limit] if limit < per_page else proposals
            response = list_response(data, total, page, per_page)
            response["meta"]["min_days_threshold"] = min_days  # Extra context
            return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get follow-up proposals: {str(e)}")


@router.get("/proposals/weekly-changes")
async def get_weekly_changes(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
):
    """Get proposal pipeline changes for Bill's weekly reports"""
    try:
        result = proposal_service.get_weekly_changes(days=days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get weekly changes: {str(e)}")


@router.post("/proposals", status_code=201)
async def create_proposal(request: CreateProposalRequest):
    """Create a new proposal. Returns standardized action response."""
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Check if project_code already exists
            cursor.execute("SELECT proposal_id FROM projects WHERE project_code = ?", (request.project_code,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Project code '{request.project_code}' already exists")

            cursor.execute("""
                INSERT INTO projects (
                    project_code, project_title, total_fee_usd,
                    proposal_submitted_date, decision_expected_date, win_probability,
                    status, is_active_project, client_name, description,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (
                request.project_code,
                request.project_title,
                request.estimated_fee_usd,
                request.proposal_submitted_date,
                request.decision_expected_date,
                request.win_probability,
                request.status,
                request.is_active_project,
                request.client_name,
                request.description
            ))

            proposal_id = cursor.lastrowid
            conn.commit()

            cursor.execute("""
                SELECT proposal_id, project_code, project_title, status,
                       total_fee_usd, win_probability, is_active_project,
                       proposal_submitted_date, decision_expected_date,
                       client_name, description, created_at
                FROM projects WHERE proposal_id = ?
            """, (proposal_id,))

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to retrieve created proposal")

            proposal = {
                "proposal_id": row[0],
                "project_code": row[1],
                "project_title": row[2],
                "status": row[3],
                "estimated_fee_usd": row[4],
                "win_probability": row[5],
                "is_active_project": row[6],
                "proposal_submitted_date": row[7],
                "decision_expected_date": row[8],
                "client_name": row[9],
                "description": row[10],
                "created_at": row[11]
            }
            return action_response(True, proposal, f"Proposal {request.project_code} created")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create proposal: {str(e)}")


# ============================================================================
# PROPOSAL TRACKER ENDPOINTS
# ============================================================================

@router.get("/proposal-tracker/stats")
async def get_tracker_stats():
    """Get proposal tracker statistics"""
    try:
        stats = proposal_tracker_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tracker stats: {str(e)}")


@router.get("/proposal-tracker/list")
async def get_tracker_list(
    status: Optional[str] = None,
    discipline: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200)
):
    """Get proposals list for tracker view"""
    try:
        result = proposal_tracker_service.get_proposals_list(
            status=status,
            discipline=discipline,
            country=country,
            search=search,
            page=page,
            per_page=per_page
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tracker list: {str(e)}")


@router.get("/proposal-tracker/disciplines")
async def get_tracker_disciplines():
    """Get distinct disciplines for filter dropdown"""
    try:
        disciplines = proposal_tracker_service.get_discipline_stats()
        return {"success": True, "disciplines": disciplines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get disciplines: {str(e)}")


@router.get("/proposal-tracker/countries")
async def get_tracker_countries():
    """Get distinct countries for filter dropdown"""
    try:
        countries = proposal_tracker_service.get_countries_list()
        return {"success": True, "countries": countries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get countries: {str(e)}")


@router.get("/proposal-tracker/{project_code}")
async def get_tracker_proposal(project_code: str):
    """Get single proposal details for tracker. Returns standardized response."""
    try:
        proposal = proposal_tracker_service.get_proposal_by_code(project_code)
        if not proposal:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")
        response = item_response(proposal)
        response.update(proposal)  # Backward compat - flatten fields at root
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal: {str(e)}")


@router.put("/proposal-tracker/{project_code}")
async def update_tracker_proposal(project_code: str, updates: dict):
    """Update proposal in tracker. Returns standardized action response."""
    try:
        result = proposal_tracker_service.update_proposal(project_code, updates)
        if not result:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")
        return action_response(True, result, f"Proposal {project_code} updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update proposal: {str(e)}")


@router.get("/proposal-tracker/{project_code}/history")
async def get_tracker_history(project_code: str):
    """Get proposal status history. Returns standardized list response."""
    try:
        history = proposal_tracker_service.get_status_history(project_code)
        response = list_response(history, len(history))
        response["history"] = history  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/proposal-tracker/{project_code}/emails")
async def get_tracker_emails(project_code: str):
    """Get emails linked to proposal. Returns standardized list response."""
    try:
        emails = proposal_tracker_service.get_email_intelligence(project_code)
        response = list_response(emails, len(emails))
        response["emails"] = emails  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get emails: {str(e)}")


# ============================================================================
# PROPOSAL VERSION TRACKING ENDPOINTS
# ============================================================================

@router.get("/proposals/{project_code}/versions")
async def get_proposal_versions(project_code: str):
    """
    Get all versions of a proposal with documents and fee history.

    Returns:
        - project_code, project_name, client info
        - current_fee, num_versions
        - versions: List of proposal documents with dates
        - fee_changes: List of fee change events

    Example: GET /api/proposals/25%20BK-087/versions
    """
    try:
        from services.proposal_version_service import ProposalVersionService

        svc = ProposalVersionService(DB_PATH)
        result = svc.get_proposal_versions(project_code)

        if not result.get('success'):
            raise HTTPException(status_code=404, detail=result.get('error', 'Not found'))

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")


@router.get("/proposals/{project_code}/fee-history")
async def get_proposal_fee_history(project_code: str):
    """
    Get fee change timeline for a proposal.

    Returns list of fee changes with dates, from initial to current.
    """
    try:
        from services.proposal_version_service import ProposalVersionService

        svc = ProposalVersionService(DB_PATH)
        history = svc.get_fee_history(project_code)

        return {
            "success": True,
            "project_code": project_code,
            "fee_history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fee history: {str(e)}")


@router.get("/proposals/search/by-client")
async def search_proposals_by_client(
    client: str = Query(..., min_length=2, description="Client name to search"),
    include_versions: bool = Query(False, description="Include version counts")
):
    """
    Search proposals by client name or company.

    Answers: "How many proposals did we send to Vahine Island?"

    Example: GET /api/proposals/search/by-client?client=Vahine&include_versions=true
    """
    try:
        from services.proposal_version_service import ProposalVersionService

        svc = ProposalVersionService(DB_PATH)

        if include_versions:
            # Get full summary with version counts
            result = svc.get_version_summary_by_client(client)
        else:
            # Just search
            proposals = svc.search_proposals_by_client(client, include_versions=False)
            result = {
                "success": True,
                "client": client,
                "proposals": proposals,
                "count": len(proposals)
            }

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search proposals: {str(e)}")
