"""
Suggestions Router - AI suggestion management endpoints

Endpoints:
    GET /api/suggestions - List suggestions
    GET /api/suggestions/stats - Suggestion statistics
    POST /api/suggestions/{id}/approve - Approve suggestion
    POST /api/suggestions/{id}/reject - Reject suggestion
    POST /api/suggestions/bulk-approve - Bulk approve
    ... and more
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import sqlite3
import json

from api.services import admin_service, ai_learning_service, email_orchestrator
from backend.services.suggestion_handlers import HandlerRegistry, ChangePreview
from api.dependencies import DB_PATH
from api.models import (
    SuggestionApproveRequest, SuggestionRejectRequest, BulkApproveRequest,
    BulkRejectRequest, BulkApproveByIdsRequest, SuggestionRejectWithCorrectionRequest,
    SuggestionApproveWithContextRequest, PatternCreateRequest, PatternUpdateRequest
)
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["suggestions"])


# ============================================================================
# SUGGESTION LIST ENDPOINTS
# ============================================================================

@router.get("/suggestions")
async def get_suggestions(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    suggestion_type: Optional[str] = Query(None, description="Filter by type"),
    field_name: Optional[str] = Query(None, description="Filter by field_name: new_contact, project_alias, etc."),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    # Also support page/per_page for backward compat
    page: int = Query(None, ge=1),
    per_page: int = Query(None, ge=1, le=200)
):
    """Get AI suggestions with optional filtering"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Handle page/per_page if provided (backward compat)
        if page is not None and per_page is not None:
            offset = (page - 1) * per_page
            limit = per_page

        # Build query with filters
        where_clauses = []
        params = []

        if status:
            where_clauses.append("status = ?")
            params.append(status)
        else:
            # Default to pending
            where_clauses.append("status = 'pending'")

        # Filter by suggestion_type (field_name is alias for backward compat)
        filter_type = field_name or suggestion_type
        if filter_type:
            where_clauses.append("suggestion_type = ?")
            params.append(filter_type)

        if min_confidence is not None:
            where_clauses.append("confidence_score >= ?")
            params.append(min_confidence)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM ai_suggestions WHERE {where_sql}", params)
        total = cursor.fetchone()[0]

        # Get paginated results
        cursor.execute(f"""
            SELECT * FROM ai_suggestions
            WHERE {where_sql}
            ORDER BY confidence_score DESC, created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])

        suggestions = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Return in format expected by frontend
        return {
            "success": True,
            "suggestions": suggestions,
            "total": total,
            "returned": len(suggestions),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/stats")
async def get_suggestion_stats():
    """Get suggestion statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                AVG(confidence_score) as avg_confidence
            FROM ai_suggestions
        """)

        row = cursor.fetchone()
        base_stats = dict(row) if row else {}

        # Get by suggestion_type breakdown for pending
        cursor.execute("""
            SELECT suggestion_type, COUNT(*) as count
            FROM ai_suggestions
            WHERE status = 'pending'
            GROUP BY suggestion_type
        """)

        pending_by_field = {row['suggestion_type']: row['count'] for row in cursor.fetchall()}

        # Get high confidence pending count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM ai_suggestions
            WHERE status = 'pending' AND confidence_score >= 0.8
        """)
        high_conf_row = cursor.fetchone()
        high_confidence_pending = high_conf_row['count'] if high_conf_row else 0

        # Get avg confidence for pending
        cursor.execute("""
            SELECT AVG(confidence_score) as avg_conf
            FROM ai_suggestions
            WHERE status = 'pending'
        """)
        avg_row = cursor.fetchone()
        avg_pending_confidence = round(avg_row['avg_conf'] or 0, 3)

        conn.close()

        # Format response for frontend compatibility
        stats = {
            'by_status': {
                'pending': base_stats.get('pending', 0),
                'approved': base_stats.get('approved', 0),
                'rejected': base_stats.get('rejected', 0),
            },
            'pending_by_field': pending_by_field,
            'high_confidence_pending': high_confidence_pending,
            'avg_pending_confidence': avg_pending_confidence,
        }

        response = item_response(stats)
        response.update(stats)  # Flatten at root for frontend
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/grouped")
async def get_suggestions_grouped(
    status: str = Query("pending", description="Filter by status: pending, approved, rejected")
):
    """
    Get suggestions grouped by project_code.

    Returns:
        - groups: List of project groups, each with project_code, project_name, suggestion_count, suggestions
        - ungrouped: Suggestions without a project_code
        - total: Total count
    """
    try:
        result = email_orchestrator.get_suggestions_grouped(status=status)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUGGESTION ACTIONS
# ============================================================================

@router.post("/suggestions/{suggestion_id}/approve")
async def approve_suggestion(suggestion_id: int, request: Optional[SuggestionApproveRequest] = None):
    """Approve an AI suggestion from ai_suggestions table"""
    try:
        # Use ai_learning_service which works with ai_suggestions table
        result = ai_learning_service.approve_suggestion(
            suggestion_id,
            reviewed_by="api",
            apply_changes=True
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', result.get('error', 'Unknown error')))
        return action_response(True, message="Suggestion approved")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(suggestion_id: int, request: Optional[SuggestionRejectRequest] = None):
    """Reject an AI suggestion"""
    try:
        reason = request.reason if request else None
        # Use ai_learning_service which has the reject_suggestion method
        result = ai_learning_service.reject_suggestion(
            suggestion_id,
            reviewed_by="api",
            reason=reason
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', result.get('error', 'Unknown error')))
        return action_response(True, message="Suggestion rejected")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/bulk-approve")
async def bulk_approve_suggestions(request: BulkApproveRequest):
    """Bulk approve suggestions above confidence threshold"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get suggestions above threshold
        cursor.execute("""
            SELECT suggestion_id FROM ai_suggestions
            WHERE status = 'pending' AND confidence >= ?
        """, (request.min_confidence,))

        suggestion_ids = [row['suggestion_id'] for row in cursor.fetchall()]

        approved_count = 0
        for sid in suggestion_ids:
            result = admin_service.approve_suggestion(sid)
            if result.get('success'):
                approved_count += 1

        conn.close()

        return action_response(
            True,
            data={"approved": approved_count, "total": len(suggestion_ids)},
            message=f"Approved {approved_count} suggestions"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/bulk-approve-by-ids")
async def bulk_approve_by_ids(request: BulkApproveByIdsRequest):
    """Bulk approve suggestions by ID list"""
    try:
        approved_count = 0
        errors = []

        for sid in request.suggestion_ids:
            try:
                result = ai_learning_service.approve_suggestion(
                    sid,
                    reviewed_by="bulk_api",
                    apply_changes=True
                )
                if result.get('success'):
                    approved_count += 1
                else:
                    errors.append({"id": sid, "error": result.get('message', 'Unknown error')})
            except Exception as e:
                errors.append({"id": sid, "error": str(e)})

        return action_response(
            True,
            data={
                "approved": approved_count,
                "total": len(request.suggestion_ids),
                "errors": errors
            },
            message=f"Approved {approved_count} of {len(request.suggestion_ids)} suggestions"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/bulk-reject")
async def bulk_reject_suggestions(request: BulkRejectRequest):
    """Bulk reject suggestions by ID list"""
    try:
        rejected_count = 0
        errors = []

        for sid in request.suggestion_ids:
            try:
                result = ai_learning_service.reject_suggestion(
                    sid,
                    reviewed_by="bulk_api",
                    reason=request.reason
                )
                if result.get('success'):
                    rejected_count += 1
                else:
                    errors.append({"id": sid, "error": result.get('message', 'Unknown error')})
            except Exception as e:
                errors.append({"id": sid, "error": str(e)})

        return action_response(
            True,
            data={
                "rejected": rejected_count,
                "total": len(request.suggestion_ids),
                "errors": errors
            },
            message=f"Rejected {rejected_count} of {len(request.suggestion_ids)} suggestions"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/correct")
async def correct_suggestion(
    suggestion_id: int,
    corrected_project_id: Optional[int] = None,
    corrected_project_code: Optional[str] = None,
    notes: Optional[str] = None
):
    """Approve a suggestion with corrections (modified data)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the suggestion
        cursor.execute("SELECT * FROM ai_suggestions WHERE suggestion_id = ?", (suggestion_id,))
        suggestion = cursor.fetchone()

        if not suggestion:
            conn.close()
            raise HTTPException(status_code=404, detail="Suggestion not found")

        suggestion = dict(suggestion)
        suggestion_type = suggestion.get('suggestion_type')

        # Handle email_link type specifically
        if suggestion_type == 'email_link':
            # Parse existing suggested_data
            import json
            suggested_data = {}
            if suggestion.get('suggested_data'):
                try:
                    suggested_data = json.loads(suggestion['suggested_data'])
                except:
                    pass

            # Use corrected values if provided
            email_id = suggested_data.get('email_id')
            project_id = corrected_project_id or suggested_data.get('project_id')
            project_code = corrected_project_code or suggested_data.get('project_code')

            if not email_id:
                conn.close()
                raise HTTPException(status_code=400, detail="No email_id in suggestion data")

            if not project_id and project_code:
                # Look up project_id from project_code
                cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
                project_row = cursor.fetchone()
                if project_row:
                    project_id = project_row['project_id']

            if not project_id:
                conn.close()
                raise HTTPException(status_code=400, detail="No valid project_id provided or found")

            # Create the actual email_project_link
            cursor.execute("""
                INSERT OR REPLACE INTO email_project_links (
                    email_id, project_id, link_method, confidence, evidence, created_at
                ) VALUES (?, ?, 'ai_corrected', ?, ?, datetime('now'))
            """, (
                email_id,
                project_id,
                suggestion.get('confidence_score', 0.8),
                f"AI suggestion corrected by user. Original: {suggestion.get('suggested_data')}. Notes: {notes or 'None'}"
            ))

            # Update suggestion status to 'modified'
            cursor.execute("""
                UPDATE ai_suggestions
                SET status = 'modified',
                    reviewed_at = datetime('now'),
                    reviewed_by = 'api'
                WHERE suggestion_id = ?
            """, (suggestion_id,))

            conn.commit()
            conn.close()

            return action_response(
                True,
                data={"email_id": email_id, "project_id": project_id, "action": "email_linked"},
                message="Email link created with corrections"
            )
        else:
            # For other suggestion types, just mark as modified
            cursor.execute("""
                UPDATE ai_suggestions
                SET status = 'modified',
                    reviewed_at = datetime('now'),
                    reviewed_by = 'api'
                WHERE suggestion_id = ?
            """, (suggestion_id,))

            conn.commit()
            conn.close()

            return action_response(True, message="Suggestion marked as corrected")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EMAIL LINK SUGGESTION HANDLING
# ============================================================================

@router.get("/suggestions/email-links")
async def get_email_link_suggestions(
    status: str = "pending",
    min_confidence: float = 0.0,
    limit: int = 50,
    offset: int = 0
):
    """Get email link suggestions specifically"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.*,
                e.subject as email_subject,
                e.sender_email,
                e.date as email_date,
                p.project_code as linked_project_code,
                p.project_title as linked_project_title
            FROM ai_suggestions s
            LEFT JOIN emails e ON json_extract(s.suggested_data, '$.email_id') = e.email_id
            LEFT JOIN projects p ON json_extract(s.suggested_data, '$.project_id') = p.project_id
            WHERE s.suggestion_type = 'email_link'
              AND s.status = ?
              AND s.confidence_score >= ?
            ORDER BY s.confidence_score DESC, s.created_at DESC
            LIMIT ? OFFSET ?
        """, (status, min_confidence, limit, offset))

        suggestions = [dict(row) for row in cursor.fetchall()]

        # Get total count
        cursor.execute("""
            SELECT COUNT(*) FROM ai_suggestions
            WHERE suggestion_type = 'email_link' AND status = ? AND confidence_score >= ?
        """, (status, min_confidence))
        total = cursor.fetchone()[0]

        conn.close()

        return {
            "success": True,
            "suggestions": suggestions,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/approve-email-link")
async def approve_email_link_suggestion(suggestion_id: int):
    """Specifically approve an email_link suggestion and create the actual link"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the suggestion
        cursor.execute("""
            SELECT * FROM ai_suggestions
            WHERE suggestion_id = ? AND suggestion_type = 'email_link'
        """, (suggestion_id,))
        suggestion = cursor.fetchone()

        if not suggestion:
            conn.close()
            raise HTTPException(status_code=404, detail="Email link suggestion not found")

        suggestion = dict(suggestion)

        # Parse suggested_data
        import json
        suggested_data = {}
        if suggestion.get('suggested_data'):
            try:
                suggested_data = json.loads(suggestion['suggested_data'])
            except:
                pass

        email_id = suggested_data.get('email_id')
        project_id = suggested_data.get('project_id')
        project_code = suggested_data.get('project_code')

        if not email_id:
            conn.close()
            raise HTTPException(status_code=400, detail="No email_id in suggestion data")

        if not project_id and project_code:
            cursor.execute("SELECT project_id FROM projects WHERE project_code = ?", (project_code,))
            project_row = cursor.fetchone()
            if project_row:
                project_id = project_row['project_id']

        if not project_id:
            conn.close()
            raise HTTPException(status_code=400, detail="No valid project found for linking")

        # Create the email_project_link
        cursor.execute("""
            INSERT OR REPLACE INTO email_project_links (
                email_id, project_id, link_method, confidence, evidence, created_at
            ) VALUES (?, ?, 'ai_approved', ?, ?, datetime('now'))
        """, (
            email_id,
            project_id,
            suggestion.get('confidence_score', 0.8),
            f"AI suggestion approved. {suggestion.get('description', '')}"
        ))

        # Update suggestion status
        cursor.execute("""
            UPDATE ai_suggestions
            SET status = 'approved',
                reviewed_at = datetime('now'),
                reviewed_by = 'api'
            WHERE suggestion_id = ?
        """, (suggestion_id,))

        conn.commit()
        conn.close()

        return action_response(
            True,
            data={"email_id": email_id, "project_id": project_id},
            message="Email successfully linked to project"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TRANSCRIPT LINK SUGGESTION HANDLING
# ============================================================================

@router.get("/suggestions/transcript-links")
async def get_transcript_link_suggestions(
    status: str = "pending",
    min_confidence: float = 0.0,
    limit: int = 50,
    offset: int = 0
):
    """Get transcript link suggestions specifically"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.*,
                mt.audio_filename,
                mt.meeting_title,
                mt.meeting_date,
                substr(mt.transcript, 1, 500) as transcript_preview,
                p.project_name as linked_project_name,
                p.client_company as linked_client
            FROM ai_suggestions s
            LEFT JOIN meeting_transcripts mt ON json_extract(s.suggested_data, '$.transcript_id') = mt.id
            LEFT JOIN proposals p ON json_extract(s.suggested_data, '$.proposal_id') = p.proposal_id
            WHERE s.suggestion_type = 'transcript_link'
              AND s.status = ?
              AND s.confidence_score >= ?
            ORDER BY s.confidence_score DESC, s.created_at DESC
            LIMIT ? OFFSET ?
        """, (status, min_confidence, limit, offset))

        suggestions = [dict(row) for row in cursor.fetchall()]

        # Get total count
        cursor.execute("""
            SELECT COUNT(*) FROM ai_suggestions
            WHERE suggestion_type = 'transcript_link' AND status = ? AND confidence_score >= ?
        """, (status, min_confidence))
        total = cursor.fetchone()[0]

        conn.close()

        return {
            "success": True,
            "suggestions": suggestions,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/approve-transcript-link")
async def approve_transcript_link_suggestion(suggestion_id: int):
    """Specifically approve a transcript_link suggestion and create the actual link"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the suggestion
        cursor.execute("""
            SELECT * FROM ai_suggestions
            WHERE suggestion_id = ? AND suggestion_type = 'transcript_link'
        """, (suggestion_id,))
        suggestion = cursor.fetchone()

        if not suggestion:
            conn.close()
            raise HTTPException(status_code=404, detail="Transcript link suggestion not found")

        suggestion = dict(suggestion)

        # Parse suggested_data
        import json
        suggested_data = {}
        if suggestion.get('suggested_data'):
            try:
                suggested_data = json.loads(suggestion['suggested_data'])
            except:
                pass

        transcript_id = suggested_data.get('transcript_id')
        proposal_id = suggested_data.get('proposal_id')
        project_code = suggested_data.get('project_code') or suggestion.get('project_code')

        if not transcript_id:
            conn.close()
            raise HTTPException(status_code=400, detail="No transcript_id in suggestion data")

        if not proposal_id:
            conn.close()
            raise HTTPException(status_code=400, detail="No proposal_id in suggestion data")

        # Update the meeting_transcripts record to link it
        cursor.execute("""
            UPDATE meeting_transcripts
            SET proposal_id = ?,
                detected_project_code = ?
            WHERE id = ?
        """, (proposal_id, project_code, transcript_id))

        # Update suggestion status
        cursor.execute("""
            UPDATE ai_suggestions
            SET status = 'approved',
                reviewed_at = datetime('now'),
                reviewed_by = 'api'
            WHERE suggestion_id = ?
        """, (suggestion_id,))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "data": {"transcript_id": transcript_id, "proposal_id": proposal_id, "project_code": project_code},
            "message": "Transcript successfully linked to proposal"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INTEL ENDPOINTS (AI Intelligence)
# ============================================================================

@router.get("/intel/suggestions")
async def get_intel_suggestions(limit: int = Query(20, ge=1, le=100)):
    """Get AI intelligence suggestions"""
    try:
        suggestions = ai_learning_service.get_pending_suggestions(limit=limit)
        response = list_response(suggestions, len(suggestions))
        response["suggestions"] = suggestions  # Backward compat
        response["count"] = len(suggestions)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intel/suggestions/{suggestion_id}/decision")
async def record_suggestion_decision(
    suggestion_id: int,
    decision: str = Query(..., regex="^(approve|reject)$")
):
    """Record decision on an intelligence suggestion"""
    try:
        if decision == "approve":
            result = admin_service.approve_suggestion(suggestion_id)
        else:
            result = admin_service.reject_suggestion(suggestion_id)

        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message'))
        return action_response(True, message=f"Suggestion {decision}d")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intel/patterns")
async def get_learned_patterns():
    """Get patterns learned by AI"""
    try:
        patterns = ai_learning_service.get_learned_patterns()
        response = item_response({"patterns": patterns})
        response["patterns"] = patterns  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intel/decisions")
async def get_recent_decisions(limit: int = Query(50, ge=1, le=200)):
    """Get recent AI decisions"""
    try:
        decisions = ai_learning_service.get_recent_decisions(limit=limit)
        response = list_response(decisions, len(decisions))
        response["decisions"] = decisions  # Backward compat
        response["count"] = len(decisions)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SUGGESTION PREVIEW, ROLLBACK, SOURCE ENDPOINTS
# ============================================================================

@router.get("/suggestions/{suggestion_id}/preview")
async def get_suggestion_preview(suggestion_id: int):
    """
    Get a preview of what changes a suggestion will make.

    Returns:
        - is_actionable: Whether this suggestion makes DB changes
        - action: The type of change (insert, update, delete, none)
        - table: The target table
        - summary: Human-readable description
        - changes: List of field-level changes
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the suggestion
        cursor.execute("SELECT * FROM ai_suggestions WHERE suggestion_id = ?", (suggestion_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Suggestion not found")

        suggestion = dict(row)
        suggestion_type = suggestion.get('suggestion_type')

        # Parse suggested_data
        suggested_data = {}
        if suggestion.get('suggested_data'):
            try:
                suggested_data = json.loads(suggestion['suggested_data'])
            except (json.JSONDecodeError, TypeError):
                pass

        # Try to get handler for this suggestion type
        handler = HandlerRegistry.get_handler(suggestion_type, conn)

        if handler:
            # Use handler's preview method
            preview = handler.preview(suggestion, suggested_data)
            conn.close()
            return {
                "success": True,
                "is_actionable": handler.is_actionable,
                "action": preview.action,
                "table": preview.table,
                "summary": preview.summary,
                "changes": preview.changes
            }
        else:
            # No handler for this type
            conn.close()
            return {
                "success": True,
                "is_actionable": False,
                "action": "none",
                "table": suggestion.get('target_table'),
                "summary": f"No handler registered for suggestion type '{suggestion_type}'",
                "changes": []
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/rollback")
async def rollback_suggestion(suggestion_id: int):
    """
    Rollback an approved suggestion, undoing its changes.

    Only works for:
    - Suggestions with status='approved'
    - Suggestions that have rollback_data stored

    Returns:
        - success: Whether rollback succeeded
        - message: Description of what was done
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the suggestion - must be approved and have rollback_data
        cursor.execute("""
            SELECT * FROM ai_suggestions
            WHERE suggestion_id = ?
            AND status = 'approved'
            AND rollback_data IS NOT NULL
        """, (suggestion_id,))
        row = cursor.fetchone()

        if not row:
            # Check if suggestion exists at all
            cursor.execute("SELECT status, rollback_data FROM ai_suggestions WHERE suggestion_id = ?", (suggestion_id,))
            check_row = cursor.fetchone()
            conn.close()

            if not check_row:
                raise HTTPException(status_code=404, detail="Suggestion not found")
            elif check_row['status'] != 'approved':
                raise HTTPException(status_code=400, detail=f"Cannot rollback: suggestion status is '{check_row['status']}', not 'approved'")
            else:
                raise HTTPException(status_code=400, detail="Cannot rollback: no rollback data stored for this suggestion")

        suggestion = dict(row)
        suggestion_type = suggestion.get('suggestion_type')

        # Parse rollback_data
        try:
            rollback_data = json.loads(suggestion['rollback_data'])
        except (json.JSONDecodeError, TypeError):
            conn.close()
            raise HTTPException(status_code=400, detail="Invalid rollback data format")

        # Get handler
        handler = HandlerRegistry.get_handler(suggestion_type, conn)

        if not handler:
            conn.close()
            raise HTTPException(status_code=400, detail=f"No handler registered for suggestion type '{suggestion_type}'")

        # Execute rollback
        success = handler.rollback(rollback_data)

        if success:
            # Update suggestion status to 'rolled_back'
            cursor.execute("""
                UPDATE ai_suggestions
                SET status = 'rolled_back',
                    reviewed_at = datetime('now')
                WHERE suggestion_id = ?
            """, (suggestion_id,))
            conn.commit()
            conn.close()
            return {
                "success": True,
                "message": f"Successfully rolled back suggestion {suggestion_id}"
            }
        else:
            conn.close()
            raise HTTPException(status_code=500, detail="Rollback operation failed")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{suggestion_id}/source")
async def get_suggestion_source(suggestion_id: int):
    """
    Get the source content (email or transcript) that triggered a suggestion.

    Returns:
        - source_type: 'email', 'transcript', 'pattern', or null
        - content: The source content (body/transcript text)
        - metadata: Additional info (subject, sender, date, etc.)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the suggestion
        cursor.execute("""
            SELECT source_type, source_id, source_reference
            FROM ai_suggestions
            WHERE suggestion_id = ?
        """, (suggestion_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Suggestion not found")

        suggestion = dict(row)
        source_type = suggestion.get('source_type')
        source_id = suggestion.get('source_id')

        if not source_type or not source_id:
            conn.close()
            return {
                "success": True,
                "source_type": None,
                "content": None,
                "metadata": {
                    "note": "No source information available for this suggestion"
                }
            }

        if source_type == 'email':
            # Fetch email details
            cursor.execute("""
                SELECT
                    email_id, subject, body_full, sender_email,
                    recipient_emails, date, folder, message_id
                FROM emails
                WHERE email_id = ?
            """, (source_id,))
            email_row = cursor.fetchone()
            conn.close()

            if not email_row:
                return {
                    "success": True,
                    "source_type": "email",
                    "content": None,
                    "metadata": {
                        "note": f"Source email (id={source_id}) not found",
                        "source_reference": suggestion.get('source_reference')
                    }
                }

            email = dict(email_row)
            return {
                "success": True,
                "source_type": "email",
                "content": email.get('body_full'),
                "metadata": {
                    "email_id": email.get('email_id'),
                    "subject": email.get('subject'),
                    "sender": email.get('sender_email'),
                    "recipients": email.get('recipient_emails'),
                    "date": email.get('date'),
                    "folder": email.get('folder')
                }
            }

        elif source_type == 'transcript':
            # Fetch transcript details
            cursor.execute("""
                SELECT
                    id, audio_filename, meeting_title, meeting_date,
                    transcript, summary, duration_seconds
                FROM meeting_transcripts
                WHERE id = ?
            """, (source_id,))
            transcript_row = cursor.fetchone()
            conn.close()

            if not transcript_row:
                return {
                    "success": True,
                    "source_type": "transcript",
                    "content": None,
                    "metadata": {
                        "note": f"Source transcript (id={source_id}) not found",
                        "source_reference": suggestion.get('source_reference')
                    }
                }

            transcript = dict(transcript_row)
            return {
                "success": True,
                "source_type": "transcript",
                "content": transcript.get('transcript'),
                "metadata": {
                    "transcript_id": transcript.get('id'),
                    "title": transcript.get('meeting_title'),
                    "filename": transcript.get('audio_filename'),
                    "date": transcript.get('meeting_date'),
                    "summary": transcript.get('summary'),
                    "duration_seconds": transcript.get('duration_seconds')
                }
            }

        else:
            # Other source types (pattern, etc.)
            conn.close()
            return {
                "success": True,
                "source_type": source_type,
                "content": None,
                "metadata": {
                    "source_id": source_id,
                    "source_reference": suggestion.get('source_reference'),
                    "note": f"Source type '{source_type}' does not have fetchable content"
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENHANCED FEEDBACK ENDPOINTS
# ============================================================================

@router.post("/suggestions/{suggestion_id}/reject-with-correction")
async def reject_with_correction(
    suggestion_id: int,
    request: SuggestionRejectWithCorrectionRequest
):
    """
    Reject a suggestion and optionally create the correct link + learn a pattern.

    This is used when the AI suggested wrong but the user knows the correct answer.
    For example: "This email should go to project X, not project Y"

    Flow:
    1. Mark suggestion as rejected with reason
    2. If correct_project_code provided, create the correct email_project_link
    3. If create_pattern is True, store a learned pattern for future suggestions
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the suggestion
        cursor.execute("SELECT * FROM ai_suggestions WHERE suggestion_id = ?", (suggestion_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Suggestion not found")

        suggestion = dict(row)
        suggestion_type = suggestion.get('suggestion_type')

        # Parse suggested_data
        suggested_data = {}
        if suggestion.get('suggested_data'):
            try:
                suggested_data = json.loads(suggestion['suggested_data'])
            except (json.JSONDecodeError, TypeError):
                pass

        result_data = {
            "suggestion_id": suggestion_id,
            "rejection_reason": request.rejection_reason,
            "corrected": False,
            "pattern_created": False
        }

        # Handle email_link type with correction
        if suggestion_type == 'email_link' and request.correct_project_code:
            email_id = suggested_data.get('email_id')

            if email_id:
                # Look up project_id from project_code
                cursor.execute(
                    "SELECT project_id FROM projects WHERE project_code = ?",
                    (request.correct_project_code,)
                )
                project_row = cursor.fetchone()

                if project_row:
                    project_id = project_row['project_id']

                    # Create the correct link
                    cursor.execute("""
                        INSERT OR REPLACE INTO email_project_links (
                            email_id, project_id, link_method, confidence, evidence, created_at
                        ) VALUES (?, ?, 'user_corrected', 1.0, ?, datetime('now'))
                    """, (
                        email_id,
                        project_id,
                        f"User corrected suggestion {suggestion_id}. Reason: {request.rejection_reason}"
                    ))
                    result_data["corrected"] = True
                    result_data["correct_link"] = {
                        "email_id": email_id,
                        "project_id": project_id,
                        "project_code": request.correct_project_code
                    }

                    # Create pattern if requested
                    if request.create_pattern:
                        # Get sender email from the email
                        cursor.execute(
                            "SELECT sender_email FROM emails WHERE email_id = ?",
                            (email_id,)
                        )
                        email_row = cursor.fetchone()

                        if email_row and email_row['sender_email']:
                            sender_email = email_row['sender_email'].lower().strip()

                            # Insert sender_to_project pattern
                            cursor.execute("""
                                INSERT OR REPLACE INTO email_learned_patterns (
                                    pattern_type, pattern_key, pattern_key_normalized,
                                    target_type, target_id, target_code,
                                    confidence, times_correct,
                                    created_from_suggestion_id, created_from_email_id,
                                    notes, created_at, updated_at
                                ) VALUES (
                                    'sender_to_project', ?, ?,
                                    'project', ?, ?,
                                    0.9, 1,
                                    ?, ?,
                                    ?, datetime('now'), datetime('now')
                                )
                            """, (
                                sender_email, sender_email,
                                project_id, request.correct_project_code,
                                suggestion_id, email_id,
                                request.pattern_notes or f"Created from user correction"
                            ))
                            result_data["pattern_created"] = True
                            result_data["pattern_key"] = sender_email

        # Handle transcript_link type with correction
        elif suggestion_type == 'transcript_link' and request.correct_proposal_id:
            transcript_id = suggested_data.get('transcript_id')

            if transcript_id:
                # Look up proposal
                cursor.execute(
                    "SELECT project_code FROM proposals WHERE proposal_id = ?",
                    (request.correct_proposal_id,)
                )
                proposal_row = cursor.fetchone()

                if proposal_row:
                    # Update the transcript with the correct link
                    cursor.execute("""
                        UPDATE meeting_transcripts
                        SET proposal_id = ?,
                            detected_project_code = ?
                        WHERE id = ?
                    """, (request.correct_proposal_id, proposal_row['project_code'], transcript_id))

                    result_data["corrected"] = True
                    result_data["correct_link"] = {
                        "transcript_id": transcript_id,
                        "proposal_id": request.correct_proposal_id
                    }

        # Mark suggestion as rejected
        cursor.execute("""
            UPDATE ai_suggestions
            SET status = 'rejected',
                reviewed_at = datetime('now'),
                reviewed_by = 'user_correction',
                review_notes = ?,
                correction_data = ?
            WHERE suggestion_id = ?
        """, (
            request.rejection_reason,
            json.dumps(result_data) if result_data.get("corrected") else None,
            suggestion_id
        ))

        conn.commit()
        conn.close()

        return action_response(
            True,
            data=result_data,
            message="Suggestion rejected with correction" if result_data.get("corrected") else "Suggestion rejected"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/approve-with-context")
async def approve_with_context(
    suggestion_id: int,
    request: SuggestionApproveWithContextRequest
):
    """
    Approve a suggestion and optionally create patterns for future learning.

    Options:
    - create_sender_pattern: Always link emails from this sender to this project
    - create_domain_pattern: Always link emails from this domain to this project
    - contact_role: Specify the role of a new contact
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the suggestion
        cursor.execute("SELECT * FROM ai_suggestions WHERE suggestion_id = ?", (suggestion_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Suggestion not found")

        suggestion = dict(row)
        suggestion_type = suggestion.get('suggestion_type')

        # Parse suggested_data
        suggested_data = {}
        if suggestion.get('suggested_data'):
            try:
                suggested_data = json.loads(suggestion['suggested_data'])
            except (json.JSONDecodeError, TypeError):
                pass

        result_data = {
            "suggestion_id": suggestion_id,
            "patterns_created": []
        }

        # First, approve the suggestion using the existing service
        conn.close()  # Close before calling service

        # Apply any contact edits
        approve_result = ai_learning_service.approve_suggestion(
            suggestion_id,
            reviewed_by="user_with_context",
            apply_changes=True
        )

        if not approve_result.get('success'):
            raise HTTPException(status_code=400, detail=approve_result.get('message', 'Approval failed'))

        # Now create patterns if requested
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if suggestion_type == 'email_link':
            email_id = suggested_data.get('email_id')
            project_id = suggested_data.get('project_id')
            project_code = suggested_data.get('project_code') or suggestion.get('project_code')

            if email_id and project_id:
                # Get email details
                cursor.execute(
                    "SELECT sender_email FROM emails WHERE email_id = ?",
                    (email_id,)
                )
                email_row = cursor.fetchone()

                if email_row and email_row['sender_email']:
                    sender_email = email_row['sender_email'].lower().strip()
                    domain = sender_email.split('@')[-1] if '@' in sender_email else None

                    # Create sender pattern if requested
                    if request.create_sender_pattern:
                        cursor.execute("""
                            INSERT OR REPLACE INTO email_learned_patterns (
                                pattern_type, pattern_key, pattern_key_normalized,
                                target_type, target_id, target_code,
                                confidence, times_correct,
                                created_from_suggestion_id, created_from_email_id,
                                notes, created_at, updated_at
                            ) VALUES (
                                'sender_to_project', ?, ?,
                                'project', ?, ?,
                                0.9, 1,
                                ?, ?,
                                ?, datetime('now'), datetime('now')
                            )
                        """, (
                            sender_email, sender_email,
                            project_id, project_code,
                            suggestion_id, email_id,
                            request.pattern_notes or "Created from approved suggestion"
                        ))
                        result_data["patterns_created"].append({
                            "type": "sender_to_project",
                            "key": sender_email
                        })

                    # Create domain pattern if requested
                    if request.create_domain_pattern and domain:
                        cursor.execute("""
                            INSERT OR REPLACE INTO email_learned_patterns (
                                pattern_type, pattern_key, pattern_key_normalized,
                                target_type, target_id, target_code,
                                confidence, times_correct,
                                created_from_suggestion_id, created_from_email_id,
                                notes, created_at, updated_at
                            ) VALUES (
                                'domain_to_project', ?, ?,
                                'project', ?, ?,
                                0.7, 1,
                                ?, ?,
                                ?, datetime('now'), datetime('now')
                            )
                        """, (
                            f"@{domain}", domain,
                            project_id, project_code,
                            suggestion_id, email_id,
                            request.pattern_notes or "Created from approved suggestion"
                        ))
                        result_data["patterns_created"].append({
                            "type": "domain_to_project",
                            "key": f"@{domain}"
                        })

        # Handle contact role update
        if suggestion_type == 'new_contact' and request.contact_role:
            contact_id = approve_result.get('data', {}).get('contact_id')
            if contact_id:
                cursor.execute("""
                    UPDATE contacts SET role = ? WHERE contact_id = ?
                """, (request.contact_role, contact_id))
                result_data["contact_role_updated"] = True

        conn.commit()
        conn.close()

        return action_response(
            True,
            data=result_data,
            message=f"Suggestion approved. Created {len(result_data['patterns_created'])} pattern(s)."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PATTERN MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/patterns")
async def get_patterns(
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    target_code: Optional[str] = Query(None, description="Filter by project/proposal code"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all learned patterns with optional filtering"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_clauses = []
        params = []

        if pattern_type:
            where_clauses.append("pattern_type = ?")
            params.append(pattern_type)

        if target_code:
            where_clauses.append("target_code = ?")
            params.append(target_code)

        if is_active is not None:
            where_clauses.append("is_active = ?")
            params.append(1 if is_active else 0)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM email_learned_patterns WHERE {where_sql}", params)
        total = cursor.fetchone()[0]

        # Get patterns
        cursor.execute(f"""
            SELECT
                pattern_id, pattern_type, pattern_key,
                target_type, target_id, target_code, target_name,
                confidence, times_used, times_correct, times_rejected,
                is_active, notes,
                created_at, updated_at, last_used_at
            FROM email_learned_patterns
            WHERE {where_sql}
            ORDER BY times_used DESC, confidence DESC, created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset])

        patterns = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "patterns": patterns,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/stats")
async def get_pattern_stats():
    """Get pattern statistics summary"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_patterns,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_patterns,
                SUM(times_used) as total_uses,
                SUM(times_correct) as total_correct,
                SUM(times_rejected) as total_rejected,
                AVG(confidence) as avg_confidence
            FROM email_learned_patterns
        """)
        row = cursor.fetchone()
        stats = dict(row) if row else {}

        # Get breakdown by pattern type
        cursor.execute("""
            SELECT pattern_type, COUNT(*) as count, SUM(times_used) as uses
            FROM email_learned_patterns
            WHERE is_active = 1
            GROUP BY pattern_type
        """)
        by_type = {r['pattern_type']: {"count": r['count'], "uses": r['uses']} for r in cursor.fetchall()}

        # Get top performing patterns
        cursor.execute("""
            SELECT pattern_id, pattern_type, pattern_key, target_code,
                   times_used, times_correct,
                   CASE WHEN times_used > 0 THEN ROUND(times_correct * 1.0 / times_used, 2) ELSE 0 END as success_rate
            FROM email_learned_patterns
            WHERE is_active = 1 AND times_used > 0
            ORDER BY times_correct DESC
            LIMIT 10
        """)
        top_patterns = [dict(r) for r in cursor.fetchall()]

        conn.close()

        return {
            "success": True,
            "stats": stats,
            "by_type": by_type,
            "top_patterns": top_patterns
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns")
async def create_pattern(request: PatternCreateRequest):
    """Manually create a pattern"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Look up target
        if request.target_type == 'project':
            cursor.execute(
                "SELECT project_id, project_title FROM projects WHERE project_code = ?",
                (request.target_code,)
            )
        else:
            cursor.execute(
                "SELECT proposal_id as project_id, project_name as project_title FROM proposals WHERE project_code = ?",
                (request.target_code,)
            )

        target_row = cursor.fetchone()
        if not target_row:
            conn.close()
            raise HTTPException(status_code=404, detail=f"{request.target_type.title()} not found: {request.target_code}")

        target_id = target_row['project_id']
        target_name = target_row['project_title']

        # Insert the pattern
        cursor.execute("""
            INSERT INTO email_learned_patterns (
                pattern_type, pattern_key, pattern_key_normalized,
                target_type, target_id, target_code, target_name,
                confidence, is_active, notes,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0.8, 1, ?, datetime('now'), datetime('now'))
        """, (
            request.pattern_type,
            request.pattern_key,
            request.pattern_key.lower().strip(),
            request.target_type,
            target_id,
            request.target_code,
            target_name,
            request.notes
        ))

        pattern_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return action_response(
            True,
            data={"pattern_id": pattern_id},
            message="Pattern created successfully"
        )

    except HTTPException:
        raise
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="A pattern with this key and target already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/patterns/{pattern_id}")
async def update_pattern(pattern_id: int, request: PatternUpdateRequest):
    """Update an existing pattern"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check pattern exists
        cursor.execute("SELECT pattern_id FROM email_learned_patterns WHERE pattern_id = ?", (pattern_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Pattern not found")

        # Build update query
        updates = []
        params = []

        if request.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if request.is_active else 0)

        if request.notes is not None:
            updates.append("notes = ?")
            params.append(request.notes)

        if request.confidence is not None:
            updates.append("confidence = ?")
            params.append(request.confidence)

        if not updates:
            conn.close()
            return action_response(True, message="No changes to apply")

        updates.append("updated_at = datetime('now')")
        params.append(pattern_id)

        cursor.execute(f"""
            UPDATE email_learned_patterns
            SET {', '.join(updates)}
            WHERE pattern_id = ?
        """, params)

        conn.commit()
        conn.close()

        return action_response(True, message="Pattern updated successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/patterns/{pattern_id}")
async def delete_pattern(pattern_id: int):
    """Delete a pattern"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM email_learned_patterns WHERE pattern_id = ?", (pattern_id,))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Pattern not found")

        conn.commit()
        conn.close()

        return action_response(True, message="Pattern deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{pattern_id}")
async def get_pattern(pattern_id: int):
    """Get a single pattern with its usage history"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get pattern
        cursor.execute("""
            SELECT * FROM email_learned_patterns WHERE pattern_id = ?
        """, (pattern_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Pattern not found")

        pattern = dict(row)

        # Get recent usage
        cursor.execute("""
            SELECT log_id, suggestion_id, email_id, action, match_score, created_at
            FROM email_pattern_usage_log
            WHERE pattern_id = ?
            ORDER BY created_at DESC
            LIMIT 20
        """, (pattern_id,))
        usage_history = [dict(r) for r in cursor.fetchall()]

        conn.close()

        return {
            "success": True,
            "pattern": pattern,
            "usage_history": usage_history
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENHANCED REVIEW UI ENDPOINTS
# ============================================================================

@router.get("/suggestions/{suggestion_id}/full-context")
async def get_suggestion_full_context(suggestion_id: int):
    """
    Get full context for reviewing a suggestion, including:
    - The suggestion itself
    - Source content (email/transcript)
    - AI analysis with detected entities
    - Preview of database changes
    - Any existing user feedback
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the suggestion
        cursor.execute("SELECT * FROM ai_suggestions WHERE suggestion_id = ?", (suggestion_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Suggestion not found")

        suggestion = dict(row)

        # Parse suggested_data
        suggested_data = {}
        if suggestion.get('suggested_data'):
            try:
                suggested_data = json.loads(suggestion['suggested_data'])
            except (json.JSONDecodeError, TypeError):
                pass

        # Get source content
        source_content = None
        source_type = suggestion.get('source_type')
        source_id = suggestion.get('source_id')

        if source_type == 'email' and source_id:
            cursor.execute("""
                SELECT email_id, subject, body_full, sender_email,
                       recipient_emails, date, folder
                FROM emails WHERE email_id = ?
            """, (source_id,))
            email_row = cursor.fetchone()
            if email_row:
                email = dict(email_row)
                source_content = {
                    "type": "email",
                    "id": email.get('email_id'),
                    "subject": email.get('subject'),
                    "sender": email.get('sender_email'),
                    "recipient": email.get('recipient_emails'),
                    "date": email.get('date'),
                    "body": email.get('body_full') or ""
                }

        elif source_type == 'transcript' and source_id:
            cursor.execute("""
                SELECT id, audio_filename, meeting_title, meeting_date,
                       transcript, summary
                FROM meeting_transcripts WHERE id = ?
            """, (source_id,))
            transcript_row = cursor.fetchone()
            if transcript_row:
                transcript = dict(transcript_row)
                source_content = {
                    "type": "transcript",
                    "id": transcript.get('id'),
                    "subject": transcript.get('meeting_title'),
                    "date": transcript.get('meeting_date'),
                    "body": transcript.get('transcript') or ""
                }

        # Build AI analysis
        ai_analysis = {
            "detected_entities": {
                "projects": [],
                "fees": [],
                "contacts": [],
                "dates": [],
                "keywords": []
            },
            "suggested_actions": [],
            "pattern_to_learn": None,
            "overall_confidence": suggestion.get('confidence_score', 0)
        }

        # Extract entities from suggested_data
        if suggested_data:
            # Project codes
            if suggested_data.get('project_code'):
                ai_analysis["detected_entities"]["projects"].append(suggested_data['project_code'])

            # Contacts
            if suggested_data.get('name') or suggested_data.get('email'):
                ai_analysis["detected_entities"]["contacts"].append({
                    "name": suggested_data.get('name', ''),
                    "email": suggested_data.get('email', '')
                })

            # Keywords from description
            if suggestion.get('description'):
                keywords = [w for w in suggestion['description'].split() if len(w) > 4][:5]
                ai_analysis["detected_entities"]["keywords"] = keywords

        # Build suggested actions based on type
        suggestion_type = suggestion.get('suggestion_type')

        if suggestion_type == 'email_link':
            ai_analysis["suggested_actions"].append({
                "id": "link_email",
                "type": "link_email",
                "description": f"Link email to {suggested_data.get('project_code', 'project')}",
                "enabled_by_default": True,
                "data": {
                    "email_id": suggested_data.get('email_id'),
                    "project_id": suggested_data.get('project_id'),
                    "project_code": suggested_data.get('project_code')
                },
                "database_change": f"INSERT INTO email_project_links (email_id, project_id)"
            })

            # Suggest pattern learning if sender is known
            if source_content and source_content.get('sender'):
                sender = source_content['sender']
                ai_analysis["pattern_to_learn"] = {
                    "type": "sender_to_project",
                    "pattern_key": sender,
                    "target": suggested_data.get('project_code', ''),
                    "confidence_boost": 0.1
                }

        elif suggestion_type == 'new_contact':
            ai_analysis["suggested_actions"].append({
                "id": "add_contact",
                "type": "link_contact",
                "description": f"Add contact: {suggested_data.get('name', 'Unknown')}",
                "enabled_by_default": True,
                "data": suggested_data,
                "database_change": f"INSERT INTO contacts (name, email)"
            })

        elif suggestion_type == 'project_alias':
            ai_analysis["suggested_actions"].append({
                "id": "add_alias",
                "type": "learn_pattern",
                "description": f"Add alias for {suggested_data.get('project_code', 'project')}",
                "enabled_by_default": True,
                "data": suggested_data,
                "database_change": f"INSERT INTO project_aliases (alias, project_code)"
            })

        # Get preview using handler
        preview = None
        handler = HandlerRegistry.get_handler(suggestion_type, conn)
        if handler:
            preview_result = handler.preview(suggestion, suggested_data)
            preview = {
                "is_actionable": handler.is_actionable,
                "action": preview_result.action,
                "table": preview_result.table,
                "summary": preview_result.summary,
                "changes": preview_result.changes
            }

        # Get existing feedback
        cursor.execute("""
            SELECT context_notes, tags, contact_role, priority
            FROM suggestion_user_feedback
            WHERE suggestion_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (suggestion_id,))
        feedback_row = cursor.fetchone()
        existing_feedback = None
        if feedback_row:
            feedback = dict(feedback_row)
            existing_feedback = {
                "notes": feedback.get('context_notes') or "",
                "tags": json.loads(feedback.get('tags') or "[]"),
                "contact_role": feedback.get('contact_role'),
                "priority": feedback.get('priority')
            }

        conn.close()

        return {
            "success": True,
            "suggestion": suggestion,
            "source_content": source_content,
            "ai_analysis": ai_analysis,
            "preview": preview,
            "existing_feedback": existing_feedback
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestion-tags")
async def get_suggestion_tags():
    """Get available tags for suggestions (for autocomplete)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT tag_id, tag_name, tag_category, usage_count
            FROM suggestion_tags
            ORDER BY usage_count DESC, tag_name
        """)

        tags = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "success": True,
            "tags": tags
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/save-feedback")
async def save_suggestion_feedback(
    suggestion_id: int,
    context_notes: Optional[str] = None,
    tags: Optional[str] = None,  # JSON array string
    contact_role: Optional[str] = None,
    priority: Optional[str] = None
):
    """Save user feedback for a suggestion without approving/rejecting"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Verify suggestion exists
        cursor.execute("SELECT suggestion_id FROM ai_suggestions WHERE suggestion_id = ?", (suggestion_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Suggestion not found")

        # Upsert feedback
        cursor.execute("""
            INSERT INTO suggestion_user_feedback (
                suggestion_id, context_notes, tags, contact_role, priority, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            ON CONFLICT(suggestion_id) DO UPDATE SET
                context_notes = excluded.context_notes,
                tags = excluded.tags,
                contact_role = excluded.contact_role,
                priority = excluded.priority,
                updated_at = datetime('now')
        """, (suggestion_id, context_notes, tags, contact_role, priority))

        # Update tag usage counts
        if tags:
            try:
                tag_list = json.loads(tags)
                for tag in tag_list:
                    cursor.execute("""
                        INSERT INTO suggestion_tags (tag_name, tag_category, usage_count)
                        VALUES (?, 'user', 1)
                        ON CONFLICT(tag_name) DO UPDATE SET
                            usage_count = usage_count + 1
                    """, (tag.lower().strip(),))
            except json.JSONDecodeError:
                pass

        conn.commit()
        conn.close()

        return action_response(True, message="Feedback saved")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
