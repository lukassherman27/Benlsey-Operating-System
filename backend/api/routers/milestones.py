"""
Milestones Router - Project milestone management

Endpoints:
    GET /api/milestones - List milestones
    GET /api/milestones/overdue - Get overdue milestones
    GET /api/milestones/upcoming - Get upcoming milestones
    GET /api/milestones/{milestone_id} - Get milestone by ID
    GET /api/milestones/by-proposal/{proposal_id} - Get proposal milestones
    GET /api/milestones/by-proposal/{proposal_id}/timeline - Get timeline
    POST /api/milestones - Create milestone
    PATCH /api/milestones/{milestone_id} - Update milestone
    PATCH /api/milestones/{milestone_id}/status - Update status
    DELETE /api/milestones/{milestone_id} - Delete milestone
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, Field

from api.services import milestone_service
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["milestones"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateMilestoneRequest(BaseModel):
    """Request to create a milestone"""
    proposal_id: int
    milestone_name: str
    milestone_type: Optional[str] = None
    target_date: Optional[str] = None
    status: str = "pending"
    notes: Optional[str] = None


class UpdateMilestoneRequest(BaseModel):
    """Request to update milestone"""
    milestone_name: Optional[str] = None
    milestone_type: Optional[str] = None
    target_date: Optional[str] = None
    actual_date: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class UpdateMilestoneStatusRequest(BaseModel):
    """Request to update milestone status"""
    status: str = Field(..., description="New status")
    actual_date: Optional[str] = None


# ============================================================================
# LIST ENDPOINTS
# ============================================================================

@router.get("/milestones")
async def list_milestones(
    proposal_id: Optional[int] = Query(None, description="Filter by proposal"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500)
):
    """List milestones with optional filtering"""
    try:
        if proposal_id:
            milestones = milestone_service.get_milestones_by_proposal(proposal_id)
        else:
            # Get upcoming as default view
            milestones = milestone_service.get_upcoming_milestones(days_ahead=90)
        return list_response(milestones, len(milestones))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/milestones/overdue")
async def get_overdue_milestones():
    """Get all overdue milestones"""
    try:
        overdue = milestone_service.get_overdue_milestones()
        return list_response(overdue, len(overdue))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/milestones/upcoming")
async def get_upcoming_milestones(days: int = Query(30, ge=1, le=180)):
    """Get milestones due in the next N days"""
    try:
        upcoming = milestone_service.get_upcoming_milestones(days_ahead=days)
        return list_response(upcoming, len(upcoming))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/milestones/{milestone_id}")
async def get_milestone(milestone_id: int):
    """Get a specific milestone"""
    try:
        milestone = milestone_service.get_milestone_by_id(milestone_id)
        if not milestone:
            raise HTTPException(status_code=404, detail=f"Milestone {milestone_id} not found")
        return item_response(milestone)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/milestones/by-proposal/{proposal_id}")
async def get_milestones_by_proposal(proposal_id: int):
    """Get all milestones for a proposal"""
    try:
        milestones = milestone_service.get_milestones_by_proposal(proposal_id)
        response = list_response(milestones, len(milestones))
        response["proposal_id"] = proposal_id  # Backward compat
        response["milestones"] = milestones  # Backward compat
        response["count"] = len(milestones)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/milestones/by-proposal/{proposal_id}/timeline")
async def get_milestone_timeline(proposal_id: int):
    """Get timeline view of milestones for a proposal"""
    try:
        timeline = milestone_service.get_timeline_data(proposal_id)
        return item_response(timeline)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CRUD
# ============================================================================

@router.post("/milestones")
async def create_milestone(request: CreateMilestoneRequest):
    """Create a new milestone"""
    try:
        milestone_id = milestone_service.create_milestone(request.dict())
        return action_response(True, data={"milestone_id": milestone_id}, message="Milestone created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/milestones/{milestone_id}")
async def update_milestone(milestone_id: int, request: UpdateMilestoneRequest):
    """Update a milestone"""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        success = milestone_service.update_milestone(milestone_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail=f"Milestone {milestone_id} not found")
        return action_response(True, message="Milestone updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/milestones/{milestone_id}/status")
async def update_milestone_status(milestone_id: int, request: UpdateMilestoneStatusRequest):
    """Update milestone status"""
    try:
        success = milestone_service.update_milestone_status(
            milestone_id=milestone_id,
            status=request.status,
            actual_date=request.actual_date
        )
        if not success:
            raise HTTPException(status_code=404, detail=f"Milestone {milestone_id} not found")
        return action_response(True, message="Status updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/milestones/{milestone_id}")
async def delete_milestone(milestone_id: int):
    """Delete a milestone"""
    try:
        success = milestone_service.delete_milestone(milestone_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Milestone {milestone_id} not found")
        return action_response(True, message="Milestone deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
