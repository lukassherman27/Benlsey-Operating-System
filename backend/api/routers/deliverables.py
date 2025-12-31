"""
Deliverables Router - Project deliverables and milestone tracking

Endpoints:
    GET /api/deliverables - List all deliverables
    GET /api/deliverables/overdue - Get overdue deliverables
    GET /api/deliverables/upcoming - Get upcoming deliverables
    GET /api/deliverables/by-project/{project_code} - Get project deliverables
    GET /api/deliverables/alerts - Get deliverable alerts
    GET /api/deliverables/pm-workload - Get PM workload summary
    GET /api/deliverables/pm-list - Get list of PMs
    POST /api/deliverables - Create deliverable
    PATCH /api/deliverables/{deliverable_id}/status - Update status
    GET /api/deliverables/project/{project_code}/phase-status - Get phase status
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field

from api.services import deliverables_service
from api.helpers import list_response, item_response, action_response

router = APIRouter(prefix="/api", tags=["deliverables"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateDeliverableRequest(BaseModel):
    """Request to create a deliverable"""
    project_code: str
    name: str  # Use 'name' to match table schema
    deliverable_name: Optional[str] = None  # Alias for backward compat
    description: Optional[str] = None
    deliverable_type: Optional[str] = None  # 'drawing', 'presentation', 'document', etc.
    phase: Optional[str] = None
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    owner_staff_id: Optional[int] = None
    assigned_pm: Optional[str] = None
    status: str = "pending"
    priority: str = "normal"
    notes: Optional[str] = None
    attachments: Optional[List[dict]] = None


class UpdateDeliverableRequest(BaseModel):
    """Request to update a deliverable"""
    name: Optional[str] = None
    description: Optional[str] = None
    deliverable_type: Optional[str] = None
    phase: Optional[str] = None
    due_date: Optional[str] = None
    start_date: Optional[str] = None
    actual_completion_date: Optional[str] = None
    owner_staff_id: Optional[int] = None
    assigned_pm: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    internal_notes: Optional[str] = None
    client_feedback: Optional[str] = None
    attachments: Optional[List[dict]] = None


class UpdateDeliverableStatusRequest(BaseModel):
    """Request to update deliverable status"""
    status: str = Field(..., description="New status: pending, in_progress, completed, delayed")
    completion_date: Optional[str] = None
    notes: Optional[str] = None


# ============================================================================
# LIST ENDPOINTS
# ============================================================================

@router.get("/deliverables")
async def get_all_deliverables(
    project_code: Optional[str] = Query(None, description="Filter by project code"),
    status: Optional[str] = Query(None, description="Filter by status"),
    pm: Optional[str] = Query(None, description="Filter by assigned PM"),
    assigned_pm: Optional[str] = Query(None, description="Filter by assigned PM (alias)"),
    phase: Optional[str] = Query(None, description="Filter by phase")
):
    """Get all deliverables with optional filtering"""
    try:
        # Support both 'pm' and 'assigned_pm' parameters
        pm_filter = assigned_pm or pm
        deliverables = deliverables_service.get_all_deliverables(
            project_code=project_code,
            status=status,
            assigned_pm=pm_filter,
            phase=phase
        )
        response = list_response(deliverables, len(deliverables))
        response["deliverables"] = deliverables  # Backward compat
        response["count"] = len(deliverables)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/deliverables/overdue")
async def get_overdue_deliverables():
    """Get all overdue deliverables"""
    try:
        overdue = deliverables_service.get_overdue_deliverables()
        return list_response(overdue, len(overdue))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/deliverables/upcoming")
async def get_upcoming_deliverables(days: int = Query(14, ge=1, le=90)):
    """Get deliverables due in the next N days"""
    try:
        upcoming = deliverables_service.get_upcoming_deliverables(days_ahead=days)
        return list_response(upcoming, len(upcoming))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/deliverables/alerts")
async def get_deliverable_alerts():
    """Get deliverable alerts (overdue, at-risk)"""
    try:
        alerts = deliverables_service.get_alerts()
        response = list_response(alerts, len(alerts))
        response["alerts"] = alerts  # Backward compat
        response["count"] = len(alerts)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/deliverables/by-project/{project_code}")
async def get_deliverables_by_project(project_code: str):
    """Get all deliverables for a specific project"""
    try:
        deliverables = deliverables_service.get_all_deliverables(project_code=project_code)
        phase_status = deliverables_service.get_project_phase_status(project_code)
        response = list_response(deliverables, len(deliverables))
        response["project_code"] = project_code  # Backward compat
        response["deliverables"] = deliverables  # Backward compat
        response["count"] = len(deliverables)  # Backward compat
        response["phase_status"] = phase_status  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# PM WORKLOAD
# ============================================================================

@router.get("/deliverables/pm-workload")
async def get_pm_workload(pm: Optional[str] = Query(None, description="Filter by PM name")):
    """Get PM workload summary"""
    try:
        workload = deliverables_service.get_pm_workload(pm_name=pm)
        response = list_response(workload, len(workload))
        response["workload"] = workload  # Backward compat
        response["count"] = len(workload)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/deliverables/pm-list")
async def get_pm_list():
    """Get list of all PMs"""
    try:
        pms = deliverables_service.get_pm_list()
        response = list_response(pms, len(pms))
        response["pms"] = pms  # Backward compat
        response["count"] = len(pms)  # Backward compat
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# CRUD
# ============================================================================

@router.post("/deliverables")
async def create_deliverable(request: CreateDeliverableRequest):
    """Create a new deliverable"""
    try:
        deliverable_id = deliverables_service.create_deliverable(
            project_code=request.project_code,
            deliverable_name=request.deliverable_name,
            phase=request.phase,
            due_date=request.due_date,
            assigned_pm=request.assigned_pm,
            status=request.status,
            priority=request.priority,
            notes=request.notes
        )
        return action_response(True, data={"deliverable_id": deliverable_id}, message="Deliverable created")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.patch("/deliverables/{deliverable_id}/status")
async def update_deliverable_status(deliverable_id: int, request: UpdateDeliverableStatusRequest):
    """Update deliverable status"""
    try:
        success = deliverables_service.update_deliverable_status(
            deliverable_id=deliverable_id,
            status=request.status,
            completion_date=request.completion_date,
            notes=request.notes
        )
        if not success:
            raise HTTPException(status_code=404, detail=f"Deliverable {deliverable_id} not found")
        return action_response(True, message="Status updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/deliverables/{deliverable_id}")
async def get_deliverable(deliverable_id: int):
    """Get a single deliverable by ID"""
    try:
        deliverable = deliverables_service.get_deliverable_by_id(deliverable_id)
        if not deliverable:
            raise HTTPException(status_code=404, detail=f"Deliverable {deliverable_id} not found")
        return item_response(deliverable)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.patch("/deliverables/{deliverable_id}")
async def update_deliverable(deliverable_id: int, request: UpdateDeliverableRequest):
    """Update a deliverable"""
    try:
        updates = request.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        success = deliverables_service.update_deliverable(deliverable_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail=f"Deliverable {deliverable_id} not found")
        return action_response(True, message="Deliverable updated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.delete("/deliverables/{deliverable_id}")
async def delete_deliverable(deliverable_id: int):
    """Delete a deliverable"""
    try:
        success = deliverables_service.delete_deliverable(deliverable_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Deliverable {deliverable_id} not found")
        return action_response(True, message="Deliverable deleted")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


# ============================================================================
# PROJECT PHASE STATUS
# ============================================================================

@router.get("/deliverables/project/{project_code}/phase-status")
async def get_project_phase_status(project_code: str):
    """Get phase status for a project"""
    try:
        status = deliverables_service.get_project_phase_status(project_code)
        return item_response(status)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.post("/deliverables/project/{project_code}/generate-milestones")
async def generate_project_milestones(project_code: str):
    """Generate standard milestones for a project"""
    try:
        result = deliverables_service.generate_project_milestones(project_code)
        return action_response(True, data=result, message="Milestones generated")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred")


@router.get("/lifecycle-phases")
async def get_lifecycle_phases():
    """Get project lifecycle phases with typical durations"""
    phases = [
        {
            "phase": "Schematic Design",
            "phase_order": 1,
            "typical_duration_months": 3,
            "description": "Initial design concepts and space planning",
            "deliverables": ["Concept drawings", "Space plans", "Material boards"],
            "is_optional": False
        },
        {
            "phase": "Design Development",
            "phase_order": 2,
            "typical_duration_months": 4,
            "description": "Detailed design with specifications",
            "deliverables": ["DD drawings", "Specifications", "Cost estimates"],
            "is_optional": False
        },
        {
            "phase": "Construction Documents",
            "phase_order": 3,
            "typical_duration_months": 4,
            "description": "Complete construction documentation",
            "deliverables": ["CD drawings", "Detail sheets", "Schedules"],
            "is_optional": False
        },
        {
            "phase": "Bidding & Negotiation",
            "phase_order": 4,
            "typical_duration_months": 1,
            "description": "Contractor selection and pricing",
            "deliverables": ["Bid packages", "Contractor evaluation"],
            "is_optional": True
        },
        {
            "phase": "Construction Administration",
            "phase_order": 5,
            "typical_duration_months": 12,
            "description": "On-site construction oversight",
            "deliverables": ["Site reports", "RFI responses", "Submittals"],
            "is_optional": False
        },
        {
            "phase": "Closeout",
            "phase_order": 6,
            "typical_duration_months": 1,
            "description": "Project completion and handover",
            "deliverables": ["As-built drawings", "Punch list", "Warranties"],
            "is_optional": False
        }
    ]

    total_months = sum(p["typical_duration_months"] for p in phases if not p.get("is_optional"))

    return {
        "success": True,
        "phases": phases,
        "total_typical_months": total_months
    }
