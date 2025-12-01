"""
Transcripts Router - Meeting transcript management endpoints

Endpoints:
    GET /api/meeting-transcripts - List all transcripts
    GET /api/meeting-transcripts/{id} - Get single transcript
    GET /api/meeting-transcripts/stats - Transcript statistics
    GET /api/meeting-transcripts/by-project/{project_code} - Project transcripts
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3
import json

from api.dependencies import DB_PATH
from api.helpers import list_response, item_response

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

        # Get paginated results
        cursor.execute(f"""
            SELECT * FROM meeting_transcripts
            WHERE {where_sql}
            ORDER BY created_at DESC
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meeting-transcripts/stats")
async def get_transcript_stats():
    """Get transcript statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN detected_project_code IS NOT NULL THEN 1 ELSE 0 END) as linked,
                SUM(CASE WHEN summary IS NOT NULL THEN 1 ELSE 0 END) as with_summary,
                AVG(duration_seconds) as avg_duration,
                COUNT(DISTINCT detected_project_code) as unique_projects
            FROM meeting_transcripts
        """)

        row = cursor.fetchone()
        stats = dict(row) if row else {}

        conn.close()

        return item_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meeting-transcripts/{transcript_id}")
async def get_transcript(transcript_id: int):
    """Get a single transcript by ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM meeting_transcripts WHERE id = ?
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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_code}/transcripts")
async def get_project_transcripts(project_code: str):
    """Get transcripts for a specific project (alternative route)"""
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

        # Get transcripts by project_id or detected_project_code
        cursor.execute("""
            SELECT * FROM meeting_transcripts
            WHERE project_id = ? OR detected_project_code = ?
            ORDER BY COALESCE(meeting_date, recorded_date, created_at) DESC
        """, (project_id, project_code))

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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))
