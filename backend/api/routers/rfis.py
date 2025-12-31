"""
RFI Router - Request for Information management endpoints

Endpoints:
    GET /api/rfis - List RFIs with filtering
    POST /api/rfis - Create new RFI
    GET /api/rfis/overdue - Get overdue RFIs
    GET /api/rfis/stats - RFI statistics
    GET /api/rfis/{rfi_id} - Get RFI detail
    POST /api/rfis/{rfi_id}/respond - Mark RFI responded
    POST /api/rfis/{rfi_id}/close - Close RFI
    POST /api/rfis/{rfi_id}/assign - Assign RFI to PM
    GET /api/rfis/by-project/{project_code} - Get RFIs by project
    PATCH /api/rfis/{rfi_id} - Update RFI
    DELETE /api/rfis/{rfi_id} - Delete RFI
    POST /api/rfis/scan - Scan emails for RFIs
    POST /api/rfis/extract-from-email/{email_id} - Extract RFI from email
    POST /api/rfis/process-batch - Batch process RFIs
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import date
import sqlite3

from api.dependencies import DB_PATH
from api.services import rfi_service
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["rfis"])


# ============================================================================
# FIELD MAPPING HELPER
# ============================================================================

def map_rfi_for_frontend(rfi: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map backend RFI fields to frontend expected format.

    Backend -> Frontend mapping:
    - rfi_id -> id
    - date_sent -> created_at
    - date_due -> due_date
    - sender_name -> requested_by
    - date_responded -> responded_at
    - project_code -> project_code (unchanged)
    """
    return {
        "id": rfi.get("rfi_id"),
        "rfi_number": rfi.get("rfi_number"),
        "subject": rfi.get("subject", ""),
        "description": rfi.get("description"),
        "project_code": rfi.get("project_code"),
        "project_name": rfi.get("project_title") or rfi.get("project_name"),
        "status": rfi.get("status", "open"),
        "priority": rfi.get("priority"),
        "requested_by": rfi.get("sender_name") or rfi.get("sender_email"),
        "assigned_to": rfi.get("assigned_to"),
        "created_at": rfi.get("date_sent") or rfi.get("created_at"),
        "due_date": rfi.get("date_due"),
        "responded_at": rfi.get("date_responded"),
        "closed_at": rfi.get("closed_at"),  # If exists
        "response": rfi.get("response"),
        "days_open": rfi.get("days_open"),
        "is_overdue": rfi.get("is_overdue", False),
        # Keep original fields for backward compat
        "rfi_id": rfi.get("rfi_id"),
        "project_id": rfi.get("project_id"),
        "extraction_confidence": rfi.get("extraction_confidence"),
    }


def map_rfis_for_frontend(rfis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Map a list of RFIs for frontend compatibility."""
    return [map_rfi_for_frontend(rfi) for rfi in rfis]


# ============================================================================
# REQUEST MODELS
# ============================================================================

class RFIAssignRequest(BaseModel):
    """Request to assign PM to RFI"""
    pm_id: int = Field(..., description="Team member ID to assign")


class RFIUpdateRequest(BaseModel):
    """Request body for updating RFI fields"""
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    date_due: Optional[str] = None
    assigned_pm_id: Optional[int] = None
    assigned_to: Optional[str] = None


# ============================================================================
# RFI LIST ENDPOINTS
# ============================================================================

@router.get("/rfis")
async def list_rfis(
    proposal_id: Optional[int] = None,
    project_code: Optional[str] = Query(None, description="Filter by project code"),
    status: Optional[str] = Query(None, description="Filter by status: open, answered, overdue"),
    overdue_only: bool = Query(False, description="Show only overdue RFIs"),
    limit: int = Query(50, description="Maximum records to return")
):
    """List RFIs with optional filtering"""
    try:
        if proposal_id and not project_code and not overdue_only:
            rfis = rfi_service.get_rfis_by_proposal(proposal_id)
            mapped = map_rfis_for_frontend(rfis)
            return {"success": True, "total": len(mapped), "rfis": mapped}

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM rfis WHERE 1=1"
        params = []

        if project_code:
            query += " AND (project_code = ? OR project_code LIKE ?)"
            params.extend([project_code, f"%{project_code}%"])

        if overdue_only:
            today = date.today().isoformat()
            query += " AND status = 'open' AND date_due < ?"
            params.append(today)
        elif status:
            if status == 'overdue':
                today = date.today().isoformat()
                query += " AND status = 'open' AND date_due < ?"
                params.append(today)
            elif status == 'pending':
                # Map 'pending' to 'open' for frontend compatibility
                query += " AND status = 'open'"
            else:
                query += " AND status = ?"
                params.append(status)

        query += " ORDER BY date_due ASC, priority DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        rfis = [dict(row) for row in rows]
        conn.close()

        today = date.today().isoformat()
        for rfi in rfis:
            if rfi.get('status') == 'open' and rfi.get('date_due'):
                rfi['is_overdue'] = rfi['date_due'] < today
            else:
                rfi['is_overdue'] = False

        # Map fields for frontend and return with 'rfis' key (frontend expectation)
        mapped_rfis = map_rfis_for_frontend(rfis)
        return {"success": True, "total": len(mapped_rfis), "rfis": mapped_rfis}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/rfis/overdue")
async def get_overdue_rfis():
    """Get all RFIs that are past their 48-hour SLA"""
    try:
        overdue = rfi_service.get_overdue_rfis()
        return list_response(overdue, len(overdue))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/rfis/stats")
async def get_rfi_stats():
    """Get RFI statistics for dashboard"""
    try:
        stats = rfi_service.get_rfi_stats_for_dashboard()
        summary = stats.get('summary', {})

        # Format stats for frontend - frontend expects 'open' not 'pending'
        formatted_stats = {
            'total': summary.get('total_rfis', 0),
            'open': summary.get('open', 0),  # Frontend expects 'open'
            'responded': summary.get('responded', 0),
            'closed': summary.get('closed', 0),
            'overdue': summary.get('overdue', 0),
            'avg_response_days': summary.get('avg_days_open'),
        }

        # Return with nested 'stats' object as frontend API expects
        return {
            "success": True,
            "stats": formatted_stats,
            # Backward compat - also flatten at root level
            **formatted_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/rfis/by-project/{project_code}")
async def get_rfis_by_project(project_code: str):
    """Get all RFIs for a specific project"""
    try:
        rfis = rfi_service.get_rfis_by_project(project_code)
        summary = rfi_service.get_rfi_summary(project_code)
        response = list_response(rfis, len(rfis))
        response["project_code"] = project_code  # Backward compat
        response["summary"] = summary  # Backward compat
        response["rfis"] = rfis  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# RFI CRUD
# ============================================================================

@router.post("/rfis")
async def create_rfi(
    proposal_id: int,
    question: str,
    asked_by: str,
    asked_date: str,
    priority: str = "normal",
    category: Optional[str] = None
):
    """Create a new RFI"""
    try:
        rfi_id = rfi_service.create_rfi({
            "proposal_id": proposal_id,
            "question": question,
            "asked_by": asked_by,
            "asked_date": asked_date,
            "priority": priority,
            "category": category
        })
        return action_response(True, data={"rfi_id": rfi_id}, message="RFI created")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/rfis/{rfi_id}")
async def get_rfi_detail(rfi_id: int):
    """Get detailed information about a specific RFI"""
    try:
        rfi = rfi_service.get_rfi_by_id(rfi_id)
        if not rfi:
            raise HTTPException(status_code=404, detail=f"RFI {rfi_id} not found")
        return item_response(rfi)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.patch("/rfis/{rfi_id}")
async def update_rfi(rfi_id: int, request: RFIUpdateRequest):
    """Update RFI fields"""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        success = rfi_service.update_rfi(rfi_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail=f"RFI {rfi_id} not found")

        return action_response(
            True,
            data={"rfi_id": rfi_id, "updated_fields": list(update_data.keys())},
            message="RFI updated"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/rfis/{rfi_id}")
async def delete_rfi(rfi_id: int):
    """Delete an RFI"""
    try:
        success = rfi_service.delete_rfi(rfi_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"RFI {rfi_id} not found")
        return action_response(True, message=f"RFI {rfi_id} deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# RFI ACTIONS
# ============================================================================

@router.post("/rfis/{rfi_id}/respond")
async def mark_rfi_responded(rfi_id: int):
    """Mark an RFI as responded"""
    try:
        success = rfi_service.mark_responded(rfi_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"RFI {rfi_id} not found")
        return action_response(True, data={"rfi_id": rfi_id}, message="RFI marked as responded")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/rfis/{rfi_id}/close")
async def close_rfi(rfi_id: int):
    """Mark an RFI as closed"""
    try:
        success = rfi_service.close_rfi(rfi_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"RFI {rfi_id} not found")
        return action_response(True, data={"rfi_id": rfi_id}, message="RFI closed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/rfis/{rfi_id}/assign")
async def assign_rfi_to_pm(rfi_id: int, request: RFIAssignRequest):
    """Assign an RFI to a specific PM"""
    try:
        success = rfi_service.update_rfi(rfi_id, {"assigned_pm_id": request.pm_id})
        if not success:
            raise HTTPException(status_code=404, detail=f"RFI {rfi_id} not found")
        return action_response(True, data={"rfi_id": rfi_id, "pm_id": request.pm_id}, message=f"RFI assigned to PM {request.pm_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# RFI DETECTION / EXTRACTION
# ============================================================================

@router.post("/rfis/scan")
async def scan_for_rfis(
    limit: int = Query(100, description="Max emails to scan"),
    min_confidence: float = Query(0.6, description="Minimum confidence threshold")
):
    """Scan unprocessed emails for potential RFIs"""
    try:
        from scripts.core.rfi_detector import RFIDetector

        detector = RFIDetector(DB_PATH)
        results = detector.scan_unprocessed_emails(limit=limit)
        filtered = [r for r in results if r['confidence'] >= min_confidence]

        response = list_response(filtered, len(filtered))
        response["scanned"] = limit  # Backward compat
        response["potential_rfis"] = len(filtered)  # Backward compat
        response["candidates"] = filtered  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/rfis/extract-from-email/{email_id}")
async def extract_rfi_from_email(
    email_id: int,
    project_code: Optional[str] = Query(None, description="Override project code")
):
    """Create RFI from a specific email"""
    try:
        from scripts.core.rfi_detector import RFIDetector

        detector = RFIDetector(DB_PATH)
        result = detector.detect_and_create_rfi(
            email_id=email_id,
            project_code=project_code
        )

        if not result['is_rfi']:
            return action_response(
                False,
                data={"reason": result.get('reason'), "confidence": result.get('confidence', 0)},
                message="Email not detected as RFI"
            )

        if result.get('rfi_id'):
            return action_response(
                True,
                data={
                    "rfi_id": result['rfi_id'],
                    "rfi_number": result.get('rfi_number'),
                    "project_code": result.get('project_code'),
                    "date_due": result.get('date_due'),
                    "confidence": result['confidence']
                },
                message=result['message']
            )
        else:
            return action_response(
                False,
                data={"reason": result.get('reason')},
                message=result.get('message', 'Could not create RFI')
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/rfis/process-batch")
async def process_rfi_batch(
    min_confidence: float = Query(0.75, description="Minimum confidence to auto-create")
):
    """Auto-process emails and create RFIs for high-confidence matches"""
    try:
        from scripts.core.rfi_detector import RFIDetector

        detector = RFIDetector(DB_PATH)
        candidates = detector.scan_unprocessed_emails(limit=200)

        created = []
        skipped = []

        for candidate in candidates:
            if candidate['confidence'] >= min_confidence:
                result = detector.detect_and_create_rfi(
                    email_id=candidate['email_id'],
                    project_code=candidate.get('project_code')
                )
                if result.get('rfi_id'):
                    created.append({
                        'rfi_id': result['rfi_id'],
                        'rfi_number': result.get('rfi_number'),
                        'project_code': result.get('project_code'),
                        'subject': candidate.get('subject', '')[:80]
                    })
                else:
                    skipped.append({
                        'email_id': candidate['email_id'],
                        'reason': result.get('reason', 'unknown')
                    })

        return action_response(
            True,
            data={
                "scanned": len(candidates),
                "created": len(created),
                "skipped": len(skipped),
                "rfis": created,
                "skip_details": skipped[:10]
            },
            message=f"Processed {len(candidates)} candidates, created {len(created)} RFIs"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")
