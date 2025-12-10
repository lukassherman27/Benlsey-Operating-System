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
import sqlite3

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


@router.get("/proposals/needs-attention")
async def get_proposals_needs_attention():
    """
    Get proposals needing follow-up, grouped by urgency tier.

    Returns proposals where WE sent the last email and haven't heard back.
    Tiers: critical (90+ days), high (30-90), medium (14-30), watch (7-14)

    Excludes: Lost, Declined, Contract Signed, Dormant
    """
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Get proposals with email activity analysis
            cursor.execute("""
                WITH email_activity AS (
                    SELECT
                        epl.proposal_id,
                        MAX(e.date) as last_email_date,
                        MAX(CASE WHEN e.sender_email LIKE '%@bensley.com%' THEN e.date END) as our_last_email,
                        MAX(CASE WHEN e.sender_email NOT LIKE '%@bensley.com%' THEN e.date END) as client_last_email,
                        COUNT(*) as email_count,
                        (SELECT sender_email FROM emails e2
                         JOIN email_proposal_links epl2 ON e2.email_id = epl2.email_id
                         WHERE epl2.proposal_id = epl.proposal_id
                         ORDER BY e2.date DESC LIMIT 1) as last_sender,
                        (SELECT subject FROM emails e3
                         JOIN email_proposal_links epl3 ON e3.email_id = epl3.email_id
                         WHERE epl3.proposal_id = epl.proposal_id
                         ORDER BY e3.date DESC LIMIT 1) as last_subject
                    FROM email_proposal_links epl
                    JOIN emails e ON epl.email_id = e.email_id
                    GROUP BY epl.proposal_id
                )
                SELECT
                    p.proposal_id,
                    p.project_code,
                    p.project_name,
                    p.status,
                    p.client_company,
                    p.contact_person,
                    p.contact_email,
                    p.project_value,
                    ea.last_email_date,
                    ea.our_last_email,
                    ea.client_last_email,
                    ea.email_count,
                    ea.last_sender,
                    ea.last_subject,
                    CAST(julianday('now') - julianday(ea.last_email_date) AS INTEGER) as days_since_contact,
                    CASE
                        WHEN ea.last_sender LIKE '%@bensley.com%' THEN 'us'
                        ELSE 'client'
                    END as last_sender_type
                FROM proposals p
                LEFT JOIN email_activity ea ON p.proposal_id = ea.proposal_id
                WHERE p.status NOT IN ('Lost', 'Declined', 'Contract Signed', 'Dormant')
                AND ea.last_email_date IS NOT NULL
                ORDER BY days_since_contact DESC
            """)

            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            # Group by urgency tier - only include where WE sent last
            tiers = {
                "critical": [],  # 90+ days
                "high": [],      # 30-90 days
                "medium": [],    # 14-30 days
                "watch": []      # 7-14 days
            }

            for row in rows:
                proposal = dict(zip(columns, row))
                days = proposal.get('days_since_contact')

                if days is None or proposal.get('last_sender_type') != 'us':
                    continue

                if days >= 90:
                    tiers["critical"].append(proposal)
                elif days >= 30:
                    tiers["high"].append(proposal)
                elif days >= 14:
                    tiers["medium"].append(proposal)
                elif days >= 7:
                    tiers["watch"].append(proposal)

            # Summary stats
            total_needing_attention = sum(len(t) for t in tiers.values())

            return {
                "success": True,
                "summary": {
                    "total": total_needing_attention,
                    "critical": len(tiers["critical"]),
                    "high": len(tiers["high"]),
                    "medium": len(tiers["medium"]),
                    "watch": len(tiers["watch"])
                },
                "tiers": tiers,
                "generated_at": datetime.now().isoformat()
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposals needing attention: {str(e)}")


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


# ============================================================================
# PROPOSAL TIMELINE & STAKEHOLDERS
# ============================================================================

@router.get("/proposals/{project_code}/timeline")
async def get_proposal_timeline(
    project_code: str,
    limit: int = Query(50, ge=1, le=500, description="Number of items to return")
):
    """
    Get unified timeline for a proposal combining emails, meetings, and events.

    Returns chronological list of activities sorted by date (most recent first).
    Each item includes: type, date, title, summary, id

    Example: GET /api/proposals/25%20BK-033/timeline
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get proposal_id from project_code
        cursor.execute("SELECT proposal_id, project_name FROM proposals WHERE project_code = ?", (project_code,))
        proposal_row = cursor.fetchone()

        if not proposal_row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        proposal_id = proposal_row['proposal_id']
        project_name = proposal_row['project_name']

        timeline_items = []

        # Get emails linked to this proposal
        cursor.execute("""
            SELECT
                e.email_id as id,
                'email' as type,
                e.date,
                e.subject as title,
                COALESCE(e.snippet, SUBSTR(e.body_full, 1, 200)) as summary,
                e.sender_email,
                e.sender_name,
                epl.confidence_score,
                epl.match_method
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            WHERE epl.proposal_id = ?
            ORDER BY e.date DESC
            LIMIT ?
        """, (proposal_id, limit))

        for row in cursor.fetchall():
            timeline_items.append(dict(row))

        # Get meeting transcripts linked to this proposal
        cursor.execute("""
            SELECT
                id,
                'meeting' as type,
                COALESCE(meeting_date, recorded_date, created_at) as date,
                COALESCE(meeting_title, audio_filename, 'Meeting Transcript') as title,
                COALESCE(summary, 'No summary available') as summary,
                participants,
                duration_seconds
            FROM meeting_transcripts
            WHERE proposal_id = ? OR detected_project_code = ?
            ORDER BY COALESCE(meeting_date, recorded_date, created_at) DESC
            LIMIT ?
        """, (proposal_id, project_code, limit))

        for row in cursor.fetchall():
            timeline_items.append(dict(row))

        # Get proposal events
        cursor.execute("""
            SELECT
                event_id as id,
                'event' as type,
                event_date as date,
                title,
                COALESCE(description, event_type) as summary,
                event_type,
                location,
                attendees,
                is_confirmed,
                completed,
                outcome
            FROM proposal_events
            WHERE proposal_id = ? OR project_code = ?
            ORDER BY event_date DESC
            LIMIT ?
        """, (proposal_id, project_code, limit))

        for row in cursor.fetchall():
            timeline_items.append(dict(row))

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
            "project_name": project_name,
            "timeline": timeline_items,
            "total": len(timeline_items),
            "item_counts": {
                "email": sum(1 for i in timeline_items if i.get('type') == 'email'),
                "meeting": sum(1 for i in timeline_items if i.get('type') == 'meeting'),
                "event": sum(1 for i in timeline_items if i.get('type') == 'event'),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal timeline: {str(e)}")


@router.get("/proposals/{project_code}/stakeholders")
async def get_proposal_stakeholders(project_code: str):
    """
    Get stakeholders/contacts for a proposal.

    Returns list of contacts with their role, company, email, etc.
    If proposal_stakeholders table is empty, derives contacts from emails.

    Example: GET /api/proposals/25%20BK-033/stakeholders
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get proposal_id from project_code
        cursor.execute("SELECT proposal_id, project_name FROM proposals WHERE project_code = ?", (project_code,))
        proposal_row = cursor.fetchone()

        if not proposal_row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        proposal_id = proposal_row['proposal_id']
        project_name = proposal_row['project_name']

        # Try to get stakeholders from proposal_stakeholders table
        cursor.execute("""
            SELECT
                stakeholder_id as contact_id,
                name,
                email,
                role,
                company,
                phone,
                whatsapp,
                is_primary,
                relationship_strength,
                communication_preference,
                notes,
                last_contact_date
            FROM proposal_stakeholders
            WHERE proposal_id = ? OR project_code = ?
            ORDER BY is_primary DESC, name
        """, (proposal_id, project_code))

        stakeholders = [dict(row) for row in cursor.fetchall()]

        # If no stakeholders found, derive from emails
        if not stakeholders:
            cursor.execute("""
                SELECT DISTINCT
                    NULL as contact_id,
                    e.sender_name as name,
                    e.sender_email as email,
                    'Client' as role,
                    NULL as company,
                    NULL as phone,
                    NULL as whatsapp,
                    0 as is_primary,
                    NULL as relationship_strength,
                    NULL as communication_preference,
                    'Derived from email activity' as notes,
                    MAX(e.date) as last_contact_date
                FROM emails e
                JOIN email_proposal_links epl ON e.email_id = epl.email_id
                WHERE epl.proposal_id = ?
                AND e.sender_email NOT LIKE '%@bensley.com%'
                GROUP BY e.sender_email, e.sender_name
                ORDER BY MAX(e.date) DESC
                LIMIT 20
            """, (proposal_id,))

            stakeholders = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "project_name": project_name,
            "stakeholders": stakeholders,
            "count": len(stakeholders)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal stakeholders: {str(e)}")
