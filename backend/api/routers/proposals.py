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

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime
import sqlite3
import logging

from api.services import proposal_service, proposal_tracker_service
from api.dependencies import DB_PATH, get_current_user
from services.proposal_detail_story_service import ProposalDetailStoryService

logger = logging.getLogger(__name__)

# Initialize story service
story_service = ProposalDetailStoryService(DB_PATH)
from api.models import CreateProposalRequest
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
    List all proposals with optional filtering and pagination.
    Returns standardized response format.
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
        # Standardize response format (Issue #126)
        return list_response(
            result.get('items', []),
            total=result.get('total', 0),
            page=result.get('page', page),
            per_page=result.get('per_page', per_page)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid request")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/proposals/stats")
async def get_proposal_stats():
    """Get proposal statistics. Returns standardized response format."""
    try:
        stats = proposal_service.get_dashboard_stats()
        # Standardize response format (Issue #126)
        return item_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/proposals/weekly-changes")
async def get_weekly_changes(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back")
):
    """Get proposal pipeline changes for Bill's weekly reports"""
    try:
        result = proposal_service.get_weekly_changes(days=days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/proposals", status_code=201)
async def create_proposal(
    request: CreateProposalRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new proposal. Returns standardized action response. Requires authentication."""
    try:
        with proposal_service.get_connection() as conn:
            cursor = conn.cursor()

            # Issue #109: Check proposals table, not projects
            cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (request.project_code,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Project code '{request.project_code}' already exists")

            # Issue #109: Insert into proposals table with correct column names
            cursor.execute("""
                INSERT INTO proposals (
                    project_code, project_name, project_value,
                    proposal_sent_date, next_action_date, win_probability,
                    status, is_active_project, client_company, internal_notes,
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
                SELECT proposal_id, project_code, project_name, status,
                       project_value, win_probability, is_active_project,
                       proposal_sent_date, next_action_date,
                       client_company, internal_notes, created_at
                FROM proposals WHERE proposal_id = ?
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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/proposal-tracker/disciplines")
async def get_tracker_disciplines():
    """Get distinct disciplines for filter dropdown"""
    try:
        disciplines = proposal_tracker_service.get_discipline_stats()
        return {"success": True, "disciplines": disciplines}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/proposal-tracker/countries")
async def get_tracker_countries():
    """Get distinct countries for filter dropdown"""
    try:
        countries = proposal_tracker_service.get_countries_list()
        return {"success": True, "countries": countries}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.put("/proposal-tracker/{project_code}")
async def update_tracker_proposal(
    project_code: str,
    updates: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update proposal in tracker. Returns standardized action response. Requires authentication."""
    try:
        result = proposal_tracker_service.update_proposal(project_code, updates)
        if not result:
            raise HTTPException(status_code=404, detail=f"Proposal {project_code} not found")
        return action_response(True, result, f"Proposal {project_code} updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/proposal-tracker/{project_code}/history")
async def get_tracker_history(project_code: str):
    """Get proposal status history. Returns standardized list response."""
    try:
        history = proposal_tracker_service.get_status_history(project_code)
        response = list_response(history, len(history))
        response["history"] = history  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/proposal-tracker/{project_code}/emails")
async def get_tracker_emails(project_code: str):
    """Get emails linked to proposal. Returns standardized list response."""
    try:
        emails = proposal_tracker_service.get_email_intelligence(project_code)
        response = list_response(emails, len(emails))
        response["emails"] = emails  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


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

    Refactored: Logic moved to ProposalDetailStoryService (#117)
    """
    try:
        return story_service.get_story(project_code)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Invalid request")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="An internal error occurred")


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
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/proposals/{project_code}/chat")
@limiter.limit("10/minute")
async def chat_about_proposal(
    request: Request,
    project_code: str,
    body: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Chat/ask questions about a specific proposal.
    Searches emails and proposal data to answer questions.
    Supports conversation history for follow-up questions.
    Requires authentication.

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

    question = body.get("question", "")
    use_ai = body.get("use_ai", True)
    history = body.get("history", [])  # Conversation history

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
        logger.exception("Error in proposal chat")
        raise HTTPException(status_code=500, detail="Chat failed due to an internal error")
