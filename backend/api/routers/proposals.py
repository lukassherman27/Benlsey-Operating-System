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
        return {"success": True, "stats": stats}  # Frontend expects {success, stats}
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
        from backend.services.proposal_version_service import ProposalVersionService

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
        from backend.services.proposal_version_service import ProposalVersionService

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
        from backend.services.proposal_version_service import ProposalVersionService

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


@router.get("/proposals/{project_code}/conversation")
async def get_proposal_conversation(project_code: str):
    """
    Get conversation view for a proposal - emails formatted for iMessage-style display.

    Returns emails with sender_category (bill/brian/lukas/mink/client) and
    body content for conversation threading. Excludes internal emails.

    Example: GET /api/proposals/25%20BK-033/conversation
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get proposal_id from project_code
        cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (project_code,))
        proposal_row = cursor.fetchone()

        if not proposal_row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        proposal_id = proposal_row['proposal_id']

        # Get emails with sender_category for conversation view
        # Exclude internal-to-internal emails to show only external correspondence
        cursor.execute("""
            SELECT
                e.email_id,
                e.date,
                e.subject,
                e.sender_email,
                COALESCE(e.sender_category,
                    CASE
                        WHEN e.sender_email LIKE '%bill@bensley%' THEN 'bill'
                        WHEN e.sender_email LIKE '%bsherman@bensley%' THEN 'brian'
                        WHEN e.sender_email LIKE '%lukas@bensley%' THEN 'lukas'
                        WHEN e.sender_email LIKE '%mink@bensley%' THEN 'mink'
                        WHEN e.sender_email LIKE '%@bensley.com%' THEN 'bensley_other'
                        ELSE 'client'
                    END
                ) as sender_category,
                COALESCE(e.snippet, SUBSTR(e.body_full, 1, 300)) as body_preview,
                e.body_full,
                e.has_attachments,
                e.email_direction
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            WHERE epl.proposal_id = ?
              AND (e.email_direction IS NULL
                   OR e.email_direction NOT IN ('internal_to_internal', 'INTERNAL'))
            ORDER BY e.date ASC
        """, (proposal_id,))

        emails = []
        for row in cursor.fetchall():
            email_dict = dict(row)
            # Convert has_attachments to boolean
            email_dict['has_attachments'] = bool(email_dict.get('has_attachments'))
            emails.append(email_dict)

        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "emails": emails,
            "total": len(emails)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal conversation: {str(e)}")


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
        # Filter out internal Bensley emails - only show external stakeholders
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
            WHERE (proposal_id = ? OR project_code = ?)
            AND (email IS NULL OR (
                email NOT LIKE '%@bensley.com%'
                AND email NOT LIKE '%@bensley.co.id%'
                AND email NOT LIKE '%@bensley.co.th%'
            ))
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
                AND e.sender_email NOT LIKE '%@bensley.co.id%'
                AND e.sender_email NOT LIKE '%@bensley.co.th%'
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


@router.get("/proposals/{project_code}/documents")
async def get_proposal_documents(project_code: str):
    """Get documents/attachments for a proposal"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get proposal_id from project_code
        cursor.execute(
            "SELECT proposal_id, project_name FROM proposals WHERE project_code = ?",
            (project_code,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        proposal_id = row["proposal_id"]
        project_name = row["project_name"]

        # Get attachments linked to this proposal
        cursor.execute("""
            SELECT
                ea.attachment_id as document_id,
                ea.filename as file_name,
                ea.filesize as file_size,
                ea.mime_type as document_type,
                ea.document_type as category,
                ea.is_signed,
                ea.ai_summary,
                ea.created_at as modified_date,
                e.subject as email_subject,
                e.date as email_date
            FROM email_attachments ea
            JOIN emails e ON ea.email_id = e.email_id
            WHERE ea.proposal_id = ?
            AND ea.is_junk = 0
            ORDER BY ea.created_at DESC
        """, (proposal_id,))

        documents = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "project_name": project_name,
            "documents": documents,
            "count": len(documents)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal documents: {str(e)}")


@router.get("/proposals/{project_code}/briefing")
async def get_proposal_briefing(project_code: str):
    """Get briefing data for a proposal including client info, financials, and milestones"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get proposal details
        cursor.execute("""
            SELECT
                proposal_id,
                project_code,
                project_name,
                client_company,
                contact_person,
                contact_email,
                contact_phone,
                project_value,
                currency,
                status,
                contract_signed_date,
                is_active_project,
                health_score,
                win_probability,
                created_at
            FROM proposals
            WHERE project_code = ?
        """, (project_code,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        proposal = dict(row)

        # Get milestones if any
        cursor.execute("""
            SELECT
                milestone_id,
                phase,
                milestone_name,
                milestone_type,
                planned_date,
                actual_date,
                status,
                notes
            FROM project_milestones
            WHERE project_code = ?
            ORDER BY planned_date ASC
        """, (project_code,))

        milestones = [dict(row) for row in cursor.fetchall()]

        # Get payment info if project is signed (check invoices table via projects)
        paid_amount = 0
        outstanding_amount = 0
        if proposal.get("is_active_project"):
            cursor.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN i.status = 'paid' THEN i.invoice_amount ELSE 0 END), 0) as paid,
                    COALESCE(SUM(CASE WHEN i.status IN ('sent', 'overdue') THEN i.invoice_amount ELSE 0 END), 0) as outstanding
                FROM invoices i
                JOIN projects p ON i.project_id = p.project_id
                WHERE p.project_code = ?
            """, (project_code,))
            invoice_row = cursor.fetchone()
            if invoice_row:
                paid_amount = invoice_row["paid"] or 0
                outstanding_amount = invoice_row["outstanding"] or 0

        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "project_name": proposal.get("project_name"),
            "client": {
                "name": proposal.get("contact_person"),
                "email": proposal.get("contact_email"),
                "phone": proposal.get("contact_phone"),
                "company": proposal.get("client_company")
            },
            "financials": {
                "total_contract_value": proposal.get("project_value") or 0,
                "currency": proposal.get("currency") or "USD",
                "initial_payment_received": paid_amount,
                "outstanding_balance": outstanding_amount,
                "overdue_amount": 0  # Could calculate from overdue invoices
            },
            "milestones": milestones,
            "health_score": proposal.get("health_score"),
            "win_probability": proposal.get("win_probability"),
            "status": proposal.get("status"),
            "contract_signed_date": proposal.get("contract_signed_date")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposal briefing: {str(e)}")


@router.get("/proposals/{project_code}/story")
async def get_proposal_story(project_code: str):
    """
    Get the COMPLETE story/timeline of a proposal.

    Returns:
    - Full proposal metadata including remarks, correspondence_summary
    - ALL emails chronologically with AI summaries
    - Proposal versions detected from attachments
    - Events (meetings, calls) from proposal_events
    - Action items extracted from emails and waiting_for field
    - Upcoming scheduled meetings/calls
    """
    import json
    from datetime import datetime, timedelta

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get FULL proposal details from proposals table (source of truth)
        cursor.execute("""
            SELECT
                proposal_id, project_code, project_name,
                status, current_status,
                client_company, contact_person, contact_email,
                project_value, currency,
                remarks, correspondence_summary, internal_notes, scope_summary,
                waiting_for, waiting_since, ball_in_court,
                next_action, next_action_date,
                last_action, last_contact_date,
                first_contact_date, proposal_sent_date,
                num_proposals_sent,
                created_at
            FROM proposals WHERE project_code = ?
        """, (project_code,))
        proposal = cursor.fetchone()
        if not proposal:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        proposal_id = proposal["proposal_id"]
        p = dict(proposal)

        # ============ 1. GET ALL EMAILS WITH FULL CONTENT ============
        cursor.execute("""
            SELECT
                e.email_id,
                e.subject,
                e.sender_email,
                e.sender_name,
                e.date,
                e.snippet,
                e.email_direction,
                ec.category,
                ec.subcategory,
                ec.ai_summary,
                ec.key_points,
                ec.action_required,
                ec.urgency_level,
                ec.sentiment
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE epl.proposal_id = ?
            ORDER BY e.date ASC
        """, (proposal_id,))
        all_emails = [dict(row) for row in cursor.fetchall()]

        # ============ 2. GET PROPOSAL VERSIONS FROM ATTACHMENTS ============
        # Only get actual proposal documents for THIS project (not generic lists)
        cursor.execute("""
            SELECT
                ea.attachment_id, ea.email_id, ea.filename, ea.filepath,
                ea.mime_type, ea.document_type, e.date as email_date, e.subject
            FROM email_attachments ea
            JOIN emails e ON ea.email_id = e.email_id
            WHERE ea.proposal_id = ?
            AND ea.filename LIKE '%.docx'
            AND ea.filename LIKE '%' || ? || '%'
            ORDER BY e.date ASC
        """, (proposal_id, project_code.split()[1] if ' ' in project_code else project_code))
        proposal_docs = [dict(row) for row in cursor.fetchall()]

        # ============ 3. GET PROPOSAL_DOCUMENTS TABLE ============
        cursor.execute("""
            SELECT * FROM proposal_documents
            WHERE proposal_id = ? OR project_code = ?
            ORDER BY sent_date ASC
        """, (proposal_id, project_code))
        formal_docs = [dict(row) for row in cursor.fetchall()]

        # ============ 4. GET EVENTS (MEETINGS, CALLS) ============
        # Get from proposal_events table
        cursor.execute("""
            SELECT * FROM proposal_events
            WHERE proposal_id = ? OR project_code = ?
            ORDER BY event_date ASC
        """, (proposal_id, project_code))
        events = [dict(row) for row in cursor.fetchall()]

        # ALSO get from meetings table (with transcript data)
        cursor.execute("""
            SELECT
                m.meeting_id,
                m.title,
                m.description,
                m.meeting_date as event_date,
                m.start_time,
                m.location,
                m.status,
                m.transcript_id,
                t.summary as transcript_summary,
                t.key_points as transcript_key_points,
                t.action_items as transcript_action_items
            FROM meetings m
            LEFT JOIN meeting_transcripts t ON m.transcript_id = t.id
            WHERE m.proposal_id = ? OR m.project_code LIKE ?
            ORDER BY m.meeting_date ASC
        """, (proposal_id, f"%{project_code}%"))

        # Merge meetings into events, mark completed if status=completed
        # If meeting has transcript, prefer it over proposal_event
        seen_dates = {}  # Map date -> index in events
        for i, e in enumerate(events):
            seen_dates[e.get("event_date")] = i

        for row in cursor.fetchall():
            meeting = dict(row)
            meeting_date = meeting.get("event_date")
            meeting["completed"] = 1 if meeting.get("status") == "completed" else 0

            if meeting_date in seen_dates:
                # If this meeting has transcript but existing one doesn't, replace it
                if meeting.get("transcript_id"):
                    events[seen_dates[meeting_date]] = meeting
            else:
                events.append(meeting)
                seen_dates[meeting_date] = len(events) - 1

        # ============ 5. GET STATUS HISTORY ============
        cursor.execute("""
            SELECT * FROM proposal_status_history
            WHERE proposal_id = ? OR project_code = ?
            ORDER BY status_date ASC
        """, (proposal_id, project_code))
        status_history = [dict(row) for row in cursor.fetchall()]

        # ============ BUILD MILESTONE TIMELINE ============
        # Only include emails that represent actual progression/milestones
        timeline = []

        # Add first contact (first meaningful external email)
        # Skip emails with garbage summaries like "not pertaining to business"
        first_external = None
        for email in all_emails:
            direction = email.get("email_direction") or ""
            if "external" in direction or direction == "OUTBOUND":
                # Check if summary is garbage
                summary = email.get("ai_summary") or ""
                subject = email.get("subject") or ""
                if "not pertain" in summary.lower() or "not related" in summary.lower():
                    continue  # Skip garbage
                if not subject or subject.lower().startswith("invitation"):
                    continue  # Skip invitations
                first_external = email
                break

        if first_external:
            timeline.append({
                "type": "first_contact",
                "date": first_external["date"],
                "title": "First Contact",
                "summary": first_external.get("subject"),  # Use subject, not potentially garbage AI summary
                "email_id": first_external["email_id"],
                "direction": first_external.get("email_direction")
            })

        # Only add emails that represent actual milestones
        # Track seen dates to avoid duplicates on same day
        seen_milestones = set()

        for email in all_emails:
            subject_lower = (email.get("subject") or "").lower()
            subject_orig = email.get("subject") or ""
            summary_lower = (email.get("ai_summary") or "").lower()
            subcategory = email.get("subcategory") or ""
            direction = email.get("email_direction") or ""
            is_outbound = "external" in direction or direction == "OUTBOUND"
            email_date = (email.get("date") or "")[:10]

            # Skip if it's the first contact we already added
            if email == first_external:
                continue

            # Skip generic internal emails
            if "proposal list" in subject_lower or "proposal tracking" in subject_lower:
                continue

            # Determine if this email represents a milestone
            milestone_type = None
            milestone_title = None

            # 1. Proposal sent to client (outbound with proposal in subject, must mention project)
            if is_outbound and "proposal" in subject_lower and project_code.lower().replace(" ", "") in subject_lower.replace(" ", ""):
                milestone_type = "proposal_sent"
                milestone_title = "Proposal Sent"

            # 2. Meeting scheduled/confirmed
            elif ("meeting" in subject_lower or "zoom" in subject_lower) and \
                 any(word in summary_lower for word in ["scheduled", "confirmed", "10 am", "10am", "9 am", "9am"]):
                milestone_type = "meeting_scheduled"
                milestone_title = "Meeting Scheduled"

            # 3. Contract/Agreement discussion
            elif any(word in subject_lower for word in ["contract", "agreement", "mou"]) and \
                 not subject_lower.startswith("re:"):
                milestone_type = "contract_discussion"
                milestone_title = "Contract Discussion"

            # 4. Client response with decision/feedback (from client, substantive)
            elif not is_outbound and any(word in summary_lower for word in
                ["confirmed", "approved", "agreed", "accept", "proceed", "go ahead",
                 "questions about", "comments on the proposal", "feedback on"]):
                milestone_type = "client_response"
                milestone_title = "Client Response"

            # Only add if it's a milestone and not a duplicate
            if milestone_type:
                # Create a key to avoid duplicates (same type on same day)
                milestone_key = f"{milestone_type}:{email_date}"
                if milestone_key not in seen_milestones:
                    seen_milestones.add(milestone_key)
                    timeline.append({
                        "type": milestone_type,
                        "date": email["date"],
                        "title": milestone_title,
                        "summary": email.get("ai_summary"),
                        "email_id": email["email_id"],
                        "direction": email.get("email_direction")
                    })

        # Add proposal versions from attachments (only external-facing, not internal drafts)
        for doc in proposal_docs:
            # Skip internal-to-internal emails (those are drafts, not sent proposals)
            cursor.execute("SELECT email_direction FROM emails WHERE email_id = ?", (doc["email_id"],))
            email_row = cursor.fetchone()
            if email_row and email_row["email_direction"] == "internal_to_internal":
                continue  # Skip internal drafts

            timeline.append({
                "type": "proposal_version",
                "date": doc["email_date"],
                "title": f"Proposal Document: {doc['filename'][:60]}...",
                "summary": f"Sent via: {doc.get('subject')}",
                "attachment_id": doc["attachment_id"],
                "filepath": doc.get("filepath")
            })

        # Add formal documents
        for doc in formal_docs:
            timeline.append({
                "type": "proposal_sent",
                "date": doc.get("sent_date"),
                "title": f"V{doc.get('version', 1)} Proposal - ${doc.get('fee_amount', 0):,.0f}" if doc.get("fee_amount") else f"V{doc.get('version', 1)} Proposal",
                "summary": doc.get("notes"),
                "doc_id": doc["doc_id"],
                "version": doc.get("version"),
                "fee_amount": doc.get("fee_amount"),
                "sent_to": doc.get("sent_to")
            })

        # Add meetings/events
        for event in events:
            is_future = False
            is_completed = event.get("completed") == 1 or event.get("status") == "completed"

            if event.get("event_date"):
                try:
                    event_date = datetime.strptime(event["event_date"], "%Y-%m-%d")
                    # Only mark as future if date is in future AND not completed
                    is_future = event_date.date() >= datetime.now().date() and not is_completed
                except:
                    pass

            timeline.append({
                "type": "meeting" if not is_future else "upcoming_meeting",
                "date": event.get("event_date"),
                "title": event.get("title"),
                "summary": event.get("transcript_summary") or event.get("description"),  # Prefer transcript summary
                "location": event.get("location"),
                "attendees": event.get("attendees"),
                "is_confirmed": event.get("is_confirmed"),
                "completed": event.get("completed"),
                "outcome": event.get("outcome"),
                "is_future": is_future,
                "has_transcript": bool(event.get("transcript_id")),
                "transcript_summary": event.get("transcript_summary"),
                "transcript_key_points": event.get("transcript_key_points"),
                "transcript_action_items": event.get("transcript_action_items")
            })

        # Add status changes - only meaningful ones (skip auto-logged and trivial)
        for sh in status_history:
            notes = sh.get("notes") or ""
            old_status = sh.get("old_status") or ""
            # Skip: auto-logged, no notes, or changes from None/empty
            if "Auto-logged" in notes or not notes or not old_status or old_status == "None":
                continue
            timeline.append({
                "type": "status_change",
                "date": sh.get("status_date"),
                "title": f"Status: {old_status} → {sh.get('new_status')}",
                "summary": notes,
                "changed_by": sh.get("changed_by")
            })

        # Sort timeline by date
        def parse_date(item):
            d = item.get("date")
            if not d:
                return datetime.min
            try:
                if "T" in str(d) or " " in str(d):
                    return datetime.fromisoformat(str(d).replace("+07:00", "").replace("+08:00", "").replace("+00:00", "")[:19])
                return datetime.strptime(str(d)[:10], "%Y-%m-%d")
            except:
                return datetime.min

        timeline.sort(key=parse_date)

        # ============ EXTRACT ACTION ITEMS ============
        action_items = []
        seen_email_ids = set()  # Track email IDs to prevent duplicates

        # Helper to clean sender names (remove angle brackets, partial emails)
        def clean_sender_name(email_data):
            sender = email_data.get("sender_name") or ""
            # Remove angle brackets and anything after them
            if "<" in sender:
                sender = sender.split("<")[0].strip()
            # If still empty or just whitespace, try sender_email
            if not sender.strip():
                sender_email = email_data.get("sender_email", "") or ""
                # Handle format like "Name <email@domain.com>" or "<email@domain.com>"
                if "<" in sender_email:
                    # Try to get name part before <
                    name_part = sender_email.split("<")[0].strip()
                    if name_part:
                        sender = name_part
                    else:
                        # No name, extract email address and use username part
                        email_part = sender_email.split("<")[1].rstrip(">") if "<" in sender_email else sender_email
                        sender = email_part.split("@")[0] if "@" in email_part else email_part
                else:
                    # Plain email address
                    sender_email = sender_email.strip().lstrip("<").rstrip(">")
                    sender = sender_email.split("@")[0] if "@" in sender_email else sender_email
            # Clean any remaining angle brackets
            sender = sender.replace("<", "").replace(">", "")
            return sender.strip() or "Unknown"

        # From waiting_for field
        if p.get("waiting_for"):
            action_items.append({
                "task": p["waiting_for"],
                "date": p.get("waiting_since"),
                "source": "system",
                "priority": "high",
                "ball_in_court": p.get("ball_in_court")
            })

        # From next_action field
        if p.get("next_action"):
            action_items.append({
                "task": p["next_action"],
                "date": p.get("next_action_date"),
                "source": "system",
                "priority": "high"
            })

        # NOTE: Meetings are NOT action items - they appear in the Upcoming section
        # Action items are things we NEED TO DO (respond to request, send document, etc.)
        # A scheduled meeting is already handled, not an action

        # Extract client requests from recent emails (last 14 days)
        # These are real action items - things the client asked for
        # GROUP BY REQUEST TYPE to avoid duplicates like "Review contract terms from X" x4
        request_patterns = [
            ("contract", "Review contract terms"),
            ("clause", "Contract clause questions"),
            ("confirm", "Confirmation requested"),
            ("please send", "Document request"),
            ("can you send", "Document request"),
            ("we need", "Client request"),
            ("could you", "Client request"),
            ("approve", "Approval needed"),
            ("feedback", "Feedback/response needed"),
        ]

        # Collect emails by request type
        request_type_emails: dict = {}  # task_type -> list of emails

        for email in reversed(all_emails[-20:]):  # Check last 20 emails, most recent first
            email_id = email.get("email_id")
            if email_id in seen_email_ids:
                continue  # Skip already processed emails

            # Only check inbound emails from external parties
            direction = email.get("email_direction") or ""
            if "internal_to_external" in direction or direction == "OUTBOUND":
                continue  # Skip our outbound emails

            email_date = email.get("date", "")[:10]
            try:
                email_dt = datetime.strptime(email_date, "%Y-%m-%d")
                days_old = (datetime.now() - email_dt).days
                if days_old > 14:
                    continue  # Skip older emails
            except:
                continue

            # Look for client requests in the snippet/body
            snippet = (email.get("snippet") or "").lower()
            subject = (email.get("subject") or "").lower()

            for pattern, task_type in request_patterns:
                if pattern in snippet or pattern in subject:
                    # Found a request - group by type
                    if task_type not in request_type_emails:
                        request_type_emails[task_type] = []
                    request_type_emails[task_type].append({
                        "email_id": email_id,
                        "date": email_date,
                        "days_old": days_old,
                        "sender": clean_sender_name(email)
                    })
                    seen_email_ids.add(email_id)
                    break  # Only one pattern match per email

        # Now create ONE action item per request type (not per email!)
        for task_type, emails in request_type_emails.items():
            if not emails:
                continue

            # Check if we already responded (outbound email after latest request)
            latest_request_date = max(e["date"] for e in emails)
            we_responded = False
            for email in all_emails:
                direction = email.get("email_direction") or ""
                if "internal_to_external" in direction or direction == "OUTBOUND":
                    email_date = (email.get("date") or "")[:10]
                    if email_date > latest_request_date:
                        we_responded = True
                        break

            if we_responded:
                continue  # Skip - we already followed up

            # Create ONE action item for this type
            min_days_old = min(e["days_old"] for e in emails)
            email_count = len(emails)

            # Build task description
            if email_count == 1:
                task_text = f"{task_type} from {emails[0]['sender']}"
            else:
                task_text = f"{task_type} ({email_count} emails)"

            action_items.append({
                "task": task_text,
                "date": latest_request_date,
                "source": "email",
                "email_id": emails[0]["email_id"],  # Link to most recent
                "priority": "high" if min_days_old <= 3 else "medium"
            })

        # From emails with action_required flag (only recent - last 14 days)
        for email in all_emails[-30:]:  # Only check last 30 emails
            email_id = email.get("email_id")
            if email_id in seen_email_ids:
                continue  # Skip already processed emails

            if not email.get("action_required"):
                continue

            # Check if recent
            email_date = email.get("date", "")[:10]
            try:
                email_dt = datetime.strptime(email_date, "%Y-%m-%d")
                if (datetime.now() - email_dt).days > 14:
                    continue  # Skip old emails
            except:
                continue

            key_points = email.get("key_points")
            if key_points:
                try:
                    points = json.loads(key_points) if isinstance(key_points, str) else key_points
                    if isinstance(points, list):
                        seen_email_ids.add(email_id)
                        for point in points[:2]:
                            action_items.append({
                                "task": point,
                                "date": email_date,
                                "source": "email",
                                "email_id": email_id,
                                "priority": email.get("urgency_level") or "medium"
                            })
                except:
                    pass

        # De-duplicate action items by task text (case-insensitive)
        seen_tasks = set()
        unique_action_items = []
        for item in action_items:
            task_key = item["task"].lower().strip()
            if task_key not in seen_tasks:
                seen_tasks.add(task_key)
                unique_action_items.append(item)
        action_items = unique_action_items

        # ============ GROUP EMAILS INTO THREADS ============
        threads = {}
        for email in all_emails:
            subject = email.get("subject") or "No Subject"
            base_subject = subject
            for prefix in ["Re: ", "RE: ", "Fwd: ", "FW: ", "Fw: ", "TR: ", "RE : "]:
                while base_subject.startswith(prefix):
                    base_subject = base_subject[len(prefix):]
            base_subject = base_subject.strip()

            if base_subject not in threads:
                threads[base_subject] = {
                    "emails": [],
                    "first_date": email["date"],
                    "last_date": email["date"],
                    "participants": set(),
                    "has_action": False
                }
            threads[base_subject]["emails"].append({
                "id": email["email_id"],
                "date": email["date"],
                "sender": email.get("sender_name") or email.get("sender_email"),
                "summary": email.get("ai_summary"),
                "direction": email.get("email_direction")
            })
            threads[base_subject]["last_date"] = email["date"]
            if email.get("sender_name"):
                threads[base_subject]["participants"].add(email["sender_name"])
            if email.get("action_required"):
                threads[base_subject]["has_action"] = True

        thread_list = []
        for subject, data in threads.items():
            thread_list.append({
                "subject": subject,
                "email_count": len(data["emails"]),
                "emails": data["emails"],
                "first_date": data["first_date"],
                "last_date": data["last_date"],
                "participants": list(data["participants"]),
                "has_action": data["has_action"]
            })
        thread_list.sort(key=lambda x: x["last_date"] or "", reverse=True)

        # ============ CALCULATE CURRENT STATUS ============
        last_email = all_emails[-1] if all_emails else None
        last_email_date = last_email["date"] if last_email else None
        days_since_contact = None

        if last_email_date:
            try:
                last_dt = datetime.fromisoformat(str(last_email_date).replace("+07:00", "").replace("+08:00", "")[:19])
                days_since_contact = (datetime.now() - last_dt).days
            except:
                pass

        current_status = {
            "status": p.get("current_status") or p.get("status"),
            "last_contact_date": last_email_date[:10] if last_email_date else p.get("last_contact_date"),
            "days_since_contact": days_since_contact,
            "email_count": len(all_emails),
            "ball_in_court": p.get("ball_in_court"),
            "waiting_for": p.get("waiting_for"),
            "waiting_since": p.get("waiting_since"),
            "last_action": p.get("last_action"),
            "suggested_action": p.get("next_action")
        }

        # ============ PARSE NEXT ACTION FROM CORRESPONDENCE_SUMMARY ============
        # If no explicit next_action, try to extract one from correspondence_summary
        if not current_status["suggested_action"]:
            import re
            corr_summary = p.get("correspondence_summary") or ""
            extracted_action = None

            # Patterns to detect next actions
            patterns = [
                # Meeting patterns
                (r'(?:meeting|call|zoom|video call)\s+(?:on|scheduled for|set for)\s+(\w+\s*\d+(?:st|nd|rd|th)?(?:\s*,?\s*\d{4})?)', 'Meeting scheduled'),
                (r'(?:meeting|call)\s+(?:to be|needs to be)\s+(?:scheduled|arranged|set up)', 'Schedule meeting'),
                # Waiting patterns
                (r'waiting\s+(?:for|on)\s+(?:their|client|owner|developer)\s+(?:response|reply|feedback|approval|decision)', 'Awaiting client response'),
                (r'awaiting\s+(?:client|their)\s+(?:response|feedback|approval)', 'Awaiting client response'),
                # Follow-up patterns
                (r'need(?:s)?\s+to\s+(?:follow up|followup|follow-up)', 'Follow up required'),
                (r'(?:will|should)\s+(?:send|submit|provide)\s+(?:revised|updated|new)\s+(?:proposal|quote|fee)', 'Send revised proposal'),
                # Review patterns
                (r'(?:contract|proposal|fee)\s+(?:under|pending)\s+(?:review|consideration)', 'Under review'),
                (r'(?:reviewing|review)\s+(?:contract|proposal|terms)', 'Under review'),
            ]

            for pattern, action_label in patterns:
                match = re.search(pattern, corr_summary, re.IGNORECASE)
                if match:
                    # If the pattern captured a date/detail, include it
                    if match.groups():
                        extracted_action = f"{action_label}: {match.group(1)}"
                    else:
                        extracted_action = action_label
                    break

            if extracted_action:
                current_status["suggested_action"] = extracted_action

        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "project_name": p.get("project_name"),
            "client": {
                "name": p.get("contact_person"),
                "company": p.get("client_company"),
                "email": p.get("contact_email")
            },
            "value": p.get("project_value"),
            "currency": p.get("currency") or "USD",

            # Rich context from proposals table
            "remarks": p.get("remarks"),
            "correspondence_summary": p.get("correspondence_summary"),
            "internal_notes": p.get("internal_notes"),  # Contains proposal history, fee breakdown, scope
            "scope_summary": p.get("scope_summary"),
            "num_proposals_sent": p.get("num_proposals_sent"),
            "first_contact_date": p.get("first_contact_date"),
            "proposal_sent_date": p.get("proposal_sent_date"),

            # The comprehensive timeline
            "timeline": timeline,

            # Proposal versions
            "proposal_versions": formal_docs,
            "proposal_attachments": proposal_docs,

            # Meetings and events
            "events": events,

            # Grouped email threads
            "threads": thread_list,

            # Action items from all sources
            "action_items": action_items,

            # Current status with waiting info
            "current_status": current_status
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get proposal story: {str(e)}")


@router.get("/proposals/summary")
async def get_proposals_summary():
    """Get proposals summary for dashboard - pipeline value, activity, meetings, etc."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Active pipeline stats (excludes Lost, Declined, Dormant, Contract Signed, Cancelled)
        cursor.execute("""
            SELECT
                COUNT(*) as active_count,
                COALESCE(SUM(project_value), 0) as active_value
            FROM proposals
            WHERE status NOT IN ('Lost', 'Declined', 'Dormant', 'Contract Signed', 'Cancelled')
            AND is_active_project = 0
        """)
        active = cursor.fetchone()

        # Proposals sent (with value)
        cursor.execute("""
            SELECT
                COUNT(*) as sent_count,
                COALESCE(SUM(project_value), 0) as sent_value
            FROM proposals
            WHERE status = 'Proposal Sent'
            AND is_active_project = 0
        """)
        sent = cursor.fetchone()

        # Contracts signed this year
        cursor.execute("""
            SELECT
                COUNT(*) as signed_count,
                COALESCE(SUM(project_value), 0) as signed_value
            FROM proposals
            WHERE status = 'Contract Signed'
            AND contract_signed_date >= date('now', 'start of year')
        """)
        signed = cursor.fetchone()

        # Activity last 7 days
        cursor.execute("""
            SELECT COUNT(DISTINCT proposal_id) as proposals_with_activity
            FROM email_proposal_links epl
            JOIN emails e ON epl.email_id = e.email_id
            WHERE date(e.date) >= date('now', '-7 days')
        """)
        recent_activity = cursor.fetchone()

        # Status changes this week
        cursor.execute("""
            SELECT COUNT(*) as status_changes
            FROM proposal_status_history
            WHERE date(status_date) >= date('now', '-7 days')
        """)
        status_changes = cursor.fetchone()

        # Upcoming meetings (from meeting_transcripts with future dates)
        cursor.execute("""
            SELECT COUNT(*) as upcoming_meetings
            FROM meeting_transcripts
            WHERE date(meeting_date) >= date('now')
        """)
        upcoming = cursor.fetchone()

        # Proposals needing follow-up (>7 days no contact)
        cursor.execute("""
            SELECT COUNT(*) as needs_followup
            FROM proposals
            WHERE status NOT IN ('Lost', 'Declined', 'Dormant', 'Contract Signed', 'Cancelled')
            AND is_active_project = 0
            AND (
                last_contact_date IS NULL
                OR julianday('now') - julianday(last_contact_date) > 7
            )
        """)
        followup = cursor.fetchone()

        # By stage breakdown
        cursor.execute("""
            SELECT
                status,
                COUNT(*) as count,
                COALESCE(SUM(project_value), 0) as value
            FROM proposals
            WHERE status NOT IN ('Lost', 'Declined', 'Dormant', 'Contract Signed', 'Cancelled')
            AND is_active_project = 0
            GROUP BY status
            ORDER BY
                CASE status
                    WHEN 'First Contact' THEN 1
                    WHEN 'Meeting Held' THEN 2
                    WHEN 'Proposal Prep' THEN 3
                    WHEN 'Proposal Sent' THEN 4
                    WHEN 'Negotiation' THEN 5
                    WHEN 'On Hold' THEN 6
                    ELSE 7
                END
        """)
        by_stage = [{"stage": row["status"], "count": row["count"], "value": row["value"]}
                    for row in cursor.fetchall()]

        conn.close()

        return {
            "success": True,
            "pipeline": {
                "active_count": active["active_count"],
                "active_value": active["active_value"],
                "sent_count": sent["sent_count"],
                "sent_value": sent["sent_value"]
            },
            "contracts_signed_ytd": {
                "count": signed["signed_count"],
                "value": signed["signed_value"]
            },
            "activity": {
                "proposals_with_emails_7d": recent_activity["proposals_with_activity"],
                "status_changes_7d": status_changes["status_changes"],
                "upcoming_meetings": upcoming["upcoming_meetings"]
            },
            "attention": {
                "needs_followup": followup["needs_followup"]
            },
            "by_stage": by_stage
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get proposals summary: {str(e)}")


@router.post("/proposals/{project_code}/chat")
async def chat_about_proposal(project_code: str, request: dict):
    """
    Chat/ask questions about a specific proposal.
    Searches emails and proposal data to answer questions.
    Supports conversation history for follow-up questions.

    NEW: Detects correction requests like "fix John's email to john@new.com"
    and auto-creates suggestions for review.

    Request body:
    {
        "question": "What contract terms did Romain ask about?",
        "use_ai": true,  # Optional, defaults to true
        "history": [  # Optional conversation history
            {"role": "user", "content": "previous question"},
            {"role": "assistant", "content": "previous answer"}
        ]
    }

    Returns relevant email excerpts and AI-generated answer if available.
    If a correction is detected, includes correction_created field.
    """
    import os
    import re
    import json
    from openai import OpenAI

    question = request.get("question", "")
    use_ai = request.get("use_ai", True)
    history = request.get("history", [])  # Conversation history

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    # Check if this is a correction request
    correction_keywords = ['fix', 'update', 'change', 'correct', 'wrong', 'should be', 'actually is', 'real email', 'correct email']
    is_correction_request = any(kw in question.lower() for kw in correction_keywords)

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get proposal info
        cursor.execute("""
            SELECT proposal_id, project_name, client_company, contact_person,
                   internal_notes, correspondence_summary, project_value
            FROM proposals WHERE project_code = ?
        """, (project_code,))
        proposal = cursor.fetchone()
        if not proposal:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")

        proposal_id = proposal["proposal_id"]

        # Get ALL emails with full body content for this proposal
        cursor.execute("""
            SELECT
                e.email_id, e.subject, e.sender_email, e.sender_name,
                e.date, e.snippet, e.body_preview, e.body_full,
                ec.ai_summary, ec.key_points
            FROM emails e
            JOIN email_proposal_links epl ON e.email_id = epl.email_id
            LEFT JOIN email_content ec ON e.email_id = ec.email_id
            WHERE epl.proposal_id = ?
            ORDER BY e.date DESC
            LIMIT 100
        """, (proposal_id,))
        emails = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Extract keywords from question for search
        stop_words = {'what', 'who', 'when', 'where', 'how', 'did', 'does', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'about', 'for', 'in', 'on', 'to', 'of', 'and', 'or'}
        keywords = [w.lower() for w in re.findall(r'\w+', question) if len(w) > 2 and w.lower() not in stop_words]

        # Score emails by relevance to question
        relevant_emails = []
        for email in emails:
            body_text = email.get('body_full') or email.get('body_preview') or ""
            searchable = f"{email.get('subject', '')} {email.get('snippet', '')} {body_text} {email.get('ai_summary', '')}".lower()
            score = sum(1 for kw in keywords if kw in searchable)

            # Skip emails that are mostly HTML/CSS noise
            if body_text and (body_text.count('{') > 10 or '@font-face' in body_text):
                score = max(0, score - 2)  # Penalize noisy emails

            # Boost external emails (more likely to have real content)
            sender = email.get('sender_email', '').lower()
            if '@bensley.com' not in sender and '@hxcore.ol' not in sender:
                score += 1  # Boost external senders

            if score > 0:
                # Extract sender name from email address if name is empty
                sender_display = email["sender_name"]
                if not sender_display:
                    sender_email = email.get("sender_email", "")
                    # Extract from formats like: "<romain@example.com>" or "Name <email>"
                    if "@" in sender_email:
                        sender_display = sender_email.split("@")[0].replace("<", "").replace(">", "")
                        sender_display = sender_display.replace(".", " ").title()

                relevant_emails.append({
                    "email_id": email["email_id"],
                    "date": email["date"],
                    "sender": sender_display or email["sender_email"],
                    "subject": email["subject"],
                    "excerpt": email["snippet"][:500] if email["snippet"] else "",
                    "body_full": body_text[:3000] if body_text else "",  # More content for AI
                    "score": score
                })

        # Sort by relevance score
        relevant_emails.sort(key=lambda x: x["score"], reverse=True)
        top_emails = relevant_emails[:5]

        # Prepare context for AI - include MORE email content
        context_parts = [
            f"PROPOSAL: {project_code} - {proposal['project_name']}",
            f"Client: {proposal['client_company']}",
            f"Contact: {proposal['contact_person']}",
            f"Value: ${proposal['project_value']:,.0f}" if proposal['project_value'] else "",
            "",
            "=== INTERNAL NOTES ===",
            proposal['internal_notes'] or "None",
            "",
            "=== RELEVANT EMAILS (most relevant first) ==="
        ]

        # Include more emails with full content
        for i, email in enumerate(top_emails[:7], 1):
            context_parts.append(f"\n--- EMAIL {i}: {email['sender']} ({email['date'][:10]}) ---")
            context_parts.append(f"Subject: {email['subject']}")
            context_parts.append(email['body_full'] or email['excerpt'])

        context = "\n".join(context_parts)

        # Try AI answer if available
        answer = None
        if use_ai:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                try:
                    client = OpenAI(api_key=api_key)

                    # Build messages with conversation history
                    # Use different prompt for correction requests
                    if is_correction_request:
                        system_prompt = """You are an expert assistant helping manage proposal data for Bensley Design Studios.

The user is requesting a DATA CORRECTION. Your job is to:
1. Understand what they want to fix (contact email, phone, company name, etc.)
2. Acknowledge the correction
3. At the END of your response, include a structured correction block in this EXACT format:

[CORRECTION]
type: update_contact | new_contact | update_proposal | link_stakeholder
target: Name of person or field being updated
field: email | phone | company | name | role (what field to update)
current: Current wrong value (if mentioned)
new: New correct value
[/CORRECTION]

Example response:
"I'll create a suggestion to update John's email from john@old.com to john@newcorp.com.

[CORRECTION]
type: update_contact
target: John Smith
field: email
current: john@old.com
new: john@newcorp.com
[/CORRECTION]"

If you cannot parse a clear correction from the request, ask for clarification."""
                    else:
                        system_prompt = """You are an expert assistant helping analyze proposal correspondence for Bensley Design Studios.

Your job is to answer questions about proposals based on email correspondence and internal notes.

Guidelines:
- Be DETAILED and SPECIFIC - quote exact clauses, dates, amounts when available
- Include specific details like clause numbers (e.g., "Clause 2.3"), dollar amounts, dates
- If the email mentions specific terms or conditions, quote them
- Cite which email/date the information comes from
- If you can't find the answer in the provided context, say so clearly
- Keep answers well-organized with bullet points if listing multiple items"""

                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Here is the proposal context:\n\n{context}"}
                    ]

                    # Add conversation history (last 5 exchanges)
                    for msg in history[-10:]:
                        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

                    # Add current question
                    messages.append({"role": "user", "content": question})

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        max_tokens=1000,  # More tokens for detailed responses
                        temperature=0.2
                    )
                    answer = response.choices[0].message.content
                except Exception as ai_err:
                    answer = f"AI unavailable: {str(ai_err)}"

        # Parse and handle correction requests
        correction_created = None
        if answer and is_correction_request:
            # Parse [CORRECTION] block from response
            correction_match = re.search(r'\[CORRECTION\](.*?)\[/CORRECTION\]', answer, re.DOTALL)
            if correction_match:
                correction_text = correction_match.group(1).strip()
                correction_data = {}
                for line in correction_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        correction_data[key.strip().lower()] = value.strip()

                # Create suggestion if we have enough data
                if correction_data.get('type') and correction_data.get('new'):
                    try:
                        suggestion_conn = sqlite3.connect(DB_PATH)
                        suggestion_cursor = suggestion_conn.cursor()

                        # Build suggestion title and description
                        corr_type = correction_data.get('type', 'data_correction')
                        target = correction_data.get('target', 'Unknown')
                        field = correction_data.get('field', '')
                        new_val = correction_data.get('new', '')
                        current_val = correction_data.get('current', '')

                        title = f"Update {target}'s {field}" if field else f"Update {target}"
                        description = f"Change {field} from '{current_val}' to '{new_val}'" if current_val else f"Set {field} to '{new_val}'"

                        # Map correction type to suggestion type
                        suggestion_type_map = {
                            'update_contact': 'update_contact',
                            'new_contact': 'new_contact',
                            'update_proposal': 'data_correction',
                            'link_stakeholder': 'contact_link'
                        }
                        suggestion_type = suggestion_type_map.get(corr_type, 'data_correction')

                        # Insert suggestion
                        suggestion_cursor.execute("""
                            INSERT INTO ai_suggestions (
                                suggestion_type, priority, confidence_score,
                                source_type, title, description,
                                suggested_data, project_code, proposal_id,
                                status, created_at
                            ) VALUES (?, 'high', 0.95, 'chat', ?, ?, ?, ?, ?, 'pending', datetime('now'))
                        """, (
                            suggestion_type,
                            title,
                            description,
                            json.dumps(correction_data),
                            project_code,
                            proposal_id
                        ))
                        suggestion_id = suggestion_cursor.lastrowid
                        suggestion_conn.commit()
                        suggestion_conn.close()

                        correction_created = {
                            "suggestion_id": suggestion_id,
                            "type": suggestion_type,
                            "title": title,
                            "description": description
                        }

                        # Clean up the answer by removing the [CORRECTION] block
                        answer = re.sub(r'\[CORRECTION\].*?\[/CORRECTION\]', '', answer, flags=re.DOTALL).strip()

                    except Exception as sugg_err:
                        # Log but don't fail the response
                        import logging
                        logging.error(f"Failed to create suggestion: {sugg_err}")

        # Build response
        if not answer and top_emails:
            # Fallback: summarize relevant emails with better formatting
            import re as regex_clean
            email_summaries = []
            for e in top_emails[:3]:
                # Clean up HTML and extract meaningful content
                content = e.get('body_full') or e.get('excerpt') or ""
                # Remove HTML tags and CSS
                content = regex_clean.sub(r'<style[^>]*>.*?</style>', '', content, flags=regex_clean.DOTALL | regex_clean.IGNORECASE)
                content = regex_clean.sub(r'<[^>]+>', '', content)
                content = regex_clean.sub(r'/\*.*?\*/', '', content, flags=regex_clean.DOTALL)
                content = regex_clean.sub(r'\{[^}]+\}', '', content)  # Remove CSS blocks
                content = regex_clean.sub(r'\s+', ' ', content)  # Normalize whitespace
                content = content.strip()[:400]
                if content:
                    sender_name = e['sender'].split('<')[0].strip().strip('"')
                    email_summaries.append(f"**{e['date'][:10]}** - {sender_name}:\n{content}...")

            # Filter out empty summaries
            email_summaries = [s for s in email_summaries if len(s) > 50]

            if email_summaries:
                answer = f"Found {len(relevant_emails)} relevant emails. Top matches:\n\n" + "\n\n".join(email_summaries)
            else:
                answer = "Found emails but couldn't extract readable content. Check the email list below."
        elif not answer:
            answer = "No relevant emails found for that question. Try different keywords."

        response_data = {
            "success": True,
            "question": question,
            "answer": answer,
            "relevant_emails": top_emails,
            "context_used": bool(top_emails)
        }

        # Include correction info if one was created
        if correction_created:
            response_data["correction_created"] = correction_created

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
