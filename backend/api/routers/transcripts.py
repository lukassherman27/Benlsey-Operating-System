"""
Transcripts Router - Meeting transcript management endpoints

Endpoints:
    GET /api/meeting-transcripts - List all transcripts
    GET /api/meeting-transcripts/{id} - Get single transcript
    GET /api/meeting-transcripts/stats - Transcript statistics
    GET /api/meeting-transcripts/by-project/{project_code} - Project transcripts
    POST /api/meeting-transcripts/{id}/claude-summary - Save Claude-generated summary with action items
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import sqlite3
import json

from api.dependencies import DB_PATH
from api.helpers import list_response, item_response


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ActionItem(BaseModel):
    """Action item extracted from meeting summary"""
    task: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None  # ISO date string
    priority: Optional[str] = "normal"  # low, normal, high, critical


class ClaudeSummaryRequest(BaseModel):
    """Request body for saving Claude-generated summary"""
    summary: str
    key_points: Optional[List[str]] = None
    action_items: Optional[List[ActionItem]] = None
    next_meeting_date: Optional[str] = None  # ISO date string
    proposal_code: Optional[str] = None  # Project code to link to

router = APIRouter(prefix="/api", tags=["transcripts"])


def _parse_json_field(value):
    """Parse JSON field if it's a string"""
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


# ============================================================================
# TRANSCRIPT LIST ENDPOINTS
# ============================================================================

@router.get("/meeting-transcripts")
async def get_transcripts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    project_code: Optional[str] = None
):
    """Get list of meeting transcripts"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query
        where_clauses = []
        params = []

        if project_code:
            where_clauses.append("detected_project_code = ?")
            params.append(project_code)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM meeting_transcripts WHERE {where_sql}", params)
        total = cursor.fetchone()[0]

        # Get paginated results - join with emails and proposals to get names
        cursor.execute(f"""
            SELECT mt.*,
                   e.body_full as final_summary,
                   p.project_name as proposal_name,
                   p.client_company
            FROM meeting_transcripts mt
            LEFT JOIN emails e ON mt.final_summary_email_id = e.email_id
            LEFT JOIN proposals p ON mt.detected_project_code = p.project_code
            WHERE {where_sql.replace('detected_project_code', 'mt.detected_project_code')}
            ORDER BY mt.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])

        rows = cursor.fetchall()
        transcripts = []

        for row in rows:
            transcript = dict(row)
            # Parse JSON fields
            transcript['key_points'] = _parse_json_field(transcript.get('key_points'))
            transcript['action_items'] = _parse_json_field(transcript.get('action_items'))
            transcript['participants'] = _parse_json_field(transcript.get('participants'))
            transcripts.append(transcript)

        conn.close()

        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "transcripts": transcripts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/meeting-transcripts/stats")
async def get_transcript_stats():
    """Get transcript statistics including orphan metrics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN detected_project_code IS NOT NULL THEN 1 ELSE 0 END) as with_detected_code,
                SUM(CASE WHEN project_id IS NOT NULL OR proposal_id IS NOT NULL THEN 1 ELSE 0 END) as linked,
                SUM(CASE WHEN project_id IS NULL AND proposal_id IS NULL THEN 1 ELSE 0 END) as orphaned,
                SUM(CASE WHEN summary IS NOT NULL THEN 1 ELSE 0 END) as with_summary,
                AVG(duration_seconds) as avg_duration,
                AVG(match_confidence) as avg_confidence,
                COUNT(DISTINCT detected_project_code) as unique_projects
            FROM meeting_transcripts
        """)

        row = cursor.fetchone()
        stats = dict(row) if row else {}

        # Calculate orphan percentage
        if stats.get('total', 0) > 0:
            stats['orphan_percentage'] = round(
                (stats.get('orphaned', 0) / stats['total']) * 100, 1
            )
        else:
            stats['orphan_percentage'] = 0

        conn.close()

        return item_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/meeting-transcripts/orphaned")
async def get_orphaned_transcripts():
    """
    Get transcripts that are not linked to any project or proposal.

    Returns transcripts where both project_id and proposal_id are NULL.
    These need manual review and linking.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                meeting_title,
                detected_project_code,
                match_confidence,
                recorded_date,
                created_at,
                SUBSTR(summary, 1, 200) as summary_preview
            FROM meeting_transcripts
            WHERE project_id IS NULL AND proposal_id IS NULL
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        orphaned = [dict(row) for row in rows]

        conn.close()

        return {
            "success": True,
            "total": len(orphaned),
            "orphaned_transcripts": orphaned,
            "message": f"Found {len(orphaned)} orphaned transcripts needing review"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/meeting-transcripts/{transcript_id}")
async def get_transcript(transcript_id: int):
    """Get a single transcript by ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Join with emails to get final_summary if available
        cursor.execute("""
            SELECT mt.*, e.body_full as final_summary
            FROM meeting_transcripts mt
            LEFT JOIN emails e ON mt.final_summary_email_id = e.email_id
            WHERE mt.id = ?
        """, (transcript_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Transcript not found")

        transcript = dict(row)
        # Parse JSON fields
        transcript['key_points'] = _parse_json_field(transcript.get('key_points'))
        transcript['action_items'] = _parse_json_field(transcript.get('action_items'))
        transcript['participants'] = _parse_json_field(transcript.get('participants'))

        return item_response(transcript)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/meeting-transcripts/by-project/{project_code}")
async def get_transcripts_by_project(project_code: str):
    """Get transcripts for a specific project"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM meeting_transcripts
            WHERE detected_project_code = ?
            ORDER BY created_at DESC
        """, (project_code,))

        rows = cursor.fetchall()
        transcripts = []

        for row in rows:
            transcript = dict(row)
            transcript['key_points'] = _parse_json_field(transcript.get('key_points'))
            transcript['action_items'] = _parse_json_field(transcript.get('action_items'))
            transcript['participants'] = _parse_json_field(transcript.get('participants'))
            transcripts.append(transcript)

        conn.close()

        response = list_response(transcripts, len(transcripts))
        response["transcripts"] = transcripts
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/projects/{project_code}/transcripts")
async def get_project_transcripts(project_code: str):
    """Get transcripts for a specific project or proposal"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Try to get project_id from projects table
        cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
        project_row = cursor.fetchone()
        project_id = project_row['project_id'] if project_row else None

        # Also try proposals table
        cursor.execute("SELECT proposal_id FROM proposals WHERE project_code = ?", (project_code,))
        proposal_row = cursor.fetchone()
        proposal_id = proposal_row['proposal_id'] if proposal_row else None

        if not project_id and not proposal_id:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Project/Proposal {project_code} not found")

        # Get transcripts by project_id, proposal_id, or detected_project_code
        cursor.execute("""
            SELECT * FROM meeting_transcripts
            WHERE project_id = ? OR proposal_id = ? OR detected_project_code = ?
            ORDER BY COALESCE(meeting_date, recorded_date, created_at) DESC
        """, (project_id, proposal_id, project_code))

        rows = cursor.fetchall()
        transcripts = []

        for row in rows:
            transcript = dict(row)
            transcript['key_points'] = _parse_json_field(transcript.get('key_points'))
            transcript['action_items'] = _parse_json_field(transcript.get('action_items'))
            transcript['participants'] = _parse_json_field(transcript.get('participants'))
            transcripts.append(transcript)

        conn.close()

        return {
            "success": True,
            "project_code": project_code,
            "transcripts": transcripts,
            "total": len(transcripts)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# TRANSCRIPT UPDATE ENDPOINTS
# ============================================================================

@router.put("/meeting-transcripts/{transcript_id}")
async def update_transcript(
    transcript_id: int,
    project_id: Optional[int] = None,
    proposal_id: Optional[int] = None,
    meeting_title: Optional[str] = None,
    meeting_date: Optional[str] = None,
    summary: Optional[str] = None,
    key_points: Optional[str] = None,
    action_items: Optional[str] = None
):
    """Update a transcript - link to project, add summary, etc."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if transcript exists
        cursor.execute("SELECT * FROM meeting_transcripts WHERE id = ?", (transcript_id,))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            raise HTTPException(status_code=404, detail="Transcript not found")

        # Build update query
        updates = []
        params = []

        if project_id is not None:
            updates.append("project_id = ?")
            params.append(project_id)
            # Also update detected fields for consistency
            cursor.execute("SELECT project_code FROM projects WHERE project_id = ?", (project_id,))
            project_row = cursor.fetchone()
            if project_row:
                updates.append("detected_project_code = ?")
                params.append(project_row['project_code'])
                updates.append("detected_project_id = ?")
                params.append(project_id)

        if proposal_id is not None:
            updates.append("proposal_id = ?")
            params.append(proposal_id)

        if meeting_title is not None:
            updates.append("meeting_title = ?")
            params.append(meeting_title)

        if meeting_date is not None:
            updates.append("meeting_date = ?")
            params.append(meeting_date)

        if summary is not None:
            updates.append("summary = ?")
            params.append(summary)

        if key_points is not None:
            updates.append("key_points = ?")
            params.append(key_points)

        if action_items is not None:
            updates.append("action_items = ?")
            params.append(action_items)

        if not updates:
            conn.close()
            return {"success": True, "message": "No updates provided"}

        params.append(transcript_id)
        cursor.execute(f"""
            UPDATE meeting_transcripts SET {', '.join(updates)} WHERE id = ?
        """, params)

        conn.commit()

        # Fetch updated transcript
        cursor.execute("SELECT * FROM meeting_transcripts WHERE id = ?", (transcript_id,))
        transcript = dict(cursor.fetchone())
        transcript['key_points'] = _parse_json_field(transcript.get('key_points'))
        transcript['action_items'] = _parse_json_field(transcript.get('action_items'))
        transcript['participants'] = _parse_json_field(transcript.get('participants'))

        conn.close()

        return {
            "success": True,
            "message": "Transcript updated successfully",
            "transcript": transcript
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# CLAUDE SUMMARY ENDPOINT
# ============================================================================

@router.post("/meeting-transcripts/{transcript_id}/claude-summary")
async def save_claude_summary(transcript_id: int, request: ClaudeSummaryRequest):
    """
    Save a Claude-generated summary with action items.

    This endpoint:
    1. Updates the transcript with summary, key_points, action_items
    2. Creates tasks from action_items in the tasks table
    3. Optionally creates a meeting record for next_meeting_date

    Returns the created task IDs and meeting ID (if created).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if transcript exists
        cursor.execute("SELECT * FROM meeting_transcripts WHERE id = ?", (transcript_id,))
        transcript = cursor.fetchone()
        if not transcript:
            conn.close()
            raise HTTPException(status_code=404, detail="Transcript not found")

        transcript = dict(transcript)

        # Get proposal_id if proposal_code provided
        proposal_id = None
        if request.proposal_code:
            cursor.execute(
                "SELECT proposal_id FROM proposals WHERE project_code = ?",
                (request.proposal_code,)
            )
            proposal_row = cursor.fetchone()
            if proposal_row:
                proposal_id = proposal_row['proposal_id']

        # If no proposal_code but transcript has detected_project_code, use that
        if not proposal_id and transcript.get('detected_project_code'):
            cursor.execute(
                "SELECT proposal_id FROM proposals WHERE project_code = ?",
                (transcript['detected_project_code'],)
            )
            proposal_row = cursor.fetchone()
            if proposal_row:
                proposal_id = proposal_row['proposal_id']

        # Update transcript with summary
        cursor.execute("""
            UPDATE meeting_transcripts SET
                summary = ?,
                key_points = ?,
                action_items = ?,
                detected_project_code = COALESCE(?, detected_project_code)
            WHERE id = ?
        """, (
            request.summary,
            json.dumps(request.key_points) if request.key_points else None,
            json.dumps([item.dict() for item in request.action_items]) if request.action_items else None,
            request.proposal_code,
            transcript_id
        ))

        created_task_ids = []
        created_meeting_id = None

        # Create tasks from action items
        if request.action_items:
            for item in request.action_items:
                cursor.execute("""
                    INSERT INTO tasks (
                        title,
                        description,
                        task_type,
                        priority,
                        status,
                        due_date,
                        proposal_id,
                        project_code,
                        source_transcript_id,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    item.task,
                    f"From meeting transcript: {transcript.get('meeting_title', 'Unknown')}",
                    'action_item',
                    item.priority or 'normal',
                    'pending',
                    item.due_date,
                    proposal_id,
                    request.proposal_code or transcript.get('detected_project_code'),
                    transcript_id
                ))
                created_task_ids.append(cursor.lastrowid)

        # Create meeting record for next meeting date
        if request.next_meeting_date:
            cursor.execute("""
                INSERT INTO meetings (
                    title,
                    description,
                    meeting_type,
                    meeting_date,
                    proposal_id,
                    project_code,
                    status,
                    source,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                f"Follow-up: {transcript.get('meeting_title', 'Meeting')}",
                f"Follow-up meeting scheduled from transcript discussion",
                'client_call',
                request.next_meeting_date,
                proposal_id,
                request.proposal_code or transcript.get('detected_project_code'),
                'scheduled',
                'transcript_extracted'
            ))
            created_meeting_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Claude summary saved successfully",
            "transcript_id": transcript_id,
            "proposal_id": proposal_id,
            "created_task_ids": created_task_ids,
            "created_meeting_id": created_meeting_id,
            "tasks_created": len(created_task_ids),
            "meeting_created": created_meeting_id is not None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# TRANSCRIPT CONSOLIDATION (Orphaned service now wired - Dec 2025)
# ============================================================================

@router.post("/meeting-transcripts/consolidate")
async def consolidate_transcripts(
    min_chunks: int = Query(2, ge=1, description="Minimum chunks to consolidate"),
    dry_run: bool = Query(False, description="Preview only, don't apply")
):
    """
    Consolidate fragmented Whisper transcripts into complete records.

    When Whisper hits time limits, it creates multiple chunks for a single meeting.
    This endpoint finds and consolidates them.

    Returns:
        - candidates: Transcripts that can be consolidated
        - consolidated: Number of transcripts consolidated (if not dry_run)
    """
    try:
        from api.services import transcript_consolidation_service

        # Find consolidation candidates
        candidates = transcript_consolidation_service.find_consolidation_candidates(
            min_chunks=min_chunks
        )

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "candidates": candidates,
                "total_chunks": sum(c.get("chunk_count", 0) for c in candidates),
                "message": f"Found {len(candidates)} transcripts to consolidate"
            }

        # Actually consolidate
        result = transcript_consolidation_service.consolidate_all(min_chunks=min_chunks)

        return {
            "success": True,
            "dry_run": False,
            "consolidated": result.get("consolidated", 0),
            "errors": result.get("errors", []),
            "message": f"Consolidated {result.get('consolidated', 0)} transcripts"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")
