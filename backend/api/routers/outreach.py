"""
Outreach Router - Client outreach and contact history

Endpoints:
    GET /api/outreach/needing-followup - Contacts needing followup
    GET /api/outreach/upcoming - Upcoming followups
    GET /api/outreach/by-proposal/{proposal_id} - Proposal outreach history
    GET /api/outreach/by-proposal/{proposal_id}/timeline - Contact timeline
    GET /api/outreach/by-proposal/{proposal_id}/summary - Outreach summary
    GET /api/outreach/by-proposal/{proposal_id}/last-contact - Last contact
    GET /api/outreach/{outreach_id} - Get outreach by ID
    GET /api/outreach/search - Search outreach
    POST /api/outreach - Create outreach record
    PATCH /api/outreach/{outreach_id} - Update outreach
    DELETE /api/outreach/{outreach_id} - Delete outreach
    POST /api/outreach/bulk-from-emails - Bulk create from emails
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field

from api.services import outreach_service
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["outreach"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateOutreachRequest(BaseModel):
    """Request to create outreach record"""
    proposal_id: int
    contact_type: str = Field(..., description="Type: email, call, meeting, message")
    contact_date: str
    contact_by: Optional[str] = None
    contact_with: Optional[str] = None
    subject: Optional[str] = None
    notes: Optional[str] = None
    followup_needed: bool = False
    followup_date: Optional[str] = None


class UpdateOutreachRequest(BaseModel):
    """Request to update outreach"""
    contact_type: Optional[str] = None
    contact_date: Optional[str] = None
    contact_by: Optional[str] = None
    contact_with: Optional[str] = None
    subject: Optional[str] = None
    notes: Optional[str] = None
    followup_needed: Optional[bool] = None
    followup_date: Optional[str] = None
    followup_completed: Optional[bool] = None


class BulkFromEmailsRequest(BaseModel):
    """Request to bulk create outreach from emails"""
    proposal_id: int
    email_ids: List[int]


# ============================================================================
# FOLLOWUP ENDPOINTS
# ============================================================================

@router.get("/outreach/needing-followup")
async def get_outreach_needing_followup():
    """Get outreach records that need followup"""
    try:
        records = outreach_service.get_outreach_needing_followup()
        return list_response(records, len(records))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outreach/upcoming")
async def get_upcoming_followups(days: int = Query(7, ge=1, le=30)):
    """Get followups scheduled in the next N days"""
    try:
        records = outreach_service.get_upcoming_followups(days_ahead=days)
        return list_response(records, len(records))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROPOSAL-SPECIFIC
# ============================================================================

@router.get("/outreach/by-proposal/{proposal_id}")
async def get_outreach_by_proposal(proposal_id: int):
    """Get all outreach for a proposal"""
    try:
        records = outreach_service.get_outreach_by_proposal(proposal_id)
        response = list_response(records, len(records))
        response["proposal_id"] = proposal_id  # Backward compat
        response["outreach"] = records  # Backward compat
        response["count"] = len(records)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outreach/by-proposal/{proposal_id}/timeline")
async def get_contact_history_timeline(proposal_id: int):
    """Get contact history timeline for a proposal"""
    try:
        timeline = outreach_service.get_contact_history_timeline(proposal_id)
        response = list_response(timeline, len(timeline))
        response["proposal_id"] = proposal_id  # Backward compat
        response["timeline"] = timeline  # Backward compat
        response["count"] = len(timeline)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outreach/by-proposal/{proposal_id}/summary")
async def get_outreach_summary(proposal_id: int):
    """Get outreach summary for a proposal"""
    try:
        summary = outreach_service.get_outreach_summary(proposal_id)
        return item_response(summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outreach/by-proposal/{proposal_id}/last-contact")
async def get_last_contact(proposal_id: int):
    """Get most recent contact for a proposal"""
    try:
        contact = outreach_service.get_last_contact(proposal_id)
        if not contact:
            return {"message": "No contact history found", "proposal_id": proposal_id}
        return item_response(contact)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outreach/by-proposal/{proposal_id}/by-type/{contact_type}")
async def get_outreach_by_type(proposal_id: int, contact_type: str):
    """Get outreach by contact type for a proposal"""
    try:
        records = outreach_service.get_outreach_by_contact_type(proposal_id, contact_type)
        response = list_response(records, len(records))
        response["proposal_id"] = proposal_id  # Backward compat
        response["contact_type"] = contact_type  # Backward compat
        response["outreach"] = records  # Backward compat
        response["count"] = len(records)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SEARCH
# ============================================================================

@router.get("/outreach/search")
async def search_outreach(
    q: str = Query(..., description="Search term"),
    proposal_id: Optional[int] = Query(None, description="Filter by proposal")
):
    """Search outreach records"""
    try:
        results = outreach_service.search_outreach(q, proposal_id=proposal_id)
        response = list_response(results, len(results))
        response["results"] = results  # Backward compat
        response["query"] = q  # Backward compat
        response["count"] = len(results)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CRUD
# ============================================================================

@router.get("/outreach/{outreach_id}")
async def get_outreach(outreach_id: int):
    """Get a specific outreach record"""
    try:
        record = outreach_service.get_outreach_by_id(outreach_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Outreach {outreach_id} not found")
        return item_response(record)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outreach")
async def create_outreach(request: CreateOutreachRequest):
    """Create a new outreach record"""
    try:
        outreach_id = outreach_service.create_outreach(request.dict())
        return action_response(True, data={"outreach_id": outreach_id}, message="Outreach created")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/outreach/{outreach_id}")
async def update_outreach(outreach_id: int, request: UpdateOutreachRequest):
    """Update an outreach record"""
    try:
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        success = outreach_service.update_outreach(outreach_id, update_data)
        if not success:
            raise HTTPException(status_code=404, detail=f"Outreach {outreach_id} not found")
        return action_response(True, message="Outreach updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/outreach/{outreach_id}")
async def delete_outreach(outreach_id: int):
    """Delete an outreach record"""
    try:
        success = outreach_service.delete_outreach(outreach_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Outreach {outreach_id} not found")
        return action_response(True, message="Outreach deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outreach/bulk-from-emails")
async def bulk_create_from_emails(request: BulkFromEmailsRequest):
    """Bulk create outreach records from emails"""
    try:
        count = outreach_service.bulk_create_from_emails(
            proposal_id=request.proposal_id,
            email_ids=request.email_ids
        )
        return action_response(True, data={"created": count}, message=f"Created {count} outreach records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
