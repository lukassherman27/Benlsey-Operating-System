"""
Learning Router - AI learning and pattern endpoints

Endpoints:
    GET /api/learning/stats - Learning statistics
    GET /api/learning/patterns - Learned patterns
    GET /api/learning/suggestions - AI suggestions for review
    POST /api/learning/suggestions/{id}/approve - Approve a suggestion
    POST /api/learning/suggestions/{id}/reject - Reject a suggestion
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3

from api.dependencies import DB_PATH
from api.helpers import item_response, list_response

router = APIRouter(prefix="/api", tags=["learning"])


@router.get("/learning/stats")
async def get_learning_stats():
    """Get AI learning statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Suggestion stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
            FROM ai_suggestions
        """)
        suggestions = dict(cursor.fetchone() or {})

        # Training feedback stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN human_verified = 1 THEN 1 ELSE 0 END) as correct,
                SUM(CASE WHEN human_verified = 0 THEN 1 ELSE 0 END) as incorrect
            FROM training_data
        """)
        feedback = dict(cursor.fetchone() or {})

        # Pattern count
        cursor.execute("""
            SELECT COUNT(*) as count FROM email_learned_patterns WHERE is_active = 1
        """)
        patterns_row = cursor.fetchone()
        active_patterns = patterns_row['count'] if patterns_row else 0

        conn.close()

        # Calculate approval rate
        total_reviewed = suggestions.get('approved', 0) + suggestions.get('rejected', 0)
        approval_rate = round(
            (suggestions.get('approved', 0) / max(total_reviewed, 1)) * 100, 1
        )

        return {
            "success": True,
            "suggestions": suggestions,
            "feedback": feedback,
            "active_patterns": active_patterns,
            "approval_rate": approval_rate
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/patterns")
async def get_learning_patterns(pattern_type: Optional[str] = None):
    """Get learned patterns"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT * FROM email_learned_patterns
            WHERE is_active = 1
        """
        params = []

        if pattern_type:
            query += " AND pattern_type = ?"
            params.append(pattern_type)

        query += " ORDER BY confidence_score DESC, evidence_count DESC"

        cursor.execute(query, params)
        patterns = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "patterns": patterns,
            "count": len(patterns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning/suggestions")
async def get_learning_suggestions(
    suggestion_type: Optional[str] = None,
    project_code: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Get AI suggestions pending review"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT * FROM ai_suggestions
            WHERE status = 'pending'
        """
        params = []

        if suggestion_type:
            query += " AND suggestion_type = ?"
            params.append(suggestion_type)

        if project_code:
            query += " AND (source_reference LIKE ? OR suggested_data LIKE ?)"
            params.extend([f"%{project_code}%", f"%{project_code}%"])

        query += " ORDER BY confidence_score DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        suggestions = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/suggestions/{suggestion_id}/approve")
async def approve_learning_suggestion(
    suggestion_id: int,
    reviewed_by: str = "system",
    apply_changes: bool = True
):
    """Approve an AI suggestion"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ai_suggestions
            SET status = 'approved',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE suggestion_id = ?
        """, (reviewed_by, suggestion_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return {
            "success": success,
            "suggestion_id": suggestion_id,
            "applied": apply_changes and success
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning/suggestions/{suggestion_id}/reject")
async def reject_learning_suggestion(
    suggestion_id: int,
    reviewed_by: str = "system",
    reason: Optional[str] = None
):
    """Reject an AI suggestion"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ai_suggestions
            SET status = 'rejected',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                review_notes = ?
            WHERE suggestion_id = ?
        """, (reviewed_by, reason, suggestion_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return {
            "success": success,
            "suggestion_id": suggestion_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
